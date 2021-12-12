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

if type -p perl < /dev/null > /dev/null 2>&1  ; then

pver=$(perl -e "print $]")
[[ $pver<5.030000 ]] && echo -e "Warning your perl version is $pver might be outdated!\n Recomended perl version is 5.34+."
else
echo -e "Perl language not detected please install latest version, ideally (as sudo) from source.\n"
exit
fi

LifeLogInstall=install_lifelog_req_modules_2.4.sh
sudo cat Installation.txt | grep 'sudo apt install' | awk '{print $0, "-y"}' > $LifeLogInstall
sudo cat Installation.txt | grep 'sudo cpan' >> $LifeLogInstall 
sudo chmod +x $LifeLogInstall
# The following is actual installation file generated. Don't run outside this script.
# You can delete or keep after running this script.
sudo ./$LifeLogInstall

#Used for stats, required utility
sudo apt install inxi -y

echo;echo "Done with Life Log modules installation!"



