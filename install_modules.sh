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
sudo cat Installation.txt | grep 'sudo apt install' > install_lifelog_modules_1.1.8.sh
sudo cat Installation.txt | grep 'sudo cpan' >> install_lifelog_modules_1.1.8.sh
sudo chmod +x install_lifelog_modules_1.1.8.sh
# The following is actual installation file generated. Don't run outside this script.
# You can delete or keep after running this script.
sudo ./install_lifelog_modules_1.1.8.sh

echo "\nDone with Life Log modules installation!\n"



