#! /usr/bin/env python

from __future__ import absolute_import
import clip, json, logging, logtool, statsd, sys, time
from path import Path
from mqreport import mqreport

LOG = logging.getLogger (__name__)
LOG.setLevel (logging.INFO)
ch = logging.StreamHandler ()
formatter = logging.Formatter("%(asctime)s %(processName)s[%(process)d] %(levelname)s <%(module)s:%(funcName)s(%(lineno)d)> %(message)s") # pylint: disable=C0301
ch.setFormatter (formatter)
LOG.addHandler (ch)

APP = clip.App (name = "coneyeye")

@APP.main (name = Path (sys.argv[0]).basename (),
           description = "RabbitMQ->StatsD monitor exchange")
@clip.opt ("-o", "--host", name = "host",
           help = "RabbitMQ admin API host", required = True)
@clip.opt ("-t", "--port", name = "port", type = int,
           help = "RabbitMQ admin API port", required = True)
@clip.opt ("-u", "--user", name = "user",
           help = "RabbitMQ admin API user", required = True)
@clip.opt ("-p", "--password", name = "passwd",
           help = "RabbitMQ admin API password", required = True)
@clip.opt ("-d", "--delay", name = "delay", type = int,
           help = "Number of minutes between reports",
           default = 5, required = True)
@clip.opt ("-m", "--metric_prefix", name = "statsd_prefix",
           default = "rabbitmq", help = "StasD metric prefix",
           required = False)
@clip.opt ("-s", "--suppress", name = "suppress",
           help = "Queue globs to supress (comma delimited, optional)",
           default = "", required = False)
@clip.opt ("-O", "--statsd_host", name = "statsd_host",
           default = "127.0.0.1", help = "StasD host (optional)",
           required = False)
@clip.opt ("-T", "--statsd_port", name = "statsd_port", type = int,
           default = 8125, help = "StasD port (optional)", required = False)
@clip.opt ("-L", "--loglevel", name = "log", default = "INFO",
           help = "StasD port (optional)", required = False)
@logtool.log_call
def app_main (host, port, user, passwd, delay, **kwargs):
  mq_conn = {
    "host": host,
    "port": port,
    "user": user,
    "passwd": passwd,
  }
  statsd_conn = {
    "host": kwargs.get ("statsd_host", "127.0.0.1"),
    "port": kwargs.get ("statsd_port", 8125),
    "prefix": kwargs.get ("statsd_prefix", "rabbitmq"),
  }
  delay = int (kwargs.get ("delay", 5)) * 60
  # ignore_queues = ["*.celery@*", "*.celeryev.*", "*pidbox"]
  ignore_queues = [s.strip () for s in kwargs["suppress"].split(",")]
  level = kwargs.get ("log")
  if level and getattr (logging, level):
    logging.root.setLevel (getattr (logging, level))
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
    APP.run ()
  except KeyboardInterrupt:
    pass
  except clip.ClipExit:
    pass
  except Exception as e:
    logtool.log_fault (e)
    sys.exit (1)

if __name__ == "__main__":
  main ()
