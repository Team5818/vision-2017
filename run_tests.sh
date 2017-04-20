#!/usr/bin/env bash
python3 -m unittest discover -t "." -s "server/test" -p '*_test.py'
