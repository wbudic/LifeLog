#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use DBI;
#DEFAULT SETTINGS HERE!
our $LOG_PATH    = '/home/will/dev/LifeLog/dbLifeLog/';


#END OF SETTINGS


my @cre;

		open(my $fh, '<', '/home/will/dev/LifeLog/htdocs/cgi-bin/main.cnf' ) or die "Can't open main.cnf: $!";
		while (my $line = <$fh>) {
					chomp $line;
					if(rindex ($line, "<<AUTO_LOGIN<", 0)==0){
						 my $end = index $line, ">", 14;
						 my $crest = substr $line, 13, $end - 13;
                          @cre = split '/', $crest;
                         if(@cre &&scalar(@cre)>1){
                         print @cre; last;
                         }

					}
		}
       close $fh;

       	if(scalar(@cre)>1){			

			 my $database = $LOG_PATH.'data_'.$cre[0].'_log.db';
			 my $dsn= "DBI:SQLite:dbname=$database";
			 my $db = DBI->connect($dsn, $cre[0], $cre[1], { RaiseError => 1 }) 
								or die "<p>Error-></p>";
					#check if enabled.	
			 my $st = $db->prepare("SELECT VALUE FROM CONFIG WHERE NAME='AUTO_LOGIN';");
		 			$st->execute();
			 my @set = $st->fetchrow_array();
             print $set[0];
					if($set[0] eq "0"){
						my $alias = $cre[0];
						my $passw = $cre[1];						 
					}
                    else{
                        print "sucks cock!"
                    }
		}
=Comm
my $fh;
my $inData = 0;
open( $fh, "<:perlio", '/home/will/dev/LifeLog/htdocs/cgi-bin/main.cnf' )
  or die "Can't open main.cnf: $!";
read $fh, my $content, -s $fh;
my @lines     = split '\n', $content;
my %vars      = ();
my $table_type = 0;
foreach my $line (@lines) {

    #chomp $line;

    my @tick = split( "`", $line );

    if( index( $line, '<<CONFIG<' ) == 0 ){$table_type = 0; $inData = 0;}
	if( index( $line, '<<CAT<' ) == 0 ){$table_type = 1; $inData = 0;}
    

    if ( scalar @tick  == 2 ) {

        my %hsh = $tick[0] =~ m[(\S+)\s*=\s*(\S+)]g;
        if ( scalar %hsh ) {
            for my $key ( keys %hsh ) {
                my %nash = $key =~ m[(\S+)\s*\|\s*(\S+)]g;
                if ( scalar(%nash) ) {
                    for my $id ( keys %nash ) {
                        my $name  = $nash{$id};
                        my $value = $hsh{$key};
                        if ( $vars{$id} ) {
                            print "4Corrupt Entry -> $line\n";
                        }
                        else {
                            $vars{$id} = $name;
                            print "CNF->[$id]->$name:$value -> $tick[1]\n";
                            $inData = 1;
                        }
                    }
                }
                else {
                    print "3Corrupt Entry -> $line\n";
                }
            }
        }
        else {
			if($table_type==0){
            	print "2Corrupt Entry -> $line\n";
			}
			else{
				my @pair = $tick[0] =~ m[(\S+)\s*\|\s*(\S+)]g;
                if ( scalar(@pair)==2 ) {					   
					my $id  = $pair[0];
                    my $name = $pair[1];
					print "CAT-> [$id]->$name [[ $tick[1] ]]\n";         
                }
                else {
                    print "3Corrupt Entry -> $line\n";
                }
			}
        }
    }
    elsif ( $inData && length($line) > 0 ) {
        if ( scalar(@tick) == 1 ) {
            print "Corrupt Entry, no description supplied -> $line\n";
        }
        else {
            print "1Corrupt Entry -> $line\n";
        }
    }

}
close $fh;
=cut

=comment

		   for my $key (keys %pv) {
			    my %id = $key =~ m[(\s*)\|(\s*)]g;
    			
           }


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
=cut

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
