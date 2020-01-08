#!/bin/bash

DIR="/home/will/dev/LifeLog"

if [ ! -d "$DIR/log" ]; then
    mkdir "$DIR/log"
fi
cd $DIR
cd /home/will/dev/LifeLog
thttpd -C thttpd.conf &
