#! /usr/bin/env python

from __future__ import absolute_import
import json, logging, logging.config, logtool, raven
import statsd, setproctitle, sys, time
from configobj import ConfigObj
from .mqreport import mqreport
from ._version import get_versions

LOG = logging.getLogger (__name__)
DEFAULT_PROCNAME = "coneyeye"
DEFAULT_CONF = "/etc/coneyeye/coneyeye.conf"
DEFAULT_LOGCONF = "/etc/coneyeye/logging.conf"

class InitialiseException (Exception):
  pass

class RuntimeException (Exception):
  pass

@logtool.log_call
def sentry_exception (conf, stats, e, message = None):
  sentry = raven.Client (conf["sentry_dsn"],
                         auto_log_stacks = True,
                         release = get_versions ()["version"])
  sentry_tags = {"component": "coneyeye"}
  logtool.log_fault (e, message = message)
  data = {
    "conf": conf,
    "stats": stats,
  }
  if message:
    data["message"] = message
  sentry.extra_context (data)
  try:
    exc_info = sys.exc_info()
    rc = sentry.captureException (exc_info, **sentry_tags)
    LOG.error ("Sentry filed: %s", rc)
  finally:
    del exc_info

@logtool.log_call
def app_main (conf):
  try:
    if not conf.get ("sentry_dsn"):
      raise InitialiseException ("Missing configuration: sentry_dsn")
    mq_conn = {
      "url": conf.get ("rabbitmq_adminapi_url"),
      "user": conf.get ("rabbitmq_adminapi_user"),
      "passwd": conf.get ("rabbitmq_adminapi_passwd"),
    }
    statsd_conn = {
      "host": conf.get ("statsd_host", "127.0.0.1"),
      "port": conf.get ("statsd_port", 8125),
      "prefix": conf.get ("statsd_prefix", "rabbitmq"),
    }
    delay = int (conf.get ("delay", 5)) * 60
    # ignore_queues = ["*.celery@*", "*.celeryev.*", "*pidbox"]
    ignore_queues = [s.strip ()
                     for s in conf.get ("suppress_queues", "").split(",")]
  except Exception as e:
    logtool.log_fault (e)
    raise InitialiseException
  stats = None
  while True:
    try:
      with statsd.StatsClient (**statsd_conn).pipeline() as pipe:
        stats = mqreport (mq_conn, ignore_queues = ignore_queues)
        LOG.info (json.dumps (stats, indent = 2))
        for k, v in stats.items ():
          pipe.gauge (k, v)
        pipe.send ()
      LOG.info ("Sent...")
      time.sleep (delay)
    except KeyboardInterrupt:
      raise
    except Exception as e:
      sentry_exception (conf, stats, e)
      LOG.info ("Sleeping for a minute...")
      time.sleep (60)

@logtool.log_call
def main ():
  try:
    logging.config.fileConfig (DEFAULT_LOGCONF,
                               disable_existing_loggers = False)
    setproctitle.setproctitle (DEFAULT_PROCNAME)
    conf = ConfigObj (DEFAULT_CONF, interpolation = False)
    app_main (conf)
  except InitialiseException as e:
    print >> sys.stderr, "Configuration problem.  See logs for details."
    sys.exit (1)
  except KeyboardInterrupt:
    sys.exit (0)
  except RuntimeException:
    LOG.error ("Exiting...")
    sys.exit (1)
  except Exception as e:
    logtool.log_fault (e)
    LOG.error ("Exiting...")
    sys.exit (1)

if __name__ == "__main__":
  main ()
