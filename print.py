#!/usr/bin/python

import config
import phones_pb2
import sys
import time

from collections import deque

# Use a sliding window to smooth out network problems.
SIZE_OF_SLIDING_WINDOW = 3

def ReadFile():
  f = open(config.LOG_FILE, "rb")
  log_file = phones_pb2.LogFile()
  log_file.ParseFromString(f.read())
  f.close()

  records = {}
  for log in log_file.log:
    if log.phone not in records:
      records[log.phone] = []
    records[log.phone].append((log.time_ms, log.present))
  return records


def FilterForStateChanges(records):
  filtered_records = {}
  for name in records:
    if name not in filtered_records:
      filtered_records[name] = []
    window = deque([(None, None)], SIZE_OF_SLIDING_WINDOW)
    state = None
    for record in records[name]:
      window.append(record)
      if all(x[1] == window[0][1] for x in window) and window[0][1] != state:
        filtered_records[name].append(window[0])
        state = window[0][1]
  return filtered_records


def PrintReport(records):
  for name in records:
    print '\nStatus for %s:' % name
    for record in records[name]:
      print '%s at %s' % (
        record[1] and 'Came home' or 'Left',
        time.asctime(time.localtime(record[0] / 1000)))


def main(argv):
  records = FilterForStateChanges(ReadFile())
  PrintReport(records)


main(sys.argv)
