#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#

use Try::Tiny;
use Switch;
 
use CGI;
use CGI::Session '-ip_match';
use Text::CSV;

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
print $cgi->header(-expires=>"+6s", -charset=>"UTF-8");    
print $cgi->start_html(-title => "Personal Log", -BGCOLOR=>"#c8fff8",
       		           -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		               -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
	        );


#TODO
my %countries = {};
my @states;    
foreach $zone (sort @zones){
    $zone =~ s/\"//g;
    my @p = split /\//, $zone;
    my $country = $p[0];
    my $city    = $p[1];
    my $region  = $p[2];

    if(length($country)==0){next;}

    if($region){
        $city = "$region/$city";
    }
    my $def = "$country/$city";
    
    if(exists($countries{$country})){
        $states = $countries{$country};    
    }else{
        $states = ();
        push (@{$countries{$country}}, $states);
      #  print "[$country] created list!\n";
    }
    push @{$states}, "$country/$city";
    #print "$zone<br>\n";    
}

print "<center>";
print "<h2 class='rz' style='text-align:center;border-bottom: 0px cornflowerblue;'>World Time Zone Strings</h2>\n";
foreach $key (sort keys %countries){   
    $states = $countries{$key}; 
    if( length($states)>0 ){
        print "<div class='rz' style='text-align:left;border-bottom: 0px cornflowerblue;'><b>$key</b></div>\n";
        print "<div class='rz' style='text-align:left;'><ul>\n";
        foreach $entry (sort @{$states}){
            if(!$entry){next}
            foreach $city ($entry){
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