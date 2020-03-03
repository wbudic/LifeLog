#!/bin/bash

DIR="/home/will/dev/LifeLog"

if [ ! -d "$DIR/log" ]; then
    mkdir "$DIR/log"
fi
cd $DIR
thttpd -C ./thttpd.conf &
