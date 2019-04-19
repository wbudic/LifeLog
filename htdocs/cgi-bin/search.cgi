#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#

use strict;
use warnings;
 
use CGI;
use DBI;
use DateTime;
use DateTime::Format::SQLite;

my $driver   = "SQLite"; 
my $database = "../../dbLifeLog/data_log.db";
my $dsn = "DBI:$driver:dbname=$database";
my $userid = $ENV{'DB_USER'};
my $password = $ENV{'DB_PASS'};


my $q = CGI->new;

my $dbh = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) 
   or die "<p>Error->"& $DBI::errstri &"</p>";

my $today = DateTime->now;
$today->set_time_zone( 'Australia/Sydney' );

my $stmtCat = "SELECT * FROM CAT;";


my $sth = $dbh->prepare( $stmtCat );
my $rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my %hshCats;
my $tbl_rc =0;

 while(my @row = $sth->fetchrow_array()) {
	$hshCats{$row[0]} = $row[1];
 }


my $stmS = "SELECT rowid, ID_CAT, DATE, LOG from LOG WHERE";
my $stmE = " ORDER BY DATE DESC, rowid DESC;";
my @keywords = split / /, $q->param('keywords');
my $stm= $stmS;
if(@keywords){
	foreach (@keywords)
	{
		$stm = $stm . " LOG LIKE '%" .$_."%'";
		if(  \$_ != \$keywords[-1]  ) {
			$stm = $stm." OR ";
		}
	}
	$stm = $stm . $stmE;
}
else{
	$stm = "";
}


     print $q->header(-expires=>"+6os");    
     print $q->start_html(-title => "Personal Log Record Removal", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

        );	  

	if($stm){
	     &build;
	}
	else{
		print $q->center($q->h2({-style=>'Color: red;'},'No Keywords Submitted!'));
	}

	print $q->pre("### -> ".$stm);

print $q->end_html;

$dbh->disconnect();



sub build{

my $tbl = '<table class="tbl">
		<tr class="r0"><th>Date</th><th>Time</th><th>Log</th><th>Category</th></tr>';
$sth = $dbh->prepare( $stm );
$rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
if($rv < 0) {
	     print "<p>Error->"& $DBI::errstri &"</p>";
}


my $r_cnt = 0;
while(my @row = $sth->fetchrow_array()) {

	 my $ct = $hshCats{$row[1]};
	 my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );

	 $tbl = $tbl . '<tr class="r1"><td>'. $dt->ymd . "</td>" . 
		  "<td>" . $dt->hms . "</td>" . "<td>" . $row[3] . "</td>\n".
		  "<td>" . $ct. '<input type="hidden" name="chk" value="'.$row[0].'"></td></tr>';	
	$r_cnt++;
}
my $plural = "";
if($r_cnt>1){
	$plural = "s";
}
 $tbl = $tbl . "</table>";

print '<center><div>' . $tbl .'</div></center>';

}
