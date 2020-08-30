#!/bin/bash
#
# This script tries to install install and test required modules for this project.
#
# You must have superuser admin password priviledges to run this script.
#
## git clone https://github.com/wbudic/LifeLog.git
# Uncoment the  following git pull if also wanting to perform a latest pull
# from the master (upgrade) repository.
## git pull
LIFELOG_MODS=install_lifelog_req_modules_2.0.sh
sudo cat Installation.txt | grep 'sudo apt install' > $LIFELOG_MODS
sudo cat Installation.txt | grep 'sudo cpan' >> $LIFELOG_MODS
sudo chmod +x $LIFELOG_MODS
# The following is actual installation file generated. Don't run outside this script.
# You can delete or keep after running this script.
sudo ./$LIFELOG_MODS

#Used for stats, required utility
sudo apt install inxi -y



echo "\nDone with Life Log modules installation!\n"



