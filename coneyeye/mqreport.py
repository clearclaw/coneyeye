#! /usr/bin/env python

from __future__ import absolute_import
import fnmatch, logging, logtool, requests, retryp
from addict import Dict
from .flattendict import flatten_dict

LOG = logging.getLogger (__name__)
logging.basicConfig (level = logging.WARN)

@retryp.retryp (expose_last_exc = True)
@logtool.log_call
def get_data (mq_conn, endpoint):
  url = "{url}{endpoint}".format (endpoint = endpoint, **mq_conn)
  rc = requests.get (url, auth = (mq_conn["user"], mq_conn["passwd"]))
  if isinstance (rc.json (), list):
    return [Dict (flatten_dict (i)) for i in rc.json ()]
  return Dict (flatten_dict (rc.json ()))

@logtool.log_call
def message_stats (name, prefix, data, stats):
  stubs = [
    "ack",
    "ack_details.rate",
    "deliver",
    "deliver_details.rate",
    "deliver_get",
    "deliver_get_details.rate",
    "deliver_no_ack",
    "deliver_no_ack_details.rate",
    "get_no_ack",
    "get_no_ack_details.rate",
    "publish",
    "publish_details.rate",
    "redeliver",
    "redeliver_details.rate",
  ]
  keys = ["%s.%s" % (prefix, k) for k in stubs]
  aggregate (name, keys, data, stats)

@logtool.log_call
def aggregate (name, keys, data, stats):
  for k in keys:
    key = "{}.{}".format (name, k)
    value = data[k]
    if value == {}:
      continue
    if value in (False, True):
      value = 1 if value else 0
    stats[key] = value

@logtool.log_call
def pattern_match (key, patterns):
  for pattern in patterns:
    p = pattern.strip ()
    if fnmatch.fnmatch (key, p): # Discard matches
      return True
  return False

@logtool.log_call
def mqreport (mp_conn, ignore_queues = None):
  stats = Dict ()
  mp_conn = Dict (mp_conn)
  data = get_data (mp_conn, "api/nodes")
  keys = [
    "disk_free",
    "disk_free_alarm",
    "fd_total",
    "fd_used",
    "mem_alarm",
    "mem_used",
    "proc_total",
    "proc_used",
    "run_queue",
    "running",
    "sockets_total",
    "sockets_used",
  ]
  for d in data:
    name = "nodes." + d.name.split ("@")[1]
    aggregate (name, keys, d, stats)
  data = get_data (mp_conn, "api/overview")
  keys = [
    "object_totals.channels",
    "object_totals.connections",
    "object_totals.consumers",
    "object_totals.exchanges",
    "object_totals.queues",
    "queue_totals.messages",
    "queue_totals.messages_details.rate",
    "queue_totals.messages_ready",
    "queue_totals.messages_ready_details.rate",
    "queue_totals.messages_unacknowledged",
    "queue_totals.messages_unacknowledged_details.rate",
  ]
  name = ("overview." + (data.cluster_name
          if data.cluster_name else data.node.split ("@")[1]))
  aggregate (name, keys, data, stats)
  message_stats (name, "message_stats", data, stats)
  data = get_data (mp_conn, "api/queues")
  keys = [
    "consumer_utilisation",
    "consumers",
    "disk_reads",
    "disk_writes",
    "durable",
    "memory",
    "message_bytes",
    "message_bytes_persistent",
    "message_bytes_ram",
    "message_bytes_ready",
    "message_bytes_unacknowledged",
    "messages",
    "messages_persistent",
    "messages_ram",
    "messages_ready",
    "messages_ready_ram",
    "messages_unacknowledged",
    "messages_unacknowledged_ram",
  ]
  for d in data:
    name = "queues." + d.name
    if ignore_queues and pattern_match (name, ignore_queues):
      continue
    aggregate (name, keys, d, stats)
    key = "queues.{}.{}".format (name, "state")
    value = 1 if d["state"] == "running" else 0
    stats[key] = value
  data = get_data (mp_conn, "api/vhosts")
  keys = [
    "messages",
    "messages_details.rate",
    "messages_ready",
    "messages_ready_details.rate",
    "messages_unacknowledged",
    "messages_unacknowledged_details.rate",
    "recv_oct",
    "send_oct",
    "send_oct_details.rate",
  ]
  for d in data:
    name = "vhosts." + d.name.replace ("/", "_slash_")
    aggregate (name, keys, d, stats)
    message_stats (name, "messages_stats", d, stats)
  return stats
