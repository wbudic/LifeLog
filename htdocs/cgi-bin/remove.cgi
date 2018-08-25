#!/usr/bin/perl

use strict;
use warnings;
 
use CGI;
use DBI;

use DateTime;
use DateTime::Format::SQLite;

my $q = CGI->new;

my $driver   = "SQLite"; 
my $database = "../../dbLifeLog/data_log.db";
my $dsn = "DBI:$driver:dbname=$database";
my $userid = "";
my $password = "";
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
my $stmE = " ORDER BY rowid DESC, DATE DESC;";
my $tbl = '<form name="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();"><table border="1px" width="580px"><tr><th>Date</th><th>Time</th><th>Log</th><th>Category</th></tr>';
my $confirmed = $q->param('confirmed');
if (!$confirmed){
     print $q->header(-expires=>"+6os");    
     print $q->start_html(-title => "Personal Log Record Removal", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

        );	  

			&NotConfirmed;
	print $q->end_html;
}
else{
	&ConfirmedDelition;
}

$dbh->disconnect();


sub ConfirmedDelition{

	my $stm;
	my $stmS = 'DELETE FROM LOG WHERE '; 

	foreach my $prm ($q->param('chk')){
		$stm = $stmS . "rowid = '" . $prm ."';";
	        $sth = $dbh->prepare( $stm );
		$rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
		if($rv < 0) {
		     print "<p>Error->"& $DBI::errstri &"</p>";
		}
	}
	
	
	print $q->redirect('main.cgi');

}

sub NotConfirmed{
#Get prms and build confirm table and check
my $stm = $stmS ." ";
foreach my $prm ($q->param('chk')){
	$stm = $stm . "rowid = '" . $prm . "' OR ";
}
#rid=0 hack! ;)
	$stm = $stm . "rowid = '0' " . $stmE;

#
$sth = $dbh->prepare( $stm );
$rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
if($rv < 0) {
	     print "<p>Error->"& $DBI::errstri &"</p>";
}



 while(my @row = $sth->fetchrow_array()) {

	 my $ct = $hshCats{@row[1]};
	 my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );

	         $tbl = $tbl . "<tr><td>". $dt->ymd . "</td>" . 
		          "<td>" . $dt->hms . "</td>" . "<td>" . $row[3] . "</td>\n".
			  "<td>" . $ct. '<input type="hidden" name="chk" value="'.$row[0].'"></td></tr>';	
 }

 $tbl = $tbl .  '<tr><td colspan="4">
 <center>
 <h2>Please Confirm You Want This Deleted!</h2>
 (Or hit you Browsers Back Button!)</center>
 </td></tr>
 <tr><td colspan="4"><center>
 <input type="submit" value="I AM CONFIRMING!">
 </center>
 <input type="hidden" name="confirmed" value="1">
</td></tr>
</table></form>';

print '<div id="tbl">' . $tbl .'</div>';

}
