#!/usr/bin/perl -w
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
 
use CGI;
use CGI::Session '-ip_match';
use DBI;
use DateTime;
use DateTime::Format::SQLite;
use Number::Bytes::Human qw(format_bytes);

our $LOG_PATH    = '../../dbLifeLog/';

my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>$LOG_PATH});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');

if(!$userid||!$dbname){
	print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
	exit;
}

my $database = '../../dbLifeLog/'.$dbname;
my $dsn= "DBI:SQLite:dbname=$database";
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) or die "<p>Error->". $DBI::errstri ."</p>";




my @stat = stat $database;


#SETTINGS HERE!
my $REC_LIMIT = 25;
my $TIME_ZONE = 'Australia/Sydney';
#
#END OF SETTINGS
my $today = DateTime->now;
$today->set_time_zone( $TIME_ZONE );

my $q = CGI->new;

print $q->header(-expires=>"+6os", -charset=>"UTF-8");    

print $q->start_html(-title => "Log Data Stats", -BGCOLOR=>"#c8fff8",
       		         -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		             -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		             -onload => "loadedBody();"
		        );	  


my $tbl = '<table class="tbl" border="1px"><tr class="r0"><td colspan="4"><b>* PERSONAL LOG DATA STATS *</b></td></tr>';



my $log_rc = selectSQL('select count(rowid) from LOG;');
my $stm = "SELECT count(date) from LOG where date>=date('now','start of year');";
my $log_this_year_rc = selectSQL($stm);

my $id_expense = selectSQL('SELECT ID from CAT where name like "Expense";');
my $id_income  = selectSQL('SELECT ID from CAT where name like "Income";');

$stm = 'SELECT sum(ammount) from LOG where date>=date("now","start of year") 
		AND ID_CAT = '.$id_expense.';';
my $expense =  sprintf("%.2f",selectSQL($stm));

$stm = 'SELECT sum(ammount) from LOG where date>=date("now","start of year") 
	AND ID_CAT = '.$id_income.';';

my $income =  sprintf("%.2f",selectSQL($stm));
my $revenue = big_money($income - $expense);
my $hardware_status =`inxi -b -c0;uptime -p`;
$hardware_status =~ s/\n/<br\/>/g;
$hardware_status =~ s/Memory:/<b>Memory:/g;
$hardware_status =~ s/Init:/<\/b>Initial:/g;
$hardware_status =~ s/up\s/<b>Server is up: /g;
$hardware_status .= '</b>';
my $prc = 'ps -eo size,pid,user,command --sort -size | awk \'{ hr=$1/1024 ; printf("%13.2f Mb ",hr) } { for ( x=4 ; x<=NF ; x++ ) { printf("%s ",$x) } print "" }\'';


my  $processes = `$prc | sort -u -r -`;
#Strip kernel 0 processes reported
$processes =~ s/\s*0.00.*//gd;
 
$tbl = $tbl . '<tr class="r1"><td>Number of Records:</td><td>'.
 		$log_rc.'</td></tr>
		<tr class="r0"><td>No. of Records This Year:</td><td>'.
 		$log_this_year_rc.'</td></tr>
		<tr class="r0"><td># Sum of Expenses For Year '.$today->year().
		'</td><td>'.$expense.'</td></tr>
		<tr class="r0"><td># Sum of Income For Year '.$today->year().
		'</td><td>'.$income.'</td></tr>
		<tr class="r0"><td>Revenue For Year '.$today->year().
		'</td><td>'.$revenue.'</td></tr>
		<tr class="r1"><td>'.$database.'</td><td>'.
 		 (uc format_bytes($stat[7], bs => 1000)).'</td></tr>

</table>';

print '<div style="float:left; padding:10px;">' . $tbl .'</div>';
print '<div style="text-align:left;  border: 1px solid black;"><br/><b>Server Info</b><br/><br/>' . $hardware_status .'</div><br>';
print '<div style="text-align:left;"><br/><b>Processes Info</b><br/><br/><pre>' . $processes .'</pre></div>';

print $q->end_html;
$db->disconnect();
exit;

sub selectSQL{


	my $sth = $db->prepare( @_ );
	$sth->execute();
	my @row = $sth->fetchrow_array();
	$sth->finish;

return $row[0];
}

sub big_money {
  my $number = sprintf("%.2f", shift @_);
 # Add one comma each time through the do-nothing loop
 1 while $number =~ s/^(-?\d+)(\d\d\d)/$1,$2/;
  # Put the dollar sign in the right place
  $number =~ s/^(-?)/$1\$/;
return $number;
}
### CGI END
