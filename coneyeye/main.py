#! /usr/bin/env python

from __future__ import absolute_import
import json, logging, logging.config, logtool, statsd, setproctitle, sys, time
from configobj import ConfigObj
from .mqreport import mqreport

LOG = logging.getLogger (__name__)
DEFAULT_PROCNAME = "coneyeye"
DEFAULT_CONF = "/etc/coneyeye/coneyeye.conf"
DEFAULT_LOGCONF = "/etc/coneyeye/logging.conf"

class ConfigurationException (Exception):
  pass

@logtool.log_call
def app_main ():
  try:
    conf = ConfigObj (DEFAULT_CONF, interpolation = False)
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
    raise ConfigurationException
  try:
    while True:
      with statsd.StatsClient (**statsd_conn).pipeline() as pipe:
        stats = mqreport (mq_conn, ignore_queues = ignore_queues)
        LOG.info (json.dumps (stats, indent = 2))
        for k, v in stats.items ():
          pipe.gauge (k, v)
        pipe.send ()
      LOG.info ("Sent...")
      time.sleep (delay)
  except KeyboardInterrupt:
    pass
  except Exception as e:
    logtool.log_fault (e)

@logtool.log_call
def main ():
  try:
    logging.config.fileConfig (DEFAULT_LOGCONF,
                               disable_existing_loggers = False)
    setproctitle.setproctitle (DEFAULT_PROCNAME)
    app_main ()
  except ConfigurationException as e:
    print >> sys.stderr, "Configuration problem.  See logs for details."
  except KeyboardInterrupt:
    pass
  except Exception as e:
    logtool.log_fault (e)
    sys.exit (1)

if __name__ == "__main__":
  main ()
