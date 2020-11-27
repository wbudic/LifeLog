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

# Settings obtains from file escalated for anons to database configuration
# Currently we don't have an database set, and don't need it for this tester script.
# So we read and process the main.cnf file in via parser and transfer into Settings;
my $cnf = CNFParser->new($ENV{'PWD'}.'/dbLifeLog/main.cnf');
my $ptr = $cnf->anons();
Settings::anonsSet($ptr);

my $time  = Settings::today();
my $a = Settings::anon('TIME_ZONE_MAP');


print $time, $a , "\n";

1;