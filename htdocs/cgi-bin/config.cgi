#!/usr/bin/perl

use strict;
use warnings;
use Try::Tiny;
use Switch;
 
use CGI;
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Text::CSV;

my $driver   = "SQLite"; 
my $database = "../../dbLifeLog/data_config_test_log.db";
my $dsn = "DBI:$driver:dbname=$database";
my $userid = $ENV{'DB_USER'};
my $password = $ENV{'DB_PASS'};

my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) 
   or die "<p>Error->"& $DBI::errstri &"</p>";


#DEFAULT SETTINGS HERE!
my $REC_LIMIT = 25;
my $TIME_ZONE = 'Australia/Sydney';
#END OF
my $rv;
my $dbs;
my $today = DateTime->now;
$today->set_time_zone( $TIME_ZONE );

#####################
	&checkCreateTablesAndSettings;
#####################

my $q = CGI->new;
	
print $q->header(-expires=>"+6os", -charset=>"UTF-8");    

print $q->start_html(-title => "Personal Log", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
#		     -onload => "loadedBody('".$rs_keys."');"
		        );	  



my $stmtCat = "SELECT * FROM CAT ORDER BY rowid;";


###############
&processSubmit;
###############
	#
$dbs = $db->prepare( $stmtCat );
$rv = $dbs->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my $cats = '<table id="ec" class="tbl" name="cats" border="0">
	    <tr class="r0"><td colspan="4"><b>* CATEGORIES CONFIGURATION *</b></td></tr>
            <tr class="r1"><th>ID</th><th>Category</th><th>Description</th><td></td></tr>
';
my %hshCats;

 while(my @row = $dbs->fetchrow_array()) {
	$cats = $cats. '<tr class="r0"><td>'.$row[0].'</td>
	<td><input name="cat'.$row[0].'" type="text" value="'.$row[1].'" size="12"></td>
	<td><input name="descr'.$row[0].'" type="text" value="'.$row[2].'" size="64"></td><td></td></tr>';
	$hshCats{$row[0]} = $row[1];
 }

	

my  $frm = qq(
	 <form id="frm_config" action="config.cgi">).$cats.qq(
	        <tr class="r1">
		 <td><input type="text" name="caid" value="" size="3"/></td>
		 <td><input type="text" name="canm" value="" size="12"/></td>
		 <td><input type="text" name="cade" value="" size="64"/></td>
		 <td></td>
		</tr>
	        <tr class="r1">
		 <td colspan="2"><input type="button" value="Add New Category" onclick="return submitNewCategory()"/></td>
		 <td colspan="2"><input type="submit" value="Change"/></td>
		</tr>
		<tr class="r1">
		<td colspan="4"><font color="red">WARNING!</font> Removing and changing categories is permanent! Adding one must have unique ID. Blanking an category will seek and remove old records under it in the LOG! Also ONLY Category <b>Unspecified</b> You Can't Change!<br/>If changing here things? Make a backup! (copy existing db, small file)</td>
</table><input type="hidden" name="cats_change" value="1"/></form><br/>);
	 

#
#Page printout from here!
#
print "<center>";
	print "\n<div>\n" . $frm ."\n</div>\n<br/>";
	print '</br><div><a href="main.cgi">Back to Main Log (Be wise)</a></div>';
print "</center>";


print $q->end_html;
$db->disconnect();
exit;

### CGI END


sub checkCreateTablesAndSettings{


$dbs = $db->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='LOG';");
 $dbs->execute();
try{
	if(!$dbs->fetchrow_array()) {
				my $stmt = qq(
					CREATE TABLE LOG (
					  ID_CAT TINY NOT NULL,
					  DATE DATETIME  NOT NULL,
					  LOG VCHAR(128) NOT NULL,
					  AMMOUNT integer
					);
				);

				$rv = $db->do($stmt);

				if($rv < 0) {
					      print "<p>Error->"& $DBI::errstri &"</p>";
				} 

				$dbs = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?)');

				$dbs->execute( 3, $today, "DB Created!",0);

				
	}

	$dbs = $db->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='CAT';");
	$dbs->execute();
	if(!$dbs->fetchrow_array()) {
			        my $stmt = qq(
					CREATE TABLE CAT(
					  ID TINY PRIMARY KEY NOT NULL,
					  NAME VCHAR(16),
					  DESCRIPTION VCHAR(64)
					 );
				);

				$rv = $db->do($stmt);

				if($rv < 0) {
					      print "<p>Error->"& $DBI::errstri &"</p>";
				} 

				$dbs = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');

		$dbs->execute(1,"Unspecified", "For quick uncategoriesed entries.");
		$dbs->execute(3,"File System", "Operating file system short log.");
		$dbs->execute(6,"System Log", "Operating system important log.");
		$dbs->execute(9,"Event", "Event that occured, meeting, historical important.");
		$dbs->execute(28,"Personal", "Personal log of historical importants, diary type.");
		$dbs->execute(32, "Expense", "Significant yearly expense.");
		$dbs->execute(35, "Income", "Significant yearly income.");
		$dbs->execute(40, "Work", "Work related entry, worth monitoring.");
	}

	$dbs = $db->prepare("SELECT name FROM sqlite_master
	       		      WHERE type='table' AND name='CONFIG';");
	$dbs->execute();
	
	if(!$dbs->fetchrow_array()) {

			        my $stmt = qq(

				CREATE TABLE CONFIG(
				  ID INT PRIMARY KEY NOT NULL,
				  NAME VCHAR(16),
				  VALUE VCHAR(64)
				);
							   
				);

				$rv = $db->do($stmt);

				if($rv < 0) {
					      print "<p>Error->"& $DBI::errstri &"</p>";
				} 

		$dbs = $db->prepare('INSERT INTO CONFIG VALUES (?,?)');
		$dbs->execute("REC_LIMIT", "25");
		$dbs->execute("TIME_ZONE", "Australia/Sydney");

	}

	$dbs = $db->prepare("SELECT * FROM CONFIG;");
	$dbs->execute();

	while (my @row=$dbs->fetchrow_array()){
		
		switch ($row[1]) {

			case "REC_LIMIT" {$REC_LIMIT=$row[2]}
			case "TIME_ZONE" {$TIME_ZONE=$row[2]}
			else {print "Unknow variable setting: ".$row[1]. " == ". $row[2]}

		}

	}
	
}
catch{
	print "ERROR:".$_;
}	

}
sub processSubmit { 
if ($q->param("cats_change")=="1"){
	
}
<< '*/';

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
		my $db = $db->prepare($stm); 
			  $db->execute();
		return;
	}

	if($view_all && $view_all=="1"){
		$REC_LIMIT = 0;
	}

	if($view_mode && $view_mode == "1"){

		if($rs_cur){
			 $stmt = 'SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT from LOG 
			          where rowid <= "'.$rs_cur.'" ORDER BY DATE DESC, rowid DESC;';
			 return;
		}
	}

	if($log && $date && $cat){

		#check for double entry
		#
		my $db = $db->prepare(
			  "SELECT DATE,LOG FROM LOG where DATE='".$date."' AND LOG='".$log."';"
			);

		$db->execute();
		if(my @row = $db->fetchrow_array()){
			return;
		}
		
		$db = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?)');
		$db->execute( $cat, $date, $log, $amm);
		#
		# UNDER DEVELOPMENT!
		#
		# After Insert renumeration check
		#
		my $dt = DateTime::Format::SQLite->parse_datetime($date);
		my $dtCur = DateTime->now();
		$dtCur->set_time_zone($TIME_ZONE);
		$dtCur = $dtCur - DateTime::Duration->new( days => 1);

		if($dtCur> $dt){
			print $q->p('<b>Insert is in the past!</b>');
			#Renumerate directly (not proper SQL but faster);
			$db = $db->prepare('select rowid from LOG ORDER BY DATE;');
			$db->execute();
			my @row = $db->fetchrow_array();
			my $cnt = 1;
 			while(my @row = $db->fetchrow_array()) {

			my $db_upd = $db->prepare("UPDATE LOG SET rowid=".$cnt.
						" WHERE rowid='".$row[0]."';");
				$db_upd->execute();
				$cnt = $cnt + 1;
			}
		}
	}
}
catch{
	print "ERROR:".$_;
}	


*/

}




