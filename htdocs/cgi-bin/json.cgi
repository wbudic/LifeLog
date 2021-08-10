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
use DBD::Pg;
use DBD::Pg qw(:pg_types);

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
use Crypt::Blowfish;
use Crypt::CBC;

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
         try{ $content = JSON->new->utf8->decode($doc) } catch {$error = "Error on doc with LID[$lid]-> ".$@}
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

sub cryptKey {
    $passw    = $alias.$passw.Settings->CIPHER_KEY;
    $passw    =~ s/(.)/sprintf '%04x', ord $1/seg;        
   return  substr $passw.Settings->CIPHER_PADDING, 0, 58;
}

sub processSubmit {

     # my $date = $cgi->param('date');
     my ($st, @arr);

    try {
        if($action eq 'store'){

           my $cipher = Crypt::CBC->new(-key  => cryptKey(), -cipher => 'Blowfish');
            $doc = qq({
                        "lid": "$lid",
                        "bg":  "$bg",
                        "doc": $doc
            });
            $doc = compress($cipher->encrypt($doc), Z_BEST_COMPRESSION);
            @arr = Settings::selectRecords($db, "SELECT LID FROM NOTES WHERE LID = $lid;")->fetchrow_array();
            if (!@arr) {
                            $st = $db->prepare("INSERT INTO NOTES(LID, DOC) VALUES (?, ?);");
                            $st->bind_param(1, $lid);
                            if(Settings::isProgressDB()){
                                $st->bind_param(2, $doc, { pg_type => DBD::Pg::PG_BYTEA })
                            }else{
                                $st->bind_param(2, $doc)
                            }
                            $st->execute();
                            $response = "Stored Document (id:$lid)!";
            }
            else{
                            $st = $db->prepare("UPDATE NOTES SET DOC = ? WHERE LID = $lid;");
                            if(Settings::isProgressDB()){$st->bind_param(1, $doc, { pg_type => DBD::Pg::PG_BYTEA })}else{$st->bind_param(1,$doc);}
                            $st->execute();                                
                            $response = "Updated Document (id:$lid)!";
            }
        }
        elsif($action eq 'load'){

           @arr = Settings::selectRecords($db, "SELECT DOC FROM NOTES WHERE LID = $lid;")->fetchrow_array();
           if(@arr eq undef){
                @arr = Settings::selectRecords($db,"SELECT DOC FROM NOTES WHERE LID = '0';")->fetchrow_array();
           }            
           $doc = $arr[0];
          
            my $d = uncompress($doc);
            my $cipher = Crypt::CBC->new(-key  => cryptKey(), -cipher => 'Blowfish');
            $doc = $cipher->decrypt($d);
          
            # print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
            # print($doc);
            # exit;
           $response = "Loaded Document!";

        }
        else{            
            $error = "Your action ($action) sux's a lot!";
        }

    }catch {
        if($action eq 'load' && $@ =~ /Ciphertext does not begin with a valid header for 'salt'/){# Maybe an pre v.2.2 old document?
            $doc = uncompress($doc);
            $response = "Your document LID[$lid] is not secure. Please resave it. [$@]";
            return;
        }
        $error = "Error on:LID[$lid]-> ".$@;
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