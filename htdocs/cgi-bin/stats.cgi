#!/usr/bin/perl

use strict;
use warnings;
 
use DBI;
use CGI;
use DateTime;
use DateTime::Format::SQLite;
use Number::Bytes::Human qw(format_bytes);

my $driver   = "SQLite"; 
my $database = "../../dbLifeLog/data_log.db";
my $dsn = "DBI:$driver:dbname=$database";
my $userid = "";
my $password = "";
my $dbh = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) 
   or die "<p>Error->"& $DBI::errstri &"</p>";

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

print $q->start_html(-title => "Personal Log Data Stats", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		     -onload => "loadedBody();"
		        );	  


my $tbl = '<table class="tbl" border="1px"><tr class="r1"><td colspan="4">Personal Log Data Stats</td></tr>';



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
my $hardware_status =`inxi -b -c0`;
$hardware_status =~ s/\n/<br\/>/g;
my $prc = 'ps -eo size,pid,user,command --sort -size | awk \'{ hr=$1/1024 ; printf("%13.2f Mb ",hr) } { for ( x=4 ; x<=NF ; x++ ) { printf("%s ",$x) } print "" }\'';
my  $processes = `$prc | sort -u -r -`;

 $tbl = $tbl . '<tr class="r0"><td>Number of Records:</td><td>'.
 		$log_rc.'</td></tr>
		<tr class="r1"><td>No. of Records This Year:</td><td>'.
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

print '<center><div>' . $tbl .'</div></center>';
print '<center><div style="text-align:left;"><br/><b>Server Info</b><br/><br/>' . $hardware_status .'</div></center>';
print '<center><div style="text-align:left;"><br/><b>Processes Info</b><br/><br/><pre>' . $processes .'</pre></div>i</center>';

print $q->end_html;
$dbh->disconnect();
exit;

sub selectSQL{


	my $sth = $dbh->prepare( @_ );
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
