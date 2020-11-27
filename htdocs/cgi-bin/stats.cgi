#!/usr/bin/perl
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use v5.10;
use strict;
use warnings;
#no warnings 'uninitialized';

use CGI;
use CGI::Pretty ":standard"; #Influde style subroutine for inline CSS
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use DBI;
use DateTime::Format::SQLite;
use Number::Bytes::Human qw(format_bytes);
use IPC::Run qw( run );
use Syntax::Keyword::Try;

use lib "system/modules";
use lib $ENV{'PWD'}.'/htdocs/cgi-bin/system/modules';
require Settings;

my $cgi     = CGI->new();
my $db      = Settings::fetchDBSettings($cgi);
my $sss     = Settings::session();
my $sid     = Settings::sid(); 
my $dbname  = Settings::dbname();
my $alias   = Settings::alias();
my $passw   = Settings::pass();

if(!$alias||!$dbname){
    if (Settings::debug()){
        $alias  ="admin";
        $dbname = "data_admin_log.db";
        $passw  = "admin";
    }
    else{
        print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
        exit;
    }
}
try{

my $today = Settings->today();

$ENV{'HOME'} = "~/";

my $CSS=<<CSS;
.main div {
    font-family: Bookman;
    text-align: left;
    vertical-align: left;
}
.info span{
    border: 1px solid black;
    padding: 5px;
    margin-top: 5px;
    margin-right: 15px;
    float: left;
    width:98%
}
.processes{
     margin-top: 5px; padding: 5px;
     border: 1px solid black;
     float: none;
}
CSS


print $cgi->header(-expires=>"+6os", -charset=>"UTF-8");
print $cgi->start_html(-title => "Log Data Stats", -BGCOLOR=>Settings::bgcol(),
                       -script=> [{-type => 'text/javascript', -src => 'wsrc/main.js'},
                                  {-type => 'text/javascript', -src => 'wsrc/jquery.js'},
                                  {-type => 'text/javascript', -src => 'wsrc/jquery-ui.js'}],
                       -style => [{-type => 'text/css', -src => "wsrc/".&Settings::css},
                                  {-type => 'text/css', -src => 'wsrc/jquery-ui.css'},
                                  {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'},
                                  {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'},
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

my $tbl = qq(<table class="tbl" border="1px"><tr class="r0"><td colspan="5" style="text-align:centered"><b>* Personal Log Data Statistics *</b></td></tr>
          <tr class="r1"><td>LifeLog App. Version:</td><td>).Settings::release().qq(</td></tr>
	      <tr class="r0"><td>Number of Records:</td><td>$log_rc</td></tr>
          <tr class="r1"><td>No. of Records This Year:</td><td>$log_this_year_rc</td></tr>
          <tr class="r0"><td>No. of RTF Documents:</td><td>$notes_rc</td></tr>
          <tr class="r1"><td># Sum of Expenses For Year $year</td><td>$expense</td></tr>
          <tr class="r0"><td># Sum of Income For Year $year</td><td>$income</td></tr>
          <tr class="r1"><td>Gross For Year $year</td><td>$gross</td></tr>
          <tr class="r0"><td>$dbname<td>$dbSize</td></tr>
          <tr class="r1"><td>Public IP</td><td>$IPPublic</td></tr>
          <tr class="r0"><td>Private IP</td><td>$IPPrivate</td></tr>
</table>);


print qq(<div id="menu" title="To close this menu click on its heart, and wait." style="border: 1px solid black;padding: 5px;margin-top: 25px;">
<a class="a_" href="main.cgi">Log</a><hr>
<a class="a_" href="config.cgi">Config</a><hr>
<a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a>
</div>);

print qq(
<div class="main">
    <hr><h2>Life Log Server Statistics</h2><hr>
    <div class="info">
        <span><b>Log Status & Information</b><hr>$tbl</span>
        <span><b>Server Info</b><hr>$hardware_status</span>       
    </div><br>
    <div class="processes" style="float:left;">
        <b>Server Side Processes</b><hr>
        <pre>$processes</pre>
    </div>

</div>);

print $cgi->end_html;
my $syslog = "<span>$hardware_status</span>"."<pre>\n".`df -h -l -x tmpfs`."</pre>";   
&Settings::toLog($db, $syslog);
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