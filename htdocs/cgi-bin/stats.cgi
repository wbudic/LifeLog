#!/usr/bin/perl
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use v5.10;
use strict;
use warnings;
#no warnings 'uninitialized';

use CGI;
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use CGI::Pretty ":standard"; #Includes style subroutine for inline CSS
use DBI;
use DateTime::Format::SQLite;
use Number::Bytes::Human qw(format_bytes);
use IPC::Run qw( run );
use Syntax::Keyword::Try;

use lib "system/modules";
use lib $ENV{'PWD'}.'/htdocs/cgi-bin/system/modules';
require Settings;

my $db      = Settings::fetchDBSettings();
my $cgi     = Settings::cgi();
my $sss     = Settings::session();
my $sid     = Settings::sid(); 
my $dbname  = Settings::dbFile();
my $alias   = Settings::alias();


if(!$alias||!$dbname){
        print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
        exit;
}
try{

my $today = Settings->today();

$ENV{'HOME'} = "~/";

my $CSS=<<_____CSS;
.main div {
    font-family: Bookman;
    text-align: left;    
}

.info span {
    border: 1px solid black;    
    margin-top: 5px;    
    float: left;
    width:97%
}

.table {
    display:table;
    border: 2px solid black;
    margin-right: 15px;
    width:45%;
}
.header {
    display:table-header-group;
    font-weight:bold;
    border-bottom: 1px solid black;
    margin-bottom: 2px;
}
.row {
    display:table-row;
}
.rowGroup {
    display:table-row-group;
}
.cell1 {
	display: table-cell;	
    padding: 5px;
    border-bottom: solid 1px;	
	border-right: solid 2px;
    vertical-align: top;
    width: 10%;
}
.cell2 {
    display:table-cell;    
    padding: 5px;
    border-bottom: solid 1px;
    vertical-align: top;
    width:25%;
}
.cell3 {
    display:table-cell;    
    padding: 5px;
    border-bottom: solid 1px;
    vertical-align: top;
    width:100%;
}
_____CSS

print $cgi->header(-expires=>"+6os", -charset=>"UTF-8");
print $cgi->start_html(-title => "Log Data Stats", -BGCOLOR=>Settings::bgcol(),
                       -script=> [{-type => 'text/javascript', -src => 'wsrc/main.js'},
                                  {-type => 'text/javascript', -src => 'wsrc/jquery.js'},
                                  {-type => 'text/javascript', -src => 'wsrc/jquery-ui.js'}],
                       -style => [{-type => 'text/css', -src => 'wsrc/jquery-ui.css'},
                                  {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'},
                                  {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'},
                                  {-type => 'text/css', -src => "wsrc/".Settings::css()},
                                  {-script=>$CSS}
                                 ],
                        -head => style({-type => 'text/css'}, $CSS),
                       -onload  => "onBodyLoadGeneric()"
                );

my $log_rc = selectSQL(Settings::selLogIDCount());
my ($stm1,$stm2) = "SELECT count(date) from LOG where ".Settings::selStartOfYear();
my $log_this_year_rc = selectSQL($stm1);
my $notes_rc = selectSQL('select count(LID) from NOTES where DOC is not null;');
my $id;

#INCOME
$stm1 = 'SELECT sum(AMOUNT) from LOG where '.Settings::selStartOfYear().' AND AFLAG = 1;';
#EXPENSE
$stm2 = 'SELECT sum(AMOUNT) from LOG where '.Settings::selStartOfYear().' AND AFLAG = 2;';


my $income  = selectSQL($stm1);
my $expense = selectSQL($stm2);
my $gross   = big_money($income - $expense);
$expense    = big_money(sprintf("%.2f",$expense));
$income     = big_money(sprintf("%.2f",$income));

#Under perlbrew, sometimes STDOUT is not piped back to our cgi,
#utility inxi could be a perl written version on newer systems.
#So I use the inter processing module here for inxi. -- @wbudic
my $buff = "";
my @cmd = ("/usr/bin/inxi", "-b", "-c0");
my $uptime = `uptime -p`;
my @ht = split(m/\s/,`hostname -I`);
my $hst = "";
   $hst = `hostname` . "($ht[0])" if (@ht);


#Gather into $buff
run \@cmd, ">&", \$buff; #instead of -> system("inxi",'-b', '-c0');
my @matches = $buff =~ /^(System.*)|(Machine.*)|(CPU.*)|(Drives.*)|(Info.*)|(Init.*)$/gm;#$txt=~/^(?=.*?\bone\b)(?=.*?\btwo\b)(?=.*?\bthree\b).*$/gim);
push (@matches, $uptime);
my $hardware_status = "<b>Host: </b>$hst<br>".join("\t", map { defined ? $_ : '' } @matches);
   $hardware_status =~ s/<.*filter>//gm; #remove crap
   $hardware_status =~ s/^(\w+:)/<b>$1<\/b>/m;
   #$hardware_status =~ s/(\t\w+:)/<b>$1<\/b>/gms;
   $hardware_status =~ s/\t+/<br>/gm; #TODO: This temp. resolves the regex needs to be adjusted so we join with <br>
   $hardware_status =~ s/Memory:/<br><b>Memory: <\/b>/g;   
   $hardware_status =~ s/up\s/<b>Server is up: <\/b>/g;

my $log = "<span>".$hardware_status."</span>"."<pre>\n".`df -h -l -x tmpfs`."</pre>";   
###
   Settings::toLog($db, $log);   
###
my $prc = 'ps -eo size,pid,user,command --sort -size | awk \'{ hr=$1/1024 ; printf("%13.2f Mb ",hr) } { for ( x=4 ; x<=NF ; x++ ) { printf("%s ",$x) } print "" }\'';
my $processes = `$prc | sort -u -r -`;
my @stat = stat Settings::dbFile();
my $dbSize =  "Not Avail";
   $dbSize = (uc format_bytes($stat[7], bs => 1000)) if !Settings::isProgressDB();
#Strip kernel 0 processes reported
$processes =~ s/\s*0.00.*//gd;
#trim reduce prefixed spacing
$processes =~ s/^\s+/  /gm;
my $year =$today->year();

my $IPPublic  = `curl -s https://www.ifconfig.me`;
my $IPPrivate = `hostname -I`; $IPPrivate =~ s/\s/<br>/g;
my $tbl = qq(
<div class="table r0" style="text-align:centered; float:left;">
  <div class="header">
      <div class="cell2" style="border-right:0;">Personal Log Data Statistics</div>
      <div class="cell2"></div>
  </div>
  <div class="row r1">
    <div class="cell1">LifeLog App. Version:</div>
    <div class="cell2">).Settings::release().qq(</div>
  </div>
  <div class="row r2">
        <div class="cell1">Number of Records:</div><div class="cell2">$log_rc</div>
  </div> 
  <div class="row r3">
        <div class="cell1">No. of Records This Year:</div><div class="cell2">$log_this_year_rc</div>
  </div>
    <div class="row r1">
        <div class="cell1">No. of RTF Documents:</div><div class="cell2">$notes_rc</div>
  </div>  <div class="row r0">
        <div class="cell1"># Sum of Expenses For Year $year</div><div class="cell2">$expense</div>
  </div>
  <div class="row r2">
        <div class="cell1"># Sum of Income For Year $year</div><div class="cell2">$income</div>
  </div>
  <div class="row r3">
        <div class="cell1"># Gross For Year $year</div><div class="cell2">$gross</div>
  </div>
  <div class="row r1">
        <div class="cell1">$dbname</div><div class="cell2">$dbSize</div>
  </div>
  <div class="row r2">
        <div class="cell1">Public IP</div><div class="cell2">$IPPublic</div>
  </div>
  <div class="row r3">
        <div class="cell1">Private IP</div><div class="cell2">$IPPrivate</div>
  </div> 
</div>
<div class="table r0">
    <div class="header"><div class="cell2">Server Info</div></div>
    <div class="row r1"><div class="cell3">$hardware_status</div></div>
</div>
);

print qq(<div id="menu" title="Menu" style="border: 2px solid black; padding: 5px; margin-top: 120px;">
<div class="r0" style="border: 1px solid black; margin: 2px; margin-bottom: 10px; padding:5px;"><b>Menu</b></div>
<div><a class="a_" href="main.cgi">Log</a><hr></div>
<div><a class="a_" href="config.cgi">Config</a><hr></div>
<div><a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a></div>
</div>);

print qq(
<div class="main">

    <div class="info">
        <span class="r2" style="padding:5px;width:98%;"><h3>Life Log Server Statistics</h3></span>
    </div>

    <div>&nbsp;</div>
    
    <div class="info">
        <span class="info r2" style="font-size:larger;padding:5px;width:98%;"><b>Status & Information</b></span>
        <span style="font-size:larger;padding:5px;width:98%;">$tbl</span>
    </div>

    <div>&nbsp;</div>

    <div class="info">    
        <span class="r2" style="font-size:larger;padding:5px;width:98%;"><b>Server Side Processes</b></span>
        <span style="border: 1px solid black; padding-right: 0px;  width:98%">
                <pre class="ql-container r2" style="max-height:480px; width:100%; overflow-x:auto; margin-top:0; margin-bottom:0"">$processes</pre>
        </span>
    </div>
</div>);

print $cgi->end_html;

$db->disconnect();

}
 catch {
            my $err = $@;
            my $pwd = `pwd`;
            $pwd =~ s/\s*$//;
            print  "<font color=red><b>SERVER ERROR</b></font> on ".DateTime->now. "->".$err,
            #"<pre>".$pwd."/$0 -> &".caller." -> [$err]","\n</pre>",
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