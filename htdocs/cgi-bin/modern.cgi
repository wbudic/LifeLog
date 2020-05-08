#!/usr/bin/perl
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use warnings;
use strict;
use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;
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
use List::MoreUtils qw(uniq);

#DEFAULT SETTINGS HERE!
use lib "system/modules";
require Settings;

my $cgi = CGI->new;
my $sss = new CGI::Session( "driver:File", $cgi, { Directory => &Settings::logPath } );
my $sid      = $sss->id();
my $dbname   = $sss->param('database');
my $userid   = $sss->param('alias');
my $password = $sss->param('passw');
my $sssCDB   = $sss->param('cdb');
my $vmode;

if ( !$userid || !$dbname ) {
    print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
    exit;
}

my $database = &Settings::logPath . $dbname;
my $dsn      = "DBI:SQLite:dbname=$database";
my $db       = DBI->connect( $dsn, $userid, $password, { PrintError => 0, RaiseError => 1 } )
                      or LifeLogException->throw("Connection failed [$_");
my ( $imgw, $imgh );
#Fetch settings
 Settings::getConfiguration($db);
 Settings::getTheme();

### Page specific settings Here
my $TH_CSS      = &Settings::css;
my $BGCOL       = &Settings::bgcol;
#Set to 1 to get debug help. Switch off with 0.
my $DEBUG       = &Settings::debug;
#END OF SETTINGS

my $lang  = Date::Language->new(Settings::language());
my $today = DateTime->now;
   $today -> set_time_zone(Settings::timezone());


##Handle Session Keeps
$sss->expire(&Settings::sessionExprs);
#
$sss->flush();


print $cgi->header(-expires => "0s", -charset => "UTF-8");
print $cgi->start_html(
    -title   => "Personal Log",
    -BGCOLOR => $BGCOL,
    -onload  => "onBodyLoad(0,'".Settings::timezone()."','$today','".&Settings::sessionExprs."',0);",
    -style   => [
        { -type => 'text/css', -src => "wsrc/$TH_CSS" },
        { -type => 'text/css', -src => 'wsrc/jquery-ui.css' },
        { -type => 'text/css', -src => 'wsrc/jquery-ui.theme.css' },
        {
            -type => 'text/css',
            -src  => 'wsrc/jquery-ui-timepicker-addon.css'
        },
        { -type => 'text/css', -src => 'wsrc/tip-skyblue/tip-skyblue.css' },
        {
            -type => 'text/css',
            -src  => 'wsrc/tip-yellowsimple/tip-yellowsimple.css'
        },

        { -type => 'text/css', -src => 'wsrc/quill/katex.min.css' },
        { -type => 'text/css', -src => 'wsrc/quill/monokai-sublime.min.css' },
        { -type => 'text/css', -src => 'wsrc/quill/quill.snow.css' },
        { -type => 'text/css', -src => 'wsrc/jquery.sweet-dropdown.css' },

    ],
    -script => [
        { -type => 'text/javascript', -src => 'wsrc/main.js' },
        { -type => 'text/javascript', -src => 'wsrc/jquery.js' },
        { -type => 'text/javascript', -src => 'wsrc/jquery-ui.js' },
        {
            -type => 'text/javascript',
            -src  => 'wsrc/jquery-ui-timepicker-addon.js'
        },
        {
            -type => 'text/javascript',
            -src  => 'wsrc/jquery-ui-sliderAccess.js'
        },
        { -type => 'text/javascript', -src => 'wsrc/jquery.poshytip.js' },

        { -type => 'text/javascript', -src => 'wsrc/quill/katex.min.js' },
        { -type => 'text/javascript', -src => 'wsrc/quill/highlight.min.js' },
        { -type => 'text/javascript', -src => 'wsrc/quill/quill.min.js' },
        { -type => 'text/javascript', -src => 'wsrc/jscolor.js' },
        { -type => 'text/javascript', -src => 'wsrc/moment.js' },
        { -type => 'text/javascript', -src => 'wsrc/moment-timezone-with-data.js' },
        { -type => 'text/javascript', -src => 'wsrc/jquery.sweet-dropdown.js'}

    ],
);


print $cgi->end_html;


$db->disconnect();
undef($sss);
exit;