#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;

use LWP::UserAgent;
use File::Basename;

my $lwp = LWP::UserAgent->new(agent=>' Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0', cookie_jar=>{});

my $link = 'http://cdn.chv.me/images/thumbnails/7_Inch_Android_4_0_Tablet_zzMn_tSh.jpg.thumb_70x70.jpg';
my $file = fileparse $link;

my $resp = $lwp->mirror($link, "/home/will/dev/LifeLog/htdocs/cgi-bin/images/$file");

unless($resp->is_success) {
    print $resp->status_line;
}

#my $log ="Kurac palac deci davac. <<FRM<paw_<<B<Agreement> reached.\n";
my $log =
"Test <run></run><<IMG<Agreement> reached.<<B<errfrffff>\n";

=comment
	if($log =~ /<<IMG</){
	   my $idx = $-[0]+5;
	   my $len = index($log, '>', $idx);
	   my $sub = substr($log,$idx+1,$len-$idx-1);
	   my $url = qq(<img src="$sub"/>");
	   	  #$tags .= qq(<input id="tag$id" type="hidden" value="$log"/>\n);
	      $log=~s/<<IMG<(.*?)>/$url/o;		  
	}


if($log =~ /<<TITLE</){
	   my $idx = $-[0];
	   my $len = index($log, '>', $idx)-8;
	   my $sub =  "<h3>".substr($log,$idx+8,$len-$idx)."</h3>";
	      $log=~s/<<TITLE<(.*)>/$sub/gsi;
		  $log=~s/<<FRM<//gsi;
}
print $log;

<<IMG<https://cdn.images.express.co.uk/img/dynamic/128/590x/secondary/Cute-puppy-pictures-science-why-adorable-puppies-1355345.jpg>
My name is Cutie!
=cut