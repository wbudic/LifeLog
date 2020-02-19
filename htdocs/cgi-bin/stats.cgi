#!/usr/bin/perl
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
#no warnings 'uninitialized';
use Switch;

use CGI;
use CGI::Session '-ip_match';
use DBI;
use DateTime;
use DateTime::Format::SQLite;
use Number::Bytes::Human qw(format_bytes);
use IPC::Run qw( run );
use Syntax::Keyword::Try;

use lib "system/modules";
use lib $ENV{'PWD'}.'/htdocs/cgi-bin/system/modules';
require Settings;


my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>&Settings::logPath});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');

if(!$userid||!$dbname){
    if (&Settings::debug){
        $userid ="admin";
        $dbname = "data_admin_log.db";
        $password = "admin";
    }
    else{
    print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
    exit;
    }
}
my $db = "";

try{

my $database = &Settings::logPath . $dbname;
my @stat = stat $database;
my $dsn      = "DBI:SQLite:dbname=$database";
$db       = DBI->connect( $dsn, $userid, $password, { RaiseError => 1 } );

Settings::getConfiguration($db);


my $today = DateTime->now;
$today->set_time_zone(&Settings::timezone);

$ENV{'HOME'} = "~/";


print $cgi->header(-expires=>"+6os", -charset=>"UTF-8");
print $cgi->start_html(-title => "Log Data Stats", -BGCOLOR=>&Settings::bgcol,
                       -script=> [{-type => 'text/javascript', -src => 'wsrc/main.js'},
                                  {-type => 'text/javascript', -src => 'wsrc/jquery.js' },
                                  {-type => 'text/javascript', -src => 'wsrc/jquery-ui.js' }],
                       -style => [{-type => 'text/css', -src => "wsrc/".&Settings::css},
                                  {-type => 'text/css', -src => 'wsrc/jquery-ui.css' },
                                  {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css' }],

                       -onload  => "onBodyLoadGeneric()"
                );

my $tbl = '<table class="tbl" border="1px"><tr class="r0"><td colspan="5"><b>* Personal Log Data Statistics *</b></td></tr>';

my $log_rc = selectSQL('select count(rowid) from LOG;');
my ($stm1,$stm2) = "SELECT count(date) from LOG where date>=date('now','start of year');";
my $log_this_year_rc = selectSQL($stm1);
my $notes_rc = selectSQL('select count(LID) from NOTES where DOC is not null;');

#INCOME
$stm1 = 'SELECT sum(AMOUNT) from LOG where date>=date("now","start of year") AND AFLAG = 1;';
#EXPENSE
$stm2 = 'SELECT sum(AMOUNT) from LOG where date>=date("now","start of year") AND AFLAG = 2;';

my $expense = selectSQL($stm1);
my $income  = selectSQL($stm2);
my $gross   = big_money($income - $expense);
$expense    = big_money(sprintf("%.2f",$expense));
$income     = big_money(sprintf("%.2f",$income));


#Under perlbrew, sometimes STDOUT is not piped back to our cgi,
#utility inxi could be a perl written version on newer systems.
#So I use the inter processing module here for inxi. -- @wbudic
my  $HS = "";
my @cmd = ("inxi", "-b", "-c0");
run \@cmd, '>&', \$HS; #instead of -> system("inxi",'-b', '-c0');
    $HS .= `uptime -p`;


my $hardware_status = $HS;#`inxi -b -c0; uptime -p`;
my $syslog = "<b>".substr $HS, index($HS, 'Host:'), index($HS, 'Console:');
   $syslog .= "</b>\n".substr $HS, rindex($HS, 'Info:');
   $HS = "<pre>".`df -h -l -x tmpfs`."</pre>";
   $syslog .= $HS;
$hardware_status =~ s/\n/<br\/>/g;
$hardware_status =~ s/Memory:/<b>Memory:/g;
$hardware_status =~ s/Init:/<\/b>Initial:/g;
$hardware_status =~ s/up\s/<b>Server is up: /g;
$hardware_status .= "</b><p>$HS</p>";

my $prc = 'ps -eo size,pid,user,command --sort -size | awk \'{ hr=$1/1024 ; printf("%13.2f Mb ",hr) } { for ( x=4 ; x<=NF ; x++ ) { printf("%s ",$x) } print "" }\'';
my  $processes = `$prc | sort -u -r -`;
my  $dbSize = (uc format_bytes($stat[7], bs => 1000));
#Strip kernel 0 processes reported
$processes =~ s/\s*0.00.*//gd;
#trim reduce prefixed spacing
$processes =~ s/^\s+/  /gm;
my $year =$today->year();

my $IPPublic  = `curl -s https://www.ifconfig.me`;
my $IPPrivate = `hostname -I`; $IPPrivate =~ s/\s/<br>/g;

$tbl .=qq(<tr class="r1"><td>LifeLog App. Version:</td><td>).&Settings::release.qq(</td></tr>
	      <tr class="r0"><td>Number of Records:</td><td>$log_rc</td></tr>
          <tr class="r1"><td>No. of Records This Year:</td><td>$log_this_year_rc</td></tr>
          <tr class="r0"><td>No. of RTF Documents:</td><td>$notes_rc</td></tr>
          <tr class="r1"><td># Sum of Expenses For Year $year</td><td>$expense</td></tr>
          <tr class="r0"><td># Sum of Income For Year $year</td><td>$income</td></tr>
          <tr class="r1"><td>Gross For Year $year</td><td>$gross</td></tr>
          <tr class="r0"><td>$database</td><td>$dbSize</td></tr>
          <tr class="r1"><td>Public IP</td><td>$IPPublic</td></tr>
          <tr class="r0"><td>Private IP</td><td>$IPPrivate</td></tr>
</table>);


print qq(<div id="menu" title="To close this menu click on its heart, and wait." style="border: 1px solid black;padding: 5px;margin-top: 25px;">
<a class="a_" href="config.cgi">Config</a><hr>
<a class="a_" href="main.cgi">Log</a><hr>
<br>
<a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a>
</div>);

print qq(
<div style="text-align:left; border: 1px solid black; padding:5px;"><h2>Life Log Server Statistics</h2><hr>
    <span style="text-align:left; float:left; padding:15px;">$tbl<br></span>
    <span style="text-align:left; margin:1px; padding-right:15px; float:none;"><h2>Server Info</h2><hr><br>
    $hardware_status</span><hr>
</div>
<div class="tbl" style="text-align:left; border: 0px; padding:5px;">
    <b>Server Side Processes</b><hr>
</div>
<pre>$processes</pre>);
print $cgi->end_html;

&Settings::toLog($db,$syslog);
$db->disconnect();

}
 catch {
            my $err = $@;
            my $pwd = `pwd`;
            $pwd =~ s/\s*$//;
            print $cgi->header,
            "<font color=red><b>SERVER ERROR</b></font> on ".DateTime->now.
            "<pre>".$pwd."/$0 -> &".caller." -> [$err]","\n</pre>",
            $cgi->end_html;
 };


exit;

sub selectSQL {
    my @row = Settings::selectRecords($db, shift)->fetchrow_array();
    my $ret = $row[0];
    $ret = 0 if !$ret;
return $ret;
}

sub big_money {
  my $number = sprintf("%.2f", shift @_);
 # Add one comma each time through the do-nothing loop
 1 while $number =~ s/^(-?\d+)(\d\d\d)/$1,$2/;
  # Put the dollar sign in the right place
  $number =~ s/^(-?)/$1\$/;
return $number;
}

sub camm {
  my $amm = sprintf("%.2f", shift @_);
 # Add one comma each time through the do-nothing loop
 1 while $amm =~ s/^(-?\d+)(\d\d\d)/$1,$2/;
return $amm;
}

1.