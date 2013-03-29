#!/usr/bin/python

import argparse
import config
import phones_pb2
import subprocess
import sys
import time
import util

from googlevoice import Voice

REVERSE_NUMBERS = dict(reversed(x) for x in config.NUMBERS.items())

FLAGS = argparse.ArgumentParser(description='Enable and disable phones.')
FLAGS.add_argument(
    '--enable', nargs='+', choices=config.NUMBERS, default=[],
    help='Phones to enable.')
FLAGS.add_argument(
    '--disable', nargs='+', choices=config.NUMBERS, default=[],
    help='Phones to disable.')


def CheckPhones():
  result = {}
  for phone in config.MAC_ADDRESSES.items():
    arp_scan = subprocess.check_output(
        ['sudo', 'arp-scan', '-t', str(config.ARP_SCAN_TIMEOUT_MS),
         '-T', phone[1][0], phone[1][1]])
    result[phone[0]] = arp_scan.find(phone[1][0]) != -1
  return result


def FindStateChangesWithoutEvents(log_file):
  actions = util.ExtractActions(log_file)

  state_changes = util.FilterForStateChanges(
      util.ExtractRecords(log_file))
  changed_without_events = {}
  for phone in state_changes:
    phone_event_times = [x.time_ms for x in actions[phone]]
    for change in state_changes[phone]:
      if (phone not in actions
          or change.time_ms not in phone_event_times):
        changed_without_events[phone] = change
        break
  return changed_without_events


def TogglePhones(log_file, actions):
  voice = Voice()
  voice.login()
  exceptions = []
  for phone in voice.phones:
    if phone.phoneNumber in REVERSE_NUMBERS:
      phone_name = REVERSE_NUMBERS[phone.phoneNumber]
      if phone_name in actions:
        action = actions[phone_name]
        try:
          if action.state == phones_pb2.Action.ENABLED:
            prefix = 'Enabling'
            phone.enable()
          else:
            prefix = 'Disabling'
            phone.disable()
          print '%s %s: %s for change at %s' % (
              prefix, phone_name, phone.phoneNumber,
              util.FormatTime(action.time_ms))
        except Exception as e:
          print e
          exceptions.append(e)
  voice.logout()
  if exceptions:
    raise Exception(exceptions)


def ExtraEnable(log_file, time_ms, phone, enable):
  print 'extra %s for %s' % (
      enable and 'enable' or 'disable',
      phone)
  action = log_file.action.add()
  action.time_ms = time_ms
  action.phone = phone
  if enable:
    action.state = phones_pb2.Action.ENABLED
  else:
    action.state = phones_pb2.Action.DISABLED
  return action


def main(argv):
  parsed = FLAGS.parse_args()

  # Compute a time for this run so that all logs in this run
  # will use the same time.
  time_ms = int(time.time() * 1000)

  # Check the current phone status before reading the log file
  # to minimize the time between when the log file is read and when
  # it is updated and written back.
  phone_status = CheckPhones()

  # Read the existing log file.  This is a simple read/modify/write
  # pattern without any locking so we make an effort to minimize the
  # time between reading the log and writing it.
  log_file = util.ReadFile()

  for status in phone_status.items():
    log = log_file.log.add()
    log.time_ms = time_ms
    log.phone = status[0]
    log.present = status[1]

  changes_without_events = FindStateChangesWithoutEvents(log_file)

  pending_actions = {}
  for phone in changes_without_events:
    change = changes_without_events[phone]
    action = log_file.action.add()
    action.time_ms = change.time_ms
    action.phone = change.phone
    if change.present:
      action.state = phones_pb2.Action.DISABLED
    else:
      action.state = phones_pb2.Action.ENABLED
    pending_actions[phone] = action

  for phone in parsed.enable:
    if phone not in pending_actions:
      pending_actions[phone] = ExtraEnable(log_file, time_ms, phone, True)

  for phone in parsed.disable:
    if phone not in pending_actions:
      pending_actions[phone] = ExtraEnable(log_file, time_ms, phone, False)

  # Write the updated log file before trying to talk to Google Voice
  # because we want to minimize the time between reading and writing
  # the log file.
  util.WriteFile(log_file)

  # If there are any pending actions go ahead and perform them.  If one of
  # them fails, it will not be retried because we have already written to
  # the log that the action was taken.  This is an acceptable failure mode
  # and protects against repeatedly taking a failing action during a
  # Google Voice outage.
  if pending_actions:
    TogglePhones(log_file, pending_actions)


main(sys.argv)
