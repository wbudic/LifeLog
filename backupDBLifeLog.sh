#!/bin/bash
#
# Following is an hardcoded script that can be used on your local machine
# to archive from server all the latest SQLite databases on the DB Life Log server.
#
# Usefull to cron, to auto backup the databases just in case.
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
DIR="/home/will/Documents/dbLifeLog"
NOW=`date +%Y%m%d`

if [ ! -d "$DIR" ]; then
   mkdir $DIR
fi
cd $DIR

sftp will@nuc:/home/will/thttpd_dev/dbLifeLog/ <<EOF
get *.db 
exit
EOF

#
# Archiving optional bellow.
#

tar -czvf DB_LIFE_LOG_BACKUP_$NOW.tar *.db

#Remove unecessary files.
find $DIR -type f -name '*.tar' -mtime  1 -exec rm {} \; 
rm *.db


exit
