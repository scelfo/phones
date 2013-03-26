#!/bin/bash

if [ ! -f config.py ]; then
  echo "You must create a config.py file!"
  echo
  echo "This script has automatically copied config.py.example to config.py, "
  echo "you should modify it for your own settings."
  cp config.py.example config.py
  exit 1
fi

echo "Compiling phones.proto..."
protoc phones.proto --python_out=.
