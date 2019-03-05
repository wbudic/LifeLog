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

my $q = CGI->new;

my $driver   = "SQLite"; 
my $database = "../../dbLifeLog/data_log.db";
my $dsn = "DBI:$driver:dbname=$database";
my $userid = "";
my $password = "";
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) 
   or die "<p>Error->"& $DBI::errstri &"</p>";
my $today = DateTime->now;
   $today->set_time_zone( 'Australia/Sydney' );

my $stmtCat = "SELECT * FROM CAT;";
my $st = $db->prepare( $stmtCat );
my $rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my %hshCats;
my $tbl_rc =0;

while(my @row = $st->fetchrow_array()) {
	$hshCats{$row[0]} = $row[1];
}


my $stmS = "SELECT rowid, ID_CAT, DATE, LOG from LOG WHERE";
my $stmE = " ORDER BY DATE DESC, rowid DESC;";
my $tbl = '<form name="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();">
		<table class="tbl">
		<tr class="r0"><th>Date</th><th>Time</th><th>Log</th><th>Category</th></tr>';

print $q->header(-expires=>"+6os");    

my $datediff = $q->param("datediff");
my $confirmed = $q->param('confirmed');
if ($datediff){
	     print $q->start_html(-title => "Date Difference Report", 
			     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
			     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

		);	  
				&DisplayDateDiffs;
}
else{
	if (!$confirmed){
	     print $q->start_html(-title => "Personal Log Record Removal", 
			     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
			     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

		);	  

				&NotConfirmed;
	}
	else{
		&ConfirmedDelition;
	}
}

print $q->end_html;
$db->disconnect();
exit;

sub DisplayDateDiffs{
    $tbl = '<table class="tbl">
	    <tr class="r0"><h2>Under Development Sorry!</h2></tr>';

    $tbl .= '</table>';

print "<div>".$tbl."</div>";
}


sub ConfirmedDelition{

	my $stm;
	my $stmS = 'DELETE FROM LOG WHERE '; 

	foreach my $prm ($q->param('chk')){
		$stm = $stmS . "rowid = '" . $prm ."';";
	        $st = $db->prepare( $stm );
		$rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
		if($rv < 0) {
		     print "<p>Error->"& $DBI::errstri &"</p>";
		}
	}
	
	
	print $q->redirect('main.cgi');

	$st->finish;
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
$st = $db->prepare( $stm );
$rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
if($rv < 0) {
	     print "<p>Error->"& $DBI::errstri &"</p>";
}


my $r_cnt = 0;
while(my @row = $st->fetchrow_array()) {

	 my $ct = $hshCats{@row[1]};
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

 $tbl = $tbl .  '<tr class="r0"><td colspan="4">
 <center>
 <h2>Please Confirm You Want <br/>The Above Record'.$plural.' Deleted?</h2>
 (Or hit you Browsers Back Button!)</center>
 </td></tr>
 <tr class="r0"><td colspan="4"><center>
 <input type="submit" value="I AM CONFIRMING!">
 </center>
 <input type="hidden" name="confirmed" value="1">
</td></tr>
</table></form>';

print '<center><div>' . $tbl .'</div></center>';

 $st->finish;
}

