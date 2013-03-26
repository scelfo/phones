#!/usr/bin/python

import argparse
import config
import phones_pb2
import subprocess
import sys
import time

from googlevoice import Voice

REVERSE_NUMBERS = dict(reversed(x) for x in config.NUMBERS.items())

FLAGS = argparse.ArgumentParser(description='Enable and disable phones.')
FLAGS.add_argument(
    '--enable', nargs='+', choices=config.NUMBERS, help='Phones to enable.')
FLAGS.add_argument(
    '--disable', nargs='+', help='Phones to disable.')


def ReadFile():
  # Read the existing log file.
  try:
    f = open(config.LOG_FILE, 'rb')
    log_file = phones_pb2.LogFile()
    log_file.ParseFromString(f.read())
    f.close()
    return log_file
  except IOError:
    print 'File %s not found, creating a new one.' % config.LOG_FILE
    return phones_pb2.LogFile()


def WriteFile(log_file):
  # Write the new log file to disk.
  f = open(config.LOG_FILE, 'wb')
  f.write(log_file.SerializeToString())
  f.close()


def CheckPhones():
  result = {}
  for phone in config.MAC_ADDRESSES.items():
    arp_scan = subprocess.check_output(
        ['sudo', 'arp-scan', '-t', '500', '-T', phone[1][0], phone[1][1]])
    result[phone[0]] = arp_scan.find(phone[1][0]) != -1
  return result


def main(argv):
  parsed = FLAGS.parse_args()
  log_file = ReadFile()
  time_ms = int(time.time() * 1000)
  phone_status = CheckPhones()
  for status in phone_status.items():
    log = log_file.log.add()
    log.time_ms = time_ms
    log.phone = status[0]
    log.present = status[1]
  WriteFile(log_file)

  if parsed.enable or parsed.disable:
    voice = Voice()
    voice.login()

    try:
      for phone in voice.phones:
        if phone.phoneNumber in REVERSE_NUMBERS:
          phone_name = REVERSE_NUMBERS[phone.phoneNumber]
          if parsed.enable and phone_name in parsed.enable:
            print 'Enabling %s: %s' % (phone_name, phone.phoneNumber)
            phone.enable()
          if parsed.disable and phone_name in parsed.disable:
            print 'Disabling %s: %s' % (phone_name, phone.phoneNumber)
            phone.disable()
    except Exception as e:
      print e

    voice.logout()


main(sys.argv)
