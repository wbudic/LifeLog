#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Syntax::Keyword::Try;

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

use lib "system/modules";
require Settings;

my $db      = Settings::fetchDBSettings();
my $cgi     = Settings::cgi();
my $session = Settings::session();
my $sid     = Settings::sid(); 
my $dbname  = Settings::dbName();
my $alias   = Settings::alias();
my $passw   = Settings::pass();
my $today   = Settings::today();

my $action   = $cgi->param('action');
my $lid      = $cgi->param('id');
my $doc      = $cgi->param('doc');
my $bg       = $cgi->param('bg');
my $error    = "";

my ($nid,$response, $JSON) = 'Session Expired';

if  ( !$alias || !$dbname ) {

    &defaultJSON;
    print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
    print $JSON;

   exit;
}

my $formater = DateTime::Format::Strptime->new(
    pattern   => '%F %T',
    locale    => 'en_AU',
    time_zone => Settings::timezone(),
    on_error  => 'croak',
);
###############
&processSubmit;
###############
&defaultJSON;

print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
print $JSON;

$db->disconnect();
undef($session);
exit;


sub defaultJSON {

     my $content = "";
     if($action eq 'load' && !$error){
         $content = JSON->new->utf8->decode($doc);
     }
     $JSON = JSON->new->utf8->space_after->pretty->allow_blessed->encode
     ({date => $formater->format_datetime($today),
       response_origin =>  "LifeLog.".Settings::release(),
       alias => $alias, log_id => $lid, database=>Settings::dbFile(), action => $action, error=>$error,
       response=>$response,
       content=>$content
       #received => $doc
   });
}

sub processSubmit {

     # my $date = $cgi->param('date');
     my $st;

    try {
        if($action eq 'store'){

           $doc = qq({
                        "lid":"$lid",
                        "bg":"$bg",
                        "doc":$doc
                 });
           my $zip = compress($doc, Z_BEST_COMPRESSION);
              $st = $db->prepare("SELECT LID FROM NOTES WHERE LID = $lid;");
              $st -> execute();
           if($st->fetchrow_array() eq undef) {
               $st = $db->prepare("INSERT INTO NOTES(LID, DOC) VALUES (?, ?);");
               $st->execute($lid, $zip);
               $response = "Stored Document (id:$lid)!";
           }
           else{
               $st = $db->prepare("UPDATE NOTES SET DOC = ? WHERE LID = $lid;");
               $st->execute($zip);
               $response = "Updated Document (id:$lid)!";
           }
           
        }
        elsif($action eq 'load'){
           $st = $db->prepare("SELECT DOC FROM NOTES WHERE LID = $lid;");
           $st -> execute();
           my @arr = $st->fetchrow_array();
           if(@arr eq undef){
               $st = $db->prepare("SELECT DOC FROM NOTES WHERE LID = '0';");
               $st -> execute();
               @arr = $st->fetchrow_array();
           }
           $doc = $arr[0];
           $doc = uncompress($doc);
        #    print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
        #    print($doc);
        #    exit;
           $response = "Loaded Document!";

        }
        else{
            $error = "Your action ($action) sux's a lot!";
        }

    }catch {
        $error = ":LID[$lid]-> ".$_;
    }
}


sub authenticate {
    try {


          my $st = $db->prepare("SELECT * FROM AUTH WHERE alias='$alias' and passw='$passw';");
          $st->execute();
          if ( $st->fetchrow_array() ) { return; }

          #Check if passw has been wiped for reset?
          $st = $db->prepare("SELECT * FROM AUTH WHERE alias='$alias';");
          $st->execute();
          my @w = $st->fetchrow_array();
          if ( @w && $w[1] == "" ) {

              #Wiped with -> UPDATE AUTH SET passw='' WHERE alias='$userid';
              $st = $db->prepare(
                  "UPDATE AUTH SET passw='$passw' WHERE alias='$alias';");
              $st->execute();
              return;
          }



          print $cgi->center( $cgi->div("<b>Access Denied!</b> alias:$alias pass:$passw") );


          $db->disconnect();
          $session->flush();
          exit;

    }catch {
        print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
        print $cgi->p( "ERROR:" . $_ );
        print $cgi->end_html;
        exit;
    }
}
1;