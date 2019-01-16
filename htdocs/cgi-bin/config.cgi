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

$dbs = $db->prepare( $stmtCat );
$rv = $dbs->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";


###############
&processSubmit;
###############
	#
my $cats = '<table id="ec" class="tbl" name="cats" border="0">
	    <tr class="r0"><td colspan="4"><b>* CATEGORIES CONFIGURATION *</b></td></tr>
            <tr class="r1"><th>ID</th><th>Category</th><th>Description</th><td></td></tr>
';

 while(my @row = $dbs->fetchrow_array()) {

	if($row[0]>0){ 
	   $cats = $cats. 
	   '<tr class="r0"><td>'.$row[0].'</td>
            <td><input name="nm'.$row[0].'" type="text" value="'.$row[1].'" size="12"></td>
	    <td><input name="ds'.$row[0].'" type="text" value="'.$row[2].'" size="64"></td>
	    <td></td></tr>';
	}
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
		 <td colspan="2"><input type="submit" value="Add New Category" onclick="return submitNewCategory()"/></td>
		 <td colspan="2"><input type="submit" value="Change"/></td>
		</tr>
		<tr class="r1">
		<td colspan="4"><font color="red">WARNING!</font> 
		Removing and changing categories is permanent! Adding one must have unique ID. 
		Blanking an category will seek and change LOG records to Unspecified! Also ONLY the category <b>Unspecified</b> You can't CHANGE!<br/>If changing here things? Make a backup! (copy existing db file)</td>
</table><input type="hidden" name="cchg" value="1"/></form><br/>);
	 

#
#Page printout from here!
#
print "<center>";
	print "\n<div>\n" . $frm ."\n</div>\n<br/>";
	print '</br><div><a href="main.cgi">Back to Main Log</a></div>';
print "</center>";


print $q->end_html;
$db->disconnect();
exit;

### CGI END

sub processSubmit {

my $change = $q->param("cchg");
my $s;
my $d;

try{
if ($change == 1){


	while(my @row = $dbs->fetchrow_array()) {

	      my $cid = $row[0];
	      my $cnm = $row[1];
	      my $cds = $row[2];

	      
	      my $pnm  = $q->param('nm'.$cid);
	      my $pds  = $q->param('ds'.$cid);

	      if($cid!=1 && $pnm ne $cnm || $pds ne $cds){
		
		 if($pnm eq  ""){

		   $s = "SELECT rowid, ID_CAT FROM LOG WHERE ID_CAT =".$cid.";";
		   $d = $db->prepare($s); 
		   $d->execute();

		    while(my @r = $d->fetchrow_array()) {
		             $s = "UPDATE LOG SET CAT_ID=1 WHERE rowid=".$r[0].";";
		             $d = $db->prepare($s); 
		             $d->execute();
		     }

			 #Delete
                   $s = "DELETE FROM CAT WHERE ID=".$cid.";"; 
		   $d = $db->prepare($s); 
		   $d->execute();   

		 }
		 else{
			#Update
                   $s = "UPDATE CAT SET NAME='".$pnm."', DESCRIPTION='".$pds."' WHERE ID=".$cid.";"; 
		   $d = $db->prepare($s); 
		   $d->execute();
	        }
		 
	      }

	}
}

if($change > 1){

	#UNDER DEVELOPMENT!
	      my $caid  = $q->param('caid');
	      my $canm  = $q->param('canm');
	      my $cade  = $q->param('cade');
	      my $valid = 1;

	while(my @row = $dbs->fetchrow_array()) {

	      my $cid = $row[0];
	      my $cnm = $row[1];
	      my $cds = $row[2];
	      

	      if($cid==$caid || $cnm eq $canm){
                 $valid = 0;
		 last;
	      }
        }

	if($valid){
	   $d = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
	   $d->execute($caid,$canm, $cade);
	}
	else{
	  print "<center><div><p>
	         <font color=red>Client Error</font>: ID->".$caid." or -> Category->".$canm.
		 " is already assigned, these must be unique!</p></div></center>";
	}
}

  #Re-select
  $dbs = $db->prepare( $stmtCat );
  $rv = $dbs->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

}
catch{	  
	print "<center><div><p>".
 	   "<font color=red><b>SERVER ERROR</b></font>:".$_. "</p></div></center>";

}

}


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

	while (my @r=$dbs->fetchrow_array()){
		
		switch ($r[1]) {

			case "REC_LIMIT" {$REC_LIMIT=$r[2]}
			case "TIME_ZONE" {$TIME_ZONE=$r[2]}
			else {print "Unknow variable setting: ".$r[1]. " == ". $r[2]}

		}

	}
	
}
catch{
	print "<font color=red><b>SERVER ERROR</b></font>:".$_;
}

}





