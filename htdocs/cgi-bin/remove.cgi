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



print $q->header(-expires=>"+6os");    

print $q->start_html(-title => "Personal Log Record Removal", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

		        );	  


my $today = DateTime->now;
$today->set_time_zone( 'Australia/Sydney' );

my $stmtCat = "SELECT * FROM CAT;";


$sth = $dbh->prepare( $stmtCat );
my $rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my %hshCats;

 while(my @row = $sth->fetchrow_array()) {
	$hshCats{$row[0]} = $row[1];
 }


my $stmS = "SELECT rowid, ID_CAT, DATE, LOG from LOG WHERE";
my $stmE = " ORDER BY rowid DESC, DATE DESC;";
my $tbl = '<form name="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();"><table border="1px" width="580px"><tr><th>Date</th><th>Time</th><th>Log</th><th>Category</th><th>Del</th></tr>';
my $confirmed = $q->param('confirmed');
if (!$confirmed){
	&NotConfirmed;
}
else{
	&ConfirmedDelition;
}

print $q->end_html;
$dbh->disconnect();

sub NotConfirmed{
#Get prms and build confirm table and check

### TODO	

#Fetch entries!
#
$sth = $dbh->prepare( $stmt );
$rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
if($rv < 0) {
	     print "<p>Error->"& $DBI::errstri &"</p>";
}



 while(my @row = $sth->fetchrow_array()) {

	 my $ct = $hshCats{@row[1]};
	 my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );

	         $tbl = $tbl . "<tr><td>". $dt->ymd . "</td>" . 
		          "<td>" . $dt->hms . "</td>" . "<td>" . $row[3] . "</td>".
			  "<td>" . $ct .
			  "</td><td><input type=\"checkbox\" value=\"".$row[0]."\"/> </td></tr>\n";
	$tbl_rc +=1;	
 }

 if($tbl_rc==1){
	 $tbl = $tbl . "<tr><td colspan=\"5\"><b>Table is Empty!</b></td></tr>\n";
 }
 $tbl = $tbl . "<tr><td colspan=\"4\"></td><td><input type=\"submit\" value=\"Del\"/></td></tr>";
 $tbl = $tbl . "</table></form>";

my  $frm = qq(
 <form name="frm_log" action="main.cgi" onSubmit="return formValidation();">
	 <table><tr>
		 <td>Date</td><td><input type="text" name="date" value=") .$today->ymd ." ". $today->hms . qq("></td>
		 </tr>
		 <tr><td>Log:</td> <td><textarea name="log" rows="2" cols="40"></textarea></td>
 		 <td>).$cats.qq(</td></tr>
		 <tr><td></td><td></td><td><input type="submit" value="Submit"></td>
	</tr></table>
</form>
 );



print "<div id=\"frm\">\n" . $frm ."</div>";
print "<div id=\"tbl\">\n" . $tbl ."</div>";
}

sub ConfirmedDelition{
#### TODO
}

