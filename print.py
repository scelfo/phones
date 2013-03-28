#!/usr/bin/python

import phones_pb2
import sys
import time
import util


def PrintActions(actions):
  for name in actions:
    print '\nAction for %s:' % name
    for action in actions[name]:
      print '%s at %s' % (
          phones_pb2._ACTION_STATE.values_by_number[action.state].name,
          util.FormatTime(action.time_ms))


def PrintRecords(records):
  for name in records:
    print '\nStatus for %s:' % name
    for record in records[name]:
      print '%s at %s' % (
          record.present and 'Came home' or 'Left',
          util.FormatTime(record.time_ms))


def main(argv):
  log_file = util.ReadFile()

  PrintActions(util.ExtractActions(log_file))

  PrintRecords(util.FilterForStateChanges(
      util.ExtractRecords(log_file)))


main(sys.argv)
