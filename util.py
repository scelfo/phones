import config
import phones_pb2
import time
import zlib

from collections import deque


def FormatTime(time_ms):
  return time.asctime(time.localtime(time_ms / 1000))


def ReadFile():
  # Read the existing log file.
  try:
    f = open(config.LOG_FILE, 'rb')
    log_file = phones_pb2.LogFile()
    contents = f.read()
    f.close()
    try:
      contents = zlib.decompress(contents)
    except zlib.error:
      # Older code wrote uncompressed.
      pass
    log_file.ParseFromString(contents)
    return log_file
  except IOError:
    print 'File %s not found, creating a new one.' % config.LOG_FILE
    return phones_pb2.LogFile()


def WriteFile(log_file):
  # Write the new log file to disk.
  f = open(config.LOG_FILE, 'wb')
  f.write(zlib.compress(log_file.SerializeToString()))
  f.close()


def ExtractActions(log_file):
  actions = {}
  for action in log_file.action:
    if action.phone not in actions:
      actions[action.phone] = []
    actions[action.phone].append(action)
  return actions


def ExtractRecords(log_file):
  records = {}
  for log in log_file.log:
    if log.phone not in records:
      records[log.phone] = []
    records[log.phone].append(log)
  return records


def FilterForStateChanges(records):
  filtered_records = {}
  for name in records:
    if name not in filtered_records:
      filtered_records[name] = []
    window = deque([], config.SIZE_OF_SLIDING_WINDOW)
    state = None
    for record in records[name]:
      window.append(record)
      if (all(x.present == window[0].present for x in window)
          and window[0].present != state):
        filtered_records[name].append(window[0])
        state = window[0].present
  return filtered_records
