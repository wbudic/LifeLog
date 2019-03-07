#!/bin/bash                                                                                        
export DB_USER="db"
export DB_PASS="db_pass"
cd /home/will/thttpd_dev
thttpd -C thttpd.conf& 
