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
# my $cnf = CNFParser->new($ENV{'PWD'}.'/dbLifeLog/main.cnf');
# my $ptr = $cnf->anons();
# Settings::anonsSet($ptr);
# my $time = Settings::today();
# my $cnf_tz = Settings::timezone();
# my $ret = Settings::setTimezone(undef, 'America/Texas');
# my $a = Settings::anon('TIME_ZONE_MAP');

use constant VW_LOG_WITH_EXCLUDES => "TEST_VIEW";

# print "tz:".$cnf_tz." time:". $time. "\n", $a , "\n\nTime America/Texas:$ret\n";
my $PAGE_EXCLUDES = "1=88,6";

print "SELECT * from LOG ",createPageViewSQL(), "\n";

#  SELECT rowid as ID,*, (select count(rowid) from LOG as recount where a.rowid >= recount.rowid) as PID
#         FROM LOG as a WHERE (ID_CAT!=88 AND ID_CAT!=6) OR date >= date('now', '-1 day') ORDER BY Date(DATE) DESC, Time(DATE) DESC;

    sub createPageViewSQL {
        my $days = 1;
        my $parse = $PAGE_EXCLUDES;
        my @a = split('=',$parse);
        if(scalar(@a)==2){
           $days  = $a[0];
           $parse = $a[1];
        }
        my $where =qq(WHERE date >= date('now', '-$days day') OR);
        @a = split(',',$parse);
        foreach (@a){
            $where .= " ID_CAT!=$_ AND";
        }
        $where =~ s/\s+OR$//;
        $where =~ s/\s+AND$//;
        return Settings::createViewLOGStmt(VW_LOG_WITH_EXCLUDES,$where);
    }


1;