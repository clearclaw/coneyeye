#! /usr/bin/env python

from __future__ import absolute_import
import clip, json, logging, logtool, statsd, sys, time
from path import Path
from mqreport import mqreport

LOG = logging.getLogger (__name__)
APP = clip.App (name = "coneyeye")

@APP.main (name = Path (sys.argv[0]).basename (),
           description = "RabbitMQ->StatsD monitor exchange")
@clip.opt ("-H", "--host", name = "host",
           help = "RabbitMQ admin API host", required = True)
@clip.opt ("-T", "--port", name = "port",
           help = "RabbitMQ admin API port", required = True)
@clip.opt ("-U", "--user", name = "user",
           help = "RabbitMQ admin API user", required = True)
@clip.opt ("-P", "--password", name = "passwd",
           help = "RabbitMQ admin API password", required = True)
@clip.opt ("-S", "--suppress", name = "suppress",
           help = "Queue globs to supress (comma delimited, optional)",
           default = "", required = False)
@logtool.log_call
def app_main (host, port, user, passwd, suppress):
  mq_conn = {
    "host": host,
    "port": port,
    "user": user,
    "passwd": passwd,
  }
  # ignore_queues = ["*.celery@*", "*.celeryev.*", "*pidbox"]
  ignore_queues = [s.strip () for s in suppress.split(",")]
  client = statsd.StatsClient ()
  try:
    while True:
      time.sleep (3)
      stats = mqreport (mq_conn, ignore_queues = ignore_queues)
      print json.dumps (stats, indent = 2)
      pipe = client.pipeline ()

      pipe.send ()
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
