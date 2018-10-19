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


my $sth = $dbh->prepare( 'select count(rowid) from LOG;' );
my $rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";


my @row = $sth->fetchrow_array();

my $log_rc = $row[0];
$sth->finish;


my $stm = "SELECT count(date) from LOG where date>=date('now','start of year');";
$sth = $dbh->prepare( $stm );
$sth->execute();
@row = $sth->fetchrow_array();
my $log_this_year_rc = $row[0];
$sth->finish;

$stm = "SELECT sum(ammount) from LOG where date>=date('now','start of year');";
$sth = $dbh->prepare( $stm );
$sth->execute();
@row = $sth->fetchrow_array();
my $sum =  sprintf("%.2f",$row[0]);
$sth->finish;

my $hardware_status =`inxi -b -c0`;
$hardware_status =~ s/\n/<br\/>/g;

 $tbl = $tbl . '<tr class="r0"><td>Number of Records:</td><td>'.
 		$log_rc.'</td></tr>
		<tr class="r1"><td>No. of Records This Year:</td><td>'.
 		$log_this_year_rc.'</td></tr>
		<tr class="r0"><td># Sum For Year '.$today->year().
		':</td><td>'.$sum.'</td></tr>
		<tr class="r1"><td>'.$database.'</td><td>'.
 		 (uc format_bytes($stat[7], bs => 1000)).'</td></tr>

</table>';

print '<center><div>' . $tbl .'</div></center>';
print '<center><div style="text-align:left;"><br/><b>Server Info</b><br/><br/>' . $hardware_status .'</div></center>';

print $q->end_html;
$sth->finish;
$dbh->disconnect();
exit;

### CGI END
