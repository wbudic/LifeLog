#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#

use Try::Tiny;
use strict;
 
use CGI;
use CGI::Session '-ip_match';
use Text::CSV;

our $LOG_PATH    = '../../dbLifeLog/';
my @zones;
my $zone;
open my $fh, '<', '../../dbLifeLog/zone.csv' or die "Cannot open: $!";
while (my $line = <$fh>) {
  $line =~ s/\s*\z//;
  my @a = split /,/, $line;
  my $z = $a[2];
  push @zones, $z;
}
close $fh;


my $cgi = CGI->new;
my $session = new CGI::Session( "driver:File", $cgi, { Directory => $LOG_PATH } );
my $TH_CSS =  $session->param("theme");
my $BGCOL  =  $session->param("bgcolor");



print $cgi->header(-expires=>"+6s", -charset=>"UTF-8");    
print $cgi->start_html(-title => "Personal Log", -BGCOLOR=>"$BGCOL",
       		           -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		               -style =>{-type => 'text/css', -src => "wsrc/$TH_CSS"},
	        );


#TODO
my %regions = {};
my @cities;    
foreach my $zone (sort @zones){
    $zone =~ s/\"//g;
    my @p = split /\//, $zone;
    #America/Argentina/Rio_Gallegos
    my $region  = $p[0];
    my $country = $p[1];
    my $city    = $p[2];
    if(!$city){
        $city = $country;
        $country = $region;
    }

    if(exists($regions{$region})){
        @cities =@{ $regions{$region} };
    }else{
        @cities = ();
        $regions{$region} = \@cities;
    }
    push @cities, "$country/$city";
}
sub trim {my $r=shift; $r=~s/^\s+|\s+$//g; return $r}

print "<center>";
print "<h2 class='rz' style='text-align:center;'>World Time Zone Strings</h2><br>\n";
my $ftzmap = $ENV{'PWD'}.'tz.map';
if(-e $ftzmap){
    my $TIME_ZONE_MAP = "";
    open($fh, "<:perlio", $ftzmap) or LifeLogException->throw( "Can't open $ftzmap: $!");
    read  $fh, $TIME_ZONE_MAP, -s $fh;
    close $fh;
    print "<div class='rz' style='text-align:left;border-bottom: 0px cornflowerblue;'><b>Custom Mapped in $ftzmap</b></div>\n";
    print "<div class='rz' style='text-align:left;'><ul>\n";
    foreach (split('\n',$TIME_ZONE_MAP)){
        my @p = split('=', $_);
        if($p[0]){
            my $mapped = trim($p[0]);
            print "<li><a href=\"config.cgi?tz=$mapped\">$mapped</a></li>";
        }
    }
    print "</ul></div>\n";
    print "</div><br>\n";
}
foreach my $key (sort keys %regions){   if(!$key){next}
    my @country =  @{$regions{$key}}; 
    if( @country>0 ){
        print "<div class='rz' style='text-align:left;border-bottom: 0px cornflowerblue;'><b>$key</b></div>\n";
        print "<div class='rz' style='text-align:left;'><ul>\n";
        foreach my $entry (sort @country){
            if(!$entry){next}
            foreach my $city ($entry){
                if($city){
                print "<li><a href=\"config.cgi?tz=$city\">$city</a></li>";
                }
            }        
        }
           print "</ul></div>\n";
        print "</div><br>\n";

    }
}
print "</center>";
print $cgi->end_html;