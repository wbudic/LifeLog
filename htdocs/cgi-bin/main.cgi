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

print $q->start_html(-title => "Personal Log", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

		        );	  


my $rv;
my $today = DateTime->now;
$today->set_time_zone( 'Australia/Sydney' );

my $sth = $dbh->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='LOG';");
$sth->execute();

if(!$sth->fetchrow_array()) {
			my $stmt = qq(

			CREATE TABLE LOG (
			  ID_CAT TINY NOT NULL,
			  DATE DATETIME  NOT NULL,
			  LOG VCHAR(128) NOT NULL
					);
						   
			);

			$rv = $dbh->do($stmt);

			if($rv < 0) {
				      print "<p>Error->"& $DBI::errstri &"</p>";
			} 

			$sth = $dbh->prepare('INSERT INTO LOG VALUES (?,?,?)');

			$sth->execute( 3, $today, "DB Created!");

			
			 $stmt = qq(

			CREATE TABLE CAT(
			  ID INT PRIMARY KEY NOT NULL,
			  NAME VCHAR(16)
			);
						   
			);

			$rv = $dbh->do($stmt);

			if($rv < 0) {
				      print "<p>Error->"& $DBI::errstri &"</p>";
			} 

			$sth = $dbh->prepare('INSERT INTO CAT VALUES (?,?)');

	$sth->execute(1,"Unspecified");
	$sth->execute(3,"File System");
	$sth->execute(6,"System Log");
	$sth->execute(9,"Event");
	$sth->execute(28,"Personal");
	$sth->execute(32, "Expense");
}
my $stmtCat = "SELECT * FROM CAT;";
my $stmt = "SELECT rowid, ID_CAT, DATE, LOG from LOG ORDER BY rowid DESC, DATE DESC;";


$sth = $dbh->prepare( $stmtCat );
$rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my $cats = '<select name="cat">\n';
my %hshCats;

 while(my @row = $sth->fetchrow_array()) {
	$cats = $cats. '<option value="'.$row[0].'">'.$row[1].'</option>\n';
	$hshCats{$row[0]} = $row[1];
 }

$cats = $cats.'</select>';


my $tbl = '<form name="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();">
<table class="tbl"><tr class="tbl"><th>Date</th><th>Time</th><th>Log</th><th>Category</th><th>Del</th></tr>';
my $tbl_rc = 0;

##################################
&processSubmit;
##################################

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

	         $tbl = $tbl . '<tr class="tbl"><td>'. $dt->ymd . '</td>' . 
		          "<td>" . $dt->hms . "</td>" . '<td class="log">' . $row[3] . "</td>".
			  "<td>" . $ct .
			  "</td><td><input name=\"chk\" type=\"checkbox\" value=\"".$row[0]."\"/> </td></tr>\n";
	$tbl_rc +=1;	
 }

 if($tbl_rc==1){
	 $tbl = $tbl . "<tr><td colspan=\"5\"><b>Table is Empty!</b></td></tr>\n";
 }
 $tbl = $tbl . '<tr><td colspan="5" align="right">
 <input type="reset" value="Unselect All"/><input type="submit" value="Delete Selected"/>
 </td></tr>
 </table></form>';

my  $frm = qq(
 <form name="frm_log" action="main.cgi" onSubmit="return formValidation();">
	 <table class="entry"><tr>
		 <td>Date:</td><td><input type="text" name="date" value=") .$today->ymd ." ". $today->hms . qq("><button onclick="return setNow();">Now</button></td><td>Category:</td>
		 </tr>
		 <tr><td>Log:</td> <td><textarea name="log" rows="2" cols="60"></textarea></td>
 		 <td>).$cats.qq(</td></tr>
		 <tr><td></td><td></td><td><input type="submit" value="Submit"></td>
	</tr></table>
</form>
 );



print "<div id=\"frm\">\n" . $frm ."</div>";
print "<div id=\"tbl\">\n" . $tbl ."</div>";
print $q->end_html;

$dbh->disconnect();

sub processSubmit { 


	my $date = $q->param('date');
	my $log = $q->param('log');
	my $cat = $q->param('cat');

	if($log && $date && $cat){
		#check for double entry
		#
		
		my $sth = $dbh->prepare(
			  "SELECT DATE,LOG FROM LOG where DATE='".$date ."' AND LOG='".$log."';"
			);

		$sth->execute();
		if(my @row = $sth->fetchrow_array()){
			return;
		}

		
		$sth = $dbh->prepare('INSERT INTO LOG VALUES (?,?,?)');

		$sth->execute( $cat, $date, $log);
	
	}
}
