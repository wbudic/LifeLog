#!/bin/bash
PID=$(ps -C thttpd | grep thttpd | awk '{printf "%s", $1}')
sudo kill -9 $PID

