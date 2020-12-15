#!/usr/bin/perl -w
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use experimental qw( switch );
use v5.10;
use strict;
use warnings;
use lib "system/modules";
# Settings are used in static context throughout.
require Settings;

use lib $ENV{'PWD'}.'/htdocs/cgi-bin/system/modules';
require CNFParser;


# my $TIME_ZONE_MAP ="";
# open(my $fh, '<',$ENV{'PWD'}.'/dbLifeLog/main.cnf') or LifeLogException->throw("Can't open main.cnf: $!");
#     while (my $line = <$fh>) {
#         chomp $line;
#         if($line =~ /<<TIME_ZONE_MAP</){
#             $TIME_ZONE_MAP = substr($line,16);
#                 while ($line = <$fh>) {
#                     chomp $line;
#                     last if($line =~ />$/);
#                     $TIME_ZONE_MAP .= $line . "\n";
#                 }
#         }
                
#         last if Settings::parseAutonom('CONFIG',$line); #By specs the config tag, is not an autonom, if found we stop reading. So better be last one spec. in file.
#     }
# close $fh;


# print "$TIME_ZONE_MAP\n";


# Settings obtains from file escalated for anons to database configuration
# Currently we don't have an database set, and don't need it for this tester script.
# So we read and process the main.cnf file in via parser and transfer into Settings;
my $cnf = CNFParser->new($ENV{'PWD'}.'/dbLifeLog/main.cnf');
my $ptr = $cnf->anons();
Settings::anonsSet($ptr);
my $time = Settings::today();
my $cnf_tz = Settings::timezone();
my $ret = Settings::setTimezone(undef, 'America/Texas');
my $a = Settings::anon('TIME_ZONE_MAP');



print "tz:".$cnf_tz." time:". $time. "\n", $a , "\n\nTime America/Texas:$ret\n";

1;