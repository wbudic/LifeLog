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
VER="2.0"
SCRIPT="install_lifelog_modules_$VER.sh"
sudo cat Installation.txt | grep 'sudo apt install' > $SCRIPT
sudo cat Installation.txt | grep 'sudo cpan' >> $SCRIPT
sudo chmod +x $SCRIPT
# The following is actual installation file generated. Don't run outside this script.
# You can delete or keep after running this script.
sudo ./$SCRIPT

#Used for stats, required utility
sudo apt install inxi -y



echo "\nDone with Life Log modules installation!\n"



