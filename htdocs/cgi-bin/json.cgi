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
use DateTime::Format::Strptime;
use DateTime::Duration;
use Date::Language;
use Date::Parse;
use Time::localtime;
use Regexp::Common qw /URI/;
use JSON;
use IO::Compress::Gzip qw(gzip $GzipError);
use Compress::Zlib;


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
my $dbname   = $session->param('database');
my $userid   = $session->param('alias');
my $password = $session->param('passw');
my $action   = $cgi->param('action');
my $lid      = $cgi->param('id');
my $doc      = $cgi->param('doc');
my $error    = "";
my ($response, $json) = 'Session Expired';

my $lang  = Date::Language->new($LANGUAGE);
my $today = DateTime->now;
$today->set_time_zone($TIME_ZONE);

if ($AUTHORITY) {
    $userid = $password = $AUTHORITY;
    $dbname = 'data_' . $userid . '_log.db';
}
elsif ( !$userid || !$dbname ) {   

    &defaultJSON;
    print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
    print $json;

   exit;
}

my $database = '../../dbLifeLog/' . $dbname;
my $dsn      = "DBI:SQLite:dbname=$database";
my $db = DBI->connect( $dsn, $userid, $password, { RaiseError => 1 } );

### Authenticate session to alias password
#&authenticate;


my $strp = DateTime::Format::Strptime->new(
    pattern   => '%F %T',
    locale    => 'en_AU',
    time_zone => $TIME_ZONE,
    on_error  => 'croak',
);


###############
&processSubmit;
###############

&defaultJSON;

print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
print $json;

$db->disconnect();
undef($session);
exit;


sub defaultJSON(){

     my $content = $response; 
     if($action eq 'load' && !$error){
         $content = JSON->new->utf8->allow_nonref->decode($response);
         $response = "Loaded Document!";
     }
     $json = JSON->new->utf8->space_after->pretty->allow_blessed->encode
     ({date => $strp->format_datetime($today), 
       response_origin => "LifeLog.".$RELEASE_VER,       
       alias => $userid, log_id => $lid, database=>$database, action => $action, error=>$error,
       response=>$response,
       content=>$content,
       #received => $doc     
   });   
}

sub processSubmit {

     # my $date = $cgi->param('date');
     my $st;
  
      try {
        if($action eq 'store'){
    
           my $zip = compress($doc,Z_BEST_COMPRESSION);
           $st = $db->prepare("SELECT LID FROM NOTES WHERE LID = '$lid';"); 
           $st -> execute();
           if($st->fetchrow_array() eq undef) {
               $st = $db->prepare("INSERT INTO NOTES(LID, DOC) VALUES (?, ?);");               
               $st->execute($lid, $zip);
               $response = "Stored Document (id:$lid)!";
           }
           else{
               $st = $db->prepare("UPDATE NOTES SET DOC = ? WHERE LID = '$lid';");
               $st->execute($zip);
               $response = "Updated Document (id:$lid)!";
           }

        }
        elsif($action eq 'load'){
           $st = $db->prepare("SELECT DOC FROM NOTES WHERE LID = '$lid';"); 
           $st -> execute();
           my @arr = $st->fetchrow_array();
           if(!@arr){
               $st = $db->prepare("SELECT DOC FROM NOTES WHERE LID = '0';"); 
               $st -> execute();
               @arr = $st->fetchrow_array();
           }
           $doc = $arr[0];
           $response = uncompress($doc);
        }
        else{
            $error = "Your action ($action) sux's a lot!";
        }

      }
      catch {
          $error = ":LID[$lid]-> ".$_;
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




