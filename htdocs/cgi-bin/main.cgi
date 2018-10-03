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
my $rs_prev=0;




#SETTINGS HERE!
my $REC_LIMIT = 0;
my $TIME_ZONE = 'Australia/Sydney';
#END OF SETTINGS



print $q->header(-expires=>"+6os", -charset=>"UTF-8");    

print $q->start_html(-title => "Personal Log", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		     -onload => "loadedBody();"
		        );	  

my $rv;
my $today = DateTime->now;
$today->set_time_zone( $TIME_ZONE );


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

my $cats = '<select id="ec" name="cat">\n';
my %hshCats;

 while(my @row = $sth->fetchrow_array()) {
	$cats = $cats. '<option value="'.$row[0].'">'.$row[1].'</option>\n';
	$hshCats{$row[0]} = $row[1];
 }

$cats = $cats.'</select>';


my $tbl = qq(
<form name="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();">
<table class="tbl">
<tr class="r0"><th>Date</th><th>Time</th><th>Log</th><th>Category</th><th>Edit</th></tr>);

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

my $tfId = 0;

 while(my @row = $sth->fetchrow_array()) {

	 my $ct = $hshCats{@row[1]};
	 my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );
	 my $log = $row[3]; 
	    #Apostrophe in the log value is doubled to avoid SQL errors.
	    $log =~ s/''/'/g;

	 if($tfId==1){
		 $tfId = 0;
	 }else{
		 $tfId = 1;
	 }

	         $tbl = $tbl . '<tr class="r'.$tfId.'"><td id="y'.$row[0].'">'. 
		 	$dt->ymd . '</td>' . 
		          '<td id="t'.$row[0].'">' . $dt->hms . "</td>" . '<td id="v'.$row[0].
			  '" class="log">' . $log . "</td>".
			  '<td id="c'.$row[0].'">' . $ct .
			  '</td>
			  <td><input class="edit" type="button" value="Edit" onclick="edit(this);return false;"/><input name="chk" type="checkbox" value="'.$row[0].'"/>
			  </td></tr>';
	$tbl_rc += 1;	

	if($REC_LIMIT>0 && $tbl_rc>$REC_LIMIT){
	 	#	
		#UNDER DEVELOPMENT!
		#
		 if($tfId==1){
			 $tfId = 0;
		 }else{
			 $tfId = 1;
		 }

	         $tbl = $tbl . '<tr class="r'.$tfId.'"><td>&dagger;</td>';

		 if($rs_prev>0){

		         $tbl = $tbl . '<td><input type="hidden" value="'.$rs_prev.'"/>
		 	 <input type="button" onclick="submitPrev(this)"
			  value="&lsaquo;&lsaquo;&ndash; Previous"/></td>';

		 }


	        $tbl = $tbl . '<td><input type="hidden" name="rsc" value="'.  $tbl_rc .  '"/>
		<input type="button" onclick="return submitNext(this);" 
		value="Next &ndash;&rsaquo;&rsaquo;"/></td>';

		$tbl = $tbl .'<td colspan="2"></td></tr>';
		last;
	 	#	
		#END OF UNDER DEVELOPMENT!
		#
	}
 }

 if($tbl_rc==1){
	 $tbl = $tbl . "<tr><td colspan=\"5\"><b>Table is Empty!</b></td></tr>\n";
 }
 $tbl = $tbl . '<tr class="r0"><td colspan="5" align="right">
 <input type="reset" value="Unselect All"/><input type="submit" value="Delete Selected"/>
 </td></tr>
 </table></form>';

my  $frm = qq(
 <form name="frm_log" action="main.cgi" onSubmit="return formValidation();">
	 <table class="tbl">
	 <tr class="r0"><td colspan="3"><b>* LOG ENTRY FORM *</b></td></tr>
	 <tr><td colspan="3"><br/></td></tr>
	 <tr>
		 <td>Date:</td><td><input id="ed" type="text" name="date" value=") .$today->ymd ." ". $today->hms . qq("><button onclick="return setNow();">Now</button></td><td>Category:</td>
		 </tr>
		 <tr><td>Log:</td> <td><textarea id="el" name="log" rows="2" cols="60"></textarea></td>
 		 <td>).$cats.qq(</td></tr>
		 <tr><td></td><td></td><td>
		 <input type="submit" value="Submit"/>
		 </td>
	</tr></table>
		 <input type="hidden" name="submit_is_edit" id="submit_is_edit" value="0"/>
		 <input type="hidden" name="submit_is_view" id="submit_is_view" value="0"/>
</form>
 );


print "<center>";
print "<div>\n" . $frm ."</div>\n<br/>";
print "<div>\n" . $tbl ."</div>";
print "</center>";

print $q->end_html;
$sth->finish;
$dbh->disconnect();
exit;

sub processSubmit { 


	my $date = $q->param('date');
	my $log = $q->param('log');
	my $cat = $q->param('cat');
	my $edit_mode =  $q->param('submit_is_edit');
	my $view_mode =  $q->param('submit_is_view');

	
	   $rs_prev = $q->param("rs_cnt");

	#Apostroph's need to be replaced with doubles  and white space fixed for the SQL.
	$log =~ s/(?<=\w) ?' ?(?=\w)/''/g;

	if($edit_mode != "0"){
		#Update

		my $stm = "UPDATE LOG SET ID_CAT='".$cat."', DATE='". $date ."',
	       			LOG='".$log."' WHERE rowid=".$edit_mode.";"; 
		my $sth = $dbh->prepare($stm); 
			  $sth->execute();
		return;
	}

	if($view_mode != "0"){
		#
		#UNDER DEVELOPMENT
		#
	
		my $rsc = $q->param('rsc');		
 		$stmt = 'SELECT rowid, ID_CAT, DATE, LOG from LOG 
			where rowid > "'.$rsc.'" ORDER BY rowid DESC, DATE DESC;';
		return;
	}

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
