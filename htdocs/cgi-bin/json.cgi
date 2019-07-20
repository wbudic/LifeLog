#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Try::Tiny;
use Switch;

use CGI;
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Date::Language;
use Date::Parse;
use Time::localtime;
use Regexp::Common qw /URI/;
use JSON;

#DEFAULT SETTINGS HERE!
our $REC_LIMIT    = 25;
our $TIME_ZONE    = 'Australia/Sydney';
our $LANGUAGE     = 'English';
our $PRC_WIDTH    = '60';
our $LOG_PATH     = '../../dbLifeLog/';
our $SESSN_EXPR   = '+30m';
our $DATE_UNI     = '0';
our $RELEASE_VER  = '1.5';
our $AUTHORITY    = '';
our $IMG_W_H      = '210x120';
our $AUTO_WRD_LMT = 200;

#END OF SETTINGS

my $cgi = CGI->new;
my $session =
  new CGI::Session( "driver:File", $cgi, { Directory => $LOG_PATH } );
my $sid      = $session->id();
my $dbname   = "";#$session->param('database');
my $userid   = $session->param('alias');
my $password = $session->param('passw');
my $action   = $cgi->param('action');
my $lid      = $cgi->param('id');
my $doc      = $cgi->param('doc');

if ($AUTHORITY) {
    $userid = $password = $AUTHORITY;
    $dbname = 'data_' . $userid . '_log.db';
}
elsif ( !$userid || !$dbname ) {
   # print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
  #  exit;
}

my $database = '../../dbLifeLog/' . $dbname;
my $dsn      = "DBI:SQLite:dbname=$database";
my $db;
#$db      = DBI->connect( $dsn, $userid, $password, { RaiseError => 1 } );

### Authenticate session to alias password
#&authenticate;


my $lang  = Date::Language->new($LANGUAGE);
my $today = DateTime->now;
$today->set_time_zone($TIME_ZONE);



###############
#&processSubmit;
###############
my $json = JSON->new->utf8->space_after->pretty->allow_blessed->encode
     ({date => DateTime::Format::SQLite->format_datetime($today), 
       response_origin => "LifeLog.".$RELEASE_VER,
       response => "Feature Under Development!",
       alias => $userid,
       log_id => $lid,
       received => $doc
    });


print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
print $json;

#$db->disconnect();
undef($session);
exit;


sub processSubmit {

     # my $date = $cgi->param('date');
    
      try {
      }
      catch {
          print "ERROR:" . $_;
    }
}


sub authenticate {
      try {

          if ($AUTHORITY) {
              return;
          }

          my $st = $db->prepare(
              "SELECT * FROM AUTH WHERE alias='$userid' and passw='$password';"
          );
          $st->execute();
          if ( $st->fetchrow_array() ) { return; }

          #Check if passw has been wiped for reset?
          $st = $db->prepare("SELECT * FROM AUTH WHERE alias='$userid';");
          $st->execute();
          my @w = $st->fetchrow_array();
          if ( @w && $w[1] == "" ) {

              #Wiped with -> UPDATE AUTH SET passw='' WHERE alias='$userid';
              $st = $db->prepare(
                  "UPDATE AUTH SET passw='$password' WHERE alias='$userid';");
              $st->execute();
              return;
          }

          

          print $cgi->center( $cgi->div("<b>Access Denied!</b> alias:$userid pass:$password") );


          $db->disconnect();
          $session->flush();
          exit;

      }
      catch {
          print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
          print $cgi->p( "ERROR:" . $_ );
          print $cgi->end_html;
          exit;
    }
}




