#! /usr/bin/env python

from __future__ import absolute_import
import logging, logtool, time
from mqreportbase import report

LOG = logging.getLogger (__name__)

@logtool.log_call
def main ():
  while True:
    time.sleep (3)
    report ()

if __name__ == "__main__":
  main ()
