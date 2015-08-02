#! /usr/bin/env python

import json, logging, logtool, requests, statsd
from addict import Dict
from flattendict import flatten_dict

LOG = logging.getLogger (__name__)

ENDPOINT_HANDLERS = {
  "api/channels",
  "api/connections",
  "api/exchanges",
  "api/nodes",
  "api/overview",
  "api/queues",
  "api/vhosts",
}

report_keys = {
  "api/channels": [],
  "api/connections": [],
  "api/exchanges": [],
  "api/nodes": [
    "disk_free",
    "disk_free_alarm",
    "fd_total",
    "fd_used",
    "mem_used",
    "mem_alarm",
    "proc_total",
    "proc_used",
    "run_queue",
    "running",
    "sockets_total",
    "sockets_used",
  ],
  "api/overview": [
    "cluster_name",
    "message_stats.deliver",
    "message_stats.deliver_no_ack_details.rate",
    "message_stats.get_no_ack_details.rate",
    "message_stats.get_no_ack",
    "message_stats.ack",
    "message_stats.publish",
    "message_stats.deliver_no_ack",
    "message_stats.deliver_get_details.rate",
    "message_stats.deliver_get",
    "message_stats.ack_details.rate",
    "message_stats.redeliver_details.rate",
    "message_stats.publish_details.rate",
    "message_stats.deliver_details.rate",
    "message_stats.redeliver",
    "object_totals.channels",
    "object_totals.connections",
    "object_totals.queues",
    "object_totals.exchanges",
    "object_totals.consumers",
    "queue_totals.messages_unacknowledged",
    "queue_totals.messages_ready",
    "queue_totals.messages_ready_details.rate",
    "queue_totals.messages_unacknowledged_details.rate",
    "queue_totals.messages_details.rate",
    "queue_totals.messages",
  ],
  "api/queues": [
    "durable",
    "messages_ready",
    "messages_unacknowledged",
    "messages",
    "messages_ready_ram",
    "messages_unacknowledged_ram",
    "messages_ram",
    "messages_persistent",
    "message_bytes",
    "message_bytes_ready",
    "message_bytes_unacknowledged",
    "message_bytes_ram",
    "message_bytes_persistent",
    "disk_reads",
    "disk_writes",
    "consumers",
    "consumer_utilisation",
    "memory",
  ],
  "api/vhosts": [

  ],
}


class MqReportBase (object):

  @logtool.log_call
  def __init__ (self, app, mq_conn):
    self.app = app
    self.mq_conn = Dict (mq_conn)
    # Include hiostname in app
    #self.timer = statsd.Counter (app)
    #self.timer = statsd.Gauge (app)
    #self.timer = statsd.Average (app)
    #self.timer = statsd.Timer (app)
    self.data = None

  @property
  def endpoint (self):
    raise NotImplementedError ("Subclasses should implement this!")

  @logtool.log_call
  def get (self):
    url = "http://{host}:{port}/{endpoint}".format (
      endpoint = self.endpoint, **self.mq_conn)
    rc = requests.get (url, auth = (self.mq_conn.user, self.mq_conn.passwd))
    if isinstance (rc.json (), list):
      self.data = [Dict (flatten_dict (i)) for i in rc.json ()]
    else:
      self.data = Dict (flatten_dict (rc.json ()))

  @logtool.log_call
  def report (self):
    raise NotImplementedError ("Subclasses should implement this!")

  @logtool.log_call
  def run (self):
    self.get ()
    self.report ()

class MqChannelReport (MqReportBase):
  endpoint =  "api/channels"

  @logtool.log_call
  def report (self):
    pass

class MqConnectionReport (MqReportBase):
  endpoint =  "api/connections"

  @logtool.log_call
  def report (self):
    pass

class MqExchangeReport (MqReportBase):
  endpoint =  "api/exchanges"

  @logtool.log_call
  def report (self):
    pass

class MqNodeReport (MqReportBase):
  endpoint =  "api/nodes"

  @logtool.log_call
  def report (self):
    return
    keys = [
      "disk_free",
      "disk_free_alarm",
      "fd_total",
      "fd_used",
      "mem_used",
      "mem_alarm",
      "proc_total",
      "proc_used",
      "run_queue",
      "running",
      "sockets_total",
      "sockets_used",
    ]
    for d in self.data:
      name = d.name.split ("@")[1]
      for k in keys:
        key = "{}.{}".format (name, k)
        value = d[k]
        statsd.Gauge (self.app).send (key, value)

class MqOverviewReport (MqReportBase):
  endpoint =  "api/overview"

  @logtool.log_call
  def report (self):
    return
    keys = [
      "cluster_name",
      "message_stats.deliver",
      "message_stats.deliver_no_ack_details.rate",
      "message_stats.get_no_ack_details.rate",
      "message_stats.get_no_ack",
      "message_stats.ack",
      "message_stats.publish",
      "message_stats.deliver_no_ack",
      "message_stats.deliver_get_details.rate",
      "message_stats.deliver_get",
      "message_stats.ack_details.rate",
      "message_stats.redeliver_details.rate",
      "message_stats.publish_details.rate",
      "message_stats.deliver_details.rate",
      "message_stats.redeliver",
      "object_totals.channels",
      "object_totals.connections",
      "object_totals.queues",
      "object_totals.exchanges",
      "object_totals.consumers",
      "queue_totals.messages_unacknowledged",
      "queue_totals.messages_ready",
      "queue_totals.messages_ready_details.rate",
      "queue_totals.messages_unacknowledged_details.rate",
      "queue_totals.messages_details.rate",
      "queue_totals.messages",
    ]
    name = d.node.split ("@")[1]
    for k in keys:
      key = "{}.{}".format (name, k)
      value = d[k]
      statsd.Gauge (self.app).send (key, value)

class MqQueueReport (MqReportBase):
  endpoint =  "api/queues"

  @logtool.log_call
  def report (self):
    keys = [
      "durable",
      "messages_ready",
      "messages_unacknowledged",
      "messages",
      "messages_ready_ram",
      "messages_unacknowledged_ram",
      "messages_ram",
      "messages_persistent",
      "message_bytes",
      "message_bytes_ready",
      "message_bytes_unacknowledged",
      "message_bytes_ram",
      "message_bytes_persistent",
      "disk_reads",
      "disk_writes",
      "consumers",
      "consumer_utilisation",
      "memory",
    ]
    queue = d.name
    for k in keys:
      key = "{}.{}".format (queue, k)
      value = d[k]
      statsd.Gauge (self.app).send (key, value)
    key = "{}.{}".format (queue, "state")
    value = 1 if d["state"] == "running" else 0
    statsd.Gauge (self.app).send (key, value)

class MqVhostReport (MqReportBase):
  endpoint =  "api/vhosts"

  @logtool.log_call
  def report (self):
    print self.endpoint
 #   print json.dumps (self.data, indent = 2)

def report ():
  for r in [MqChannelReport, MqConnectionReport, MqExchangeReport,
            MqNodeReport, MqOverviewReport, MqQueueReport,
            MqVhostReport,]:
    mq_conn = {
      "host": "queuehost",
      "port": 15672,
      "user": "admin",
      "passwd": "Guest",
    }
    r ("coneyeye.rabbitmq", mq_conn).run ()
