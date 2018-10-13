#!/usr/bin/perl

use strict;
use warnings;
use Try::Tiny;
 
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
my $sth;
my $today = DateTime->now;
$today->set_time_zone( $TIME_ZONE );

#####################
	&checkCreateTables;
#####################

my $stmtCat = "SELECT * FROM CAT;";
my $stmt    = "SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT FROM LOG ORDER BY rowid DESC, DATE DESC;";


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
<form id="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();">
<table class="tbl">
<tr class="r0"><th>Date</th><th>Time</th><th>Log</th><th>#</th><th>Category</th><th>Edit</th></tr>);

my $tbl_rc = 0;
my $tbl_rc_prev = 0;
my $tbl_cur_id;



###############
	&processSubmit;
###############
	#
	# Enable to see main query statement issued!
	#
#	print "### -> ".$stmt;

	#
	#
#Fetch entries!
#
$sth = $dbh->prepare( $stmt );
$rv = $sth->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
if($rv < 0) {
	     print "<p>Error->"& $DBI::errstri &"</p>";
}

my $tfId = 0;
my $id = 0;
my $rs_prev = $q->param('rs_prev'); 

 while(my @row = $sth->fetchrow_array()) {

	 $id = $row[0];
	 my $ct = $hshCats{$row[1]};
	 my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );
	 my $log = $row[3]; 
	 my $amm = $row[4];

	 #Apostrophe in the log value is doubled to avoid SQL errors.
		    $log =~ s/''/'/g;
	 #
	    
	 if(!$amm){
		 $amm = "0.00";
	 }
         if($tbl_rc_prev == 0){
 	    $tbl_rc_prev = $id;
	 }
	 if($tfId==1){
		 $tfId = 0;
	 }else{
		 $tfId = 1;
	 }

	         $tbl = $tbl . '<tr class="r'.$tfId.'"><td id="y'.$id.'">'. 
		 	$dt->ymd . '</td>' . 
		          '<td id="t'.$id.'">' . $dt->hms . "</td>" . '<td id="v'.$id.
			  '" class="log">' . $log . '</td>'.
			  '<td id="a'.$id.'">' . $amm .'</td>'.
			  '<td id="c'.$id.'">' . $ct .'</td>'.
			  '<td><input class="edit" type="button" value="Edit"
			 	 onclick="edit('.$id.');return false;"/>
			  <input name="chk" type="checkbox" value="'.$id.'"/>
			  </td></tr>';
	$tbl_rc += 1;	

	if($REC_LIMIT>0 && $tbl_rc==$REC_LIMIT){

		&buildNavigationButtons;
		last;
	}
 }

 #End of record set?
 if($rs_prev && $tbl_rc < $REC_LIMIT){
	&buildNavigationButtons(1);
 }

 if($tbl_rc==0){
	 $tbl = $tbl . "<tr><td colspan=\"5\"><b>Database is New or  Empty!</b></td></tr>\n";
 }
 $tbl = $tbl . '<tr class="r0"><td colspan="5" align="right">
 <input type="reset" value="Unselect All"/><input type="submit" value="Delete Selected"/>
 </td></tr>
 </table></form>';

my  $frm = qq(
 <form id="frm_log" action="main.cgi" onSubmit="return formValidation();">
	 <table class="tbl" border=0>
	 <tr class="r0"><td colspan="3"><b>* LOG ENTRY FORM *</b></td></tr>
	 <tr><td colspan="3"><br/></td></tr>
	 <tr>
		 <td>Date:</td><td id="al"><input id="ed" type="text" name="date" value=") .$today->ymd ." ". $today->hms . qq("><button onclick="return setNow();">Now</button></td><td>Category:</td>
		 </tr>
		 <tr><td>Log:</td><td><textarea id="el" name="log" rows="2" cols="60"></textarea></td>
 		 <td>).$cats.qq(</td></tr>
		 <tr><td>Ammount:</td><td id="al"><input id="am" name="am" type="number"/></td><td>
		 <input type="submit" value="Submit"/>
		 </td>
	</tr></table>
		 <input type="hidden" name="submit_is_edit" id="submit_is_edit" value="0"/>
		 <input type="hidden" name="submit_is_view" id="submit_is_view" value="0"/>
		 <input type="hidden" name="rs_all" value="0"/>
		 <input type="hidden" name="rs_cur" value="0"/>
		 <input type="hidden" name="rs_prev" value=").$tbl_rc_prev.q("/> </form>
 );


print "<center>";
print "<div>\n" . $frm ."</div>\n<br/>";
print "<div>\n" . $tbl ."</div>";
print "</center>";


print $q->end_html;
$sth->finish;
$dbh->disconnect();
exit;

### CGI END


sub buildNavigationButtons{
	#	
	#UNDER DEVELOPMENT!
	#
	my $is_end_of_rs = shift;
	

	if(!$tbl_cur_id){
	#Following is a quick hack as previous id as current minus one might not
	#coincide in the database table!
	$tbl_cur_id = $id-1;
	}
	if($tfId==1){
	 $tfId = 0;
	}else{
	 $tfId = 1;
	}

	$tbl = $tbl . '<tr class="r'.$tfId.'"><td>&dagger;</td>';

	if($rs_prev && $rs_prev>0){

	 $tbl = $tbl . '<td><input type="hidden" value="'.$rs_prev.'"/>
	 <input type="button" onclick="submitPrev('.$rs_prev.');return false;"
	  value="&lsaquo;&lsaquo;&ndash; Previous"/></td>';

	}
	else{
                $tbl = $tbl .'<td><i>Top</i></td>';
	}


	$tbl = $tbl .'<td colspan="1"><input type="button" onclick="viewAll();return false;" 
	value="View All"/></td>';

	if($is_end_of_rs == 1){
	  $tbl = $tbl .'<td><i>End</i></td>';
	}
	else{

	$tbl = $tbl . '<td><input type="button" onclick="submitNext('.$tbl_cur_id.');return false;" 
	value="Next &ndash;&rsaquo;&rsaquo;"/></td>';

	}

	$tbl = $tbl .'<td colspan="1"></td></tr>';
	#	
	#END OF UNDER DEVELOPMENT!
	#
}

sub processSubmit { 


	my $date = $q->param('date');
	my $log = $q->param('log');
	my $cat = $q->param('cat');
	my $amm = $q->param('am');

	my $edit_mode =  $q->param('submit_is_edit');
	my $view_mode =  $q->param('submit_is_view');
	my $view_all  =  $q->param('rs_all');

	
try{
	#Apostroph's need to be replaced with doubles  and white space fixed for the SQL.
	$log =~ s/(?<=\w) ?' ?(?=\w)/''/g;

	if($edit_mode && $edit_mode != "0"){
		#Update

		my $stm = "UPDATE LOG SET ID_CAT='".$cat."', DATE='". $date ."',
	       			LOG='".$log."' WHERE rowid=".$edit_mode.";"; 
		my $sth = $dbh->prepare($stm); 
			  $sth->execute();
		return;
	}

	if($view_all && $view_all=="1"){
		$REC_LIMIT = 0;
	}

	if($view_mode && $view_mode == "1"){
		#
		#UNDER DEVELOPMENT
		#
	
		my $rs = $q->param("rs_cur");
		my $rs_prev = $q->param("rs_prev");

		if($rs){
			 $stmt = 'SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT from LOG 
			          where rowid <= "'.$rs.'" ORDER BY rowid DESC, DATE DESC;';
			 return;
		}
	}

	if($log && $date && $cat){

		#check for double entry
		#
		my $sth = $dbh->prepare(
			  "SELECT DATE,LOG FROM LOG where DATE='".$date."' AND LOG='".$log."';"
			);

		$sth->execute();
		if(my @row = $sth->fetchrow_array()){
			return;
		}
		
		$sth = $dbh->prepare('INSERT INTO LOG VALUES (?,?,?,?)');
		$sth->execute( $cat, $date, $log, $amm);
	}
}
catch{
	print "ERROR:".$_;
}	
}



sub checkCreateTables(){

	$sth = $dbh->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='LOG';");
	$sth->execute();

	if(!$sth->fetchrow_array()) {
				my $stmt = qq(

				CREATE TABLE LOG (
				  ID_CAT TINY NOT NULL,
				  DATE DATETIME  NOT NULL,
				  LOG VCHAR(128) NOT NULL,
				  AMMOUNT integer
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
		$sth->execute(35, "Income");
	}

}

