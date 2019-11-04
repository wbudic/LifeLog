#!/usr/bin/perl
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
#no warnings 'uninitialized';

use Try::Tiny;
use Switch;
 
use CGI;
use CGI::Session '-ip_match';
use DBI;
use DateTime;
use DateTime::Format::SQLite;
use Number::Bytes::Human qw(format_bytes);
my $HS;
#perlbrew fix, with main::sub not recognised in inxi.pl
BEGIN {
  $HS = `inxi -b -c0; uptime -p`;
}


#SETTINGS HERE!
my $REC_LIMIT = 25;
my $TIME_ZONE    = 'Australia/Sydney';
my $LOG_PATH     = '../../dbLifeLog/';
my $RELEASE_VER  = "";
my $THEME        = 0;
my $TH_CSS       = 'main.css';
#END OF SETTINGS

my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>$LOG_PATH});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');

if(!$userid||!$dbname){
   # print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
  #  exit;
  $userid ="admin";
  $dbname = "data_admin_log.db";
  $password = "admin";
}

my $database = '../../dbLifeLog/' . $dbname;
my $dsn      = "DBI:SQLite:dbname=$database";
my $db       = DBI->connect( $dsn, $userid, $password, { RaiseError => 1 } ) or die "<p>Error->" & $DBI::errstri & "</p>";
my @stat = stat $database;

##################
&getConfiguration;
##################


my $today = DateTime->now;
$today->set_time_zone( $TIME_ZONE );


my $BGCOL = '#c8fff8';
if ( $THEME eq 'Sun' ) {
    $BGCOL = '#D4AF37';
    $TH_CSS = "main_sun.css";
}elsif ($THEME eq 'Moon'){
    $TH_CSS = "main_moon.css";
    $BGCOL = '#000000';

}elsif ($THEME eq 'Earth'){
    $TH_CSS = "main_earth.css";
    $BGCOL = 'green';
}

$ENV{'HOME'} = "~/";


print $cgi->header(-expires=>"+6os", -charset=>"UTF-8");
print $cgi->start_html(-title => "Log Data Stats", -BGCOLOR=>"$BGCOL",
                       -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
                       -style =>{-type => 'text/css', -src => "wsrc/$TH_CSS"}                       
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

my $hardware_status = $HS;#`inxi -b -c0; uptime -p`;
$hardware_status =~ s/\n/<br\/>/g;
$hardware_status =~ s/Memory:/<b>Memory:/g;
$hardware_status =~ s/Init:/<\/b>Initial:/g;
$hardware_status =~ s/up\s/<b>Server is up: /g;
$hardware_status .= '</b>';

my $prc = 'ps -eo size,pid,user,command --sort -size | awk \'{ hr=$1/1024 ; printf("%13.2f Mb ",hr) } { for ( x=4 ; x<=NF ; x++ ) { printf("%s ",$x) } print "" }\'';


my  $processes = `$prc | sort -u -r -`;
my  $dbSize = (uc format_bytes($stat[7], bs => 1000));
#Strip kernel 0 processes reported
$processes =~ s/\s*0.00.*//gd;
my $year =$today->year();

my $IPPublic  = `curl -s https://www.ifconfig.me`;
my $IPPrivate = `hostname -I`; $IPPrivate =~ s/\s/<br>/g;
 
$tbl .=qq(<tr class="r1"><td>LifeLog App. Version:</td><td>$RELEASE_VER</td></tr>
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


print qq(<div id="menu" title="To close this menu click on its heart, and wait." style="border: 1px solid black;">
<a class="a_" href="config.cgi">Config</a><hr>
<a class="a_" href="main.cgi">Log</a><hr>
<br>
<a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a>
</div>);

print qq(<div style="text-align:left; border: 1px solid black; padding:5px;"><h2>Life Log Server Statistics</h2><hr>
    <span style="text-align:left; float:left; padding:15px;">$tbl<br></span>
    <span style="text-align:left; margin:1px;  padding-right:15px; float:none;"><h2>Server Info</h2><hr><br>
    $hardware_status</span></div>
<div class="tbl" style="text-align:left; border: 0px; padding:5px;">
<b>Server Side Processes</b><hr></div>
<pre style="text-align:left;">$processes</pre></div>);


print $cgi->end_html;
$db->disconnect();
exit;

sub selectSQL{

    my ($sth,$ret) = dbExecute( @_ );    
    my @row = $sth->fetchrow_array();
    $sth->finish;
    $ret = $row[0];
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

sub getConfiguration {
    try{
        my $st = dbExecute('SELECT ID, NAME, VALUE FROM CONFIG;');
        while (my @r=$st->fetchrow_array()){            
            switch ($r[1]) {
                case "RELEASE_VER" { $RELEASE_VER  = $r[2] }
                case "THEME"       {$THEME= $r[2]}
            }
        }
    }
    catch{
        print "<font color=red><b>SERVER ERROR</b></font>:".$_;
    }

}

sub dbExecute{
    my $ret	= $db->prepare(shift);
       $ret->execute() or die "<p>Error->"& $DBI::errstri &"</p>";
    return $ret;
}


### CGI END