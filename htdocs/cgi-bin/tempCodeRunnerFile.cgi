#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;

our $LOG_PATH    = '/home/will/dev/LifeLog/dbLifeLog/';

&removeOldSessions;

sub removeOldSessions{
	opendir(DIR, $LOG_PATH);
	my @files = grep(/cgisess_*/,readdir(DIR));
	closedir(DIR);

	my $now = time - (24 * 60 * 60);

	foreach my $file (@files) {
		my $mod = (stat("$LOG_PATH/$file"))[9];
		if($mod<$now){
		    print "$file\n";
		}
	}
}