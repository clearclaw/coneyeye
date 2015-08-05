#! /usr/bin/env python

import collections, logging, logtool
from addict import Dict

LOG = logging.getLogger (__name__)

class FlattenDict (object):

  @logtool.log_call (log_args = False)
  def __init__ (self, data):
    self.data = data

  # @logtool.log_call (log_args = False)
  def flatten_list (self, l, parent_key = '', sep = '.'):
    items = []
    items.append ((parent_key + sep + "#" + "count", len (l)))
    for i in xrange (len (l)):
      new_key = parent_key + ("[%d]" % i if parent_key else "%d" % i)
      items.extend (self.flatten_item (l[i], new_key, sep = sep))
    return items

  # @logtool.log_call (log_args = False)
  def flatten_dict (self, d, parent_key = '', sep = '.'):
    items = []
    for k, v in d.items ():
      new_key = parent_key + sep + k if parent_key else k
      items.extend (self.flatten_item (v, new_key, sep = sep))
    return items

  # @logtool.log_call (log_args = False)
  def flatten_item (self, i, parent_key = '', sep = '.'):
    items = []
    if isinstance (i, collections.MutableMapping): # Dictionary
      items.extend (self.flatten_dict (i, parent_key, sep = sep))
    elif isinstance (i, collections.MutableSequence):
      items.extend (self.flatten_list (i, parent_key, sep = sep))
    else:
      items.append ((parent_key, i))
    return items

  @logtool.log_call (log_args = False, log_rc = False)
  def run (self, parent_key = '', sep = '.'):
    return Dict (self.flatten_item (self.data, parent_key, sep = sep))

@logtool.log_call (log_args = False)
def flatten_dict (data):
  return FlattenDict (data).run ()
