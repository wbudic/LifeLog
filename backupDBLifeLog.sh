#!/bin/bash
#
# Following is an hardcoded script that can be used on your local machine
# to archive from server all the latest SQLite databases on the DB Life Log server.
#
# Usefull to cron, to auto backup the databases just in case.
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#Example crontab -e entry for every three hours.
#crontab -> * */3 * * * /home/will/dev/backupDBLifeLog.sh > /dev/null 2>&1

export DISPLAY=":0"
export XDG_RUNTIME_DIR=/run/user/$(id -u)
export XAUTHORITY="/home/will/.Xauthority"
export SSHPASS='N0-MA-E9-5E-4A-C6-MJ-2F'
DIR="/home/will/backups/r2d2_dbLifeLog"
NOW=`date +%Y%m%d`

if [ ! -d "$DIR" ]; then
   mkdir $DIR
fi
cd $DIR

sshpass -e sftp -oIdentityFile=~/.ssh/id_dsa -oBatchMode=no r2d2@192.168.1.20:/home/r2d2/dev/dbLifeLog/ <<EOF
get *.db 
exit
EOF

#
# Archiving optional bellow.
#

tar -czvf DB_LIFE_LOG_BACKUP_$NOW.tar *.db

#Remove unecessary files.
find $DIR -type f -name '*.tar' -mtime +3 -exec rm -f {} \; 
rm *.db

exit
