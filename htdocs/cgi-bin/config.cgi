#!/usr/bin/perl -w
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Try::Tiny;
use Switch;
 
use CGI;
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Text::CSV;

#DEFAULT SETTINGS HERE!
our $REC_LIMIT   = 25;
our $TIME_ZONE   = 'Australia/Sydney';
our $LANGUAGE	   = 'English';
our $PRC_WIDTH   = '60';
our $LOG_PATH    = '../../dbLifeLog/';
our $SESSN_EXPR  = '+30m';
our $DATE_UNI    = '0';
our $RELEASE_VER = '1.3';
our $AUTHORITY   = '';
our $IMG_W_H     = '210x120';
#END OF SETTINGS

#15mg data post limit
$CGI::POST_MAX = 1024 * 15000;

my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>$LOG_PATH});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');
my  $sys = `uname -n`;
#my $acumululator="";

if(!$userid||!$dbname){
	print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
	exit;
}

my $database = '../../dbLifeLog/'.$dbname;
my $dsn= "DBI:SQLite:dbname=$database";
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) or die "<p>Error->"& $DBI::errstri &"</p>";

my $rv;
my $dbs;
my $today  = DateTime->now;
my $tz     = $cgi->param('tz');
my $csvp   = $cgi->param('csv');
   
	 switch ($csvp){
				case "1" {&exportLogToCSV}
				case "2" {&exportLogToCSV}
				case "3" {&exportCategoriesToCSV}
				case "4" {&exportCategoriesToCSV}				
	 }

	if($cgi->param('data_cat')){
			&importCatCSV;
	 }elsif($cgi->param('data_log')){
			&importLogCSV;
	 }


	  
		
#####################
	&getConfiguration;
#####################
$today->set_time_zone( $TIME_ZONE );
	
print $cgi->header(-expires=>"+6s", -charset=>"UTF-8");
print $cgi->start_html(-title => "Personal Log", -BGCOLOR=>"#c8fff8",
       		           -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		                 -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
	        );

my $stmtCat = 'SELECT * FROM CAT ORDER BY ID;';
$dbs = $db->prepare( $stmtCat );
$rv = $dbs->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my $status = "Ready for change!";

###############
&processSubmit;
###############

my $tbl = '<table id="ec" class="tbl" name="cats" border="0" width="'.$PRC_WIDTH.'%">
	          <tr class="r0"><td colspan="4"><b>* CATEGORIES CONFIGURATION *</b></td></tr>
            <tr class="r1"><th>ID</th><th>Category</th><th>Description</th></tr>
          ';

 while(my @row = $dbs->fetchrow_array()) {
	if($row[0]>0){ 
	   $tbl = $tbl. 
	   '<tr class="r0"><td>'.$row[0].'</td>
            <td><input name="nm'.$row[0].'" type="text" value="'.$row[1].'" size="12"></td>
	    <td><input name="ds'.$row[0].'" type="text" value="'.$row[2].'" size="64"></td>
	    </tr>';
	}
 }

my  $frm = qq(
	 <form id="frm_config" action="config.cgi">).$tbl.qq(
	  <tr class="r1">
		 <td><input type="text" name="caid" value="" size="3"/></td>
		 <td><input type="text" name="canm" value="" size="12"/></td>
		 <td><input type="text" name="cade" value="" size="64"/></td>		 
		</tr>
	  <tr class="r1">
		 <td colspan="2"><a href="#bottom">&#x21A1;</a>&nbsp;&nbsp;&nbsp;<input type="submit" value="Add New Category" onclick="return submitNewCategory()"/></td>
		 <td colspan="1"><b>Log Configuration In -> $dbname</b>&nbsp;<input type="submit" value="Change"/></td>
		</tr>
		<tr class="r1">
		  <td colspan="3"><div style="text-align:left; float"><font color="red">WARNING!</font> 
		   Removing or changing categories is permanent! Each category one must have an unique ID. 
			 Blank a category name to remove it. LOG records will change to the Unspecified (id 1) category! <br>
			 The category <b>Unspecified</b>, can't be removed!
			 </div>
			</td>			
		</tr>
		</table><input type="hidden" name="cchg" value="1"/></form><br>);
	 

$tbl = '<table id="ev" class="tbl" name="confs" border="0" width="'.$PRC_WIDTH.'%">
	          <tr class="r0"><td colspan="2"><b>* SYSTEM CONFIGURATION *</b></td></tr>
            <tr class="r1"><th>Variable</th><th>Value</th></tr>
       ';
my $stm = 'SELECT * FROM CONFIG;';
$dbs = $db->prepare( $stm );
$rv = $dbs->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

while(my @row = $dbs->fetchrow_array()) {
	   my $i = $row[0];
	   my $n = $row[1];
		 my $v = $row[2];
		 if($n eq "TIME_ZONE"){
			  $n = '<a href="time_zones.cgi" target=_blank>'.$n.'</a>';
			  if($tz){
				   $v = $tz;
			  }
			  $v = '<input name="var'.$i.'" type="text" value="'.$v.'" size="12">';		
		 }
		 elsif($n eq "DATE_UNI"){
			  my($l,$u)=("","");
				if($v == 0){
					 $l = "SELECTED"
				}
				else{
			     $u = "SELECTED"
				}
        $v = qq(<select id="dumi" name="var$i">
				         <option value="0" $l>Locale</option>
								 <option value="1" $u>Universal</option>
								</select>);
		 }
		 elsif($n ne "RELEASE_VER"){		 
			 $v = '<input name="var'.$i.'" type="text" value="'.$v.'" size="12">';
		 }		 
	   $tbl = $tbl. 
	   '<tr class="r0">
		    <td>'.$n.'</td>
		    <td>'.$v.'</td>	    
	    </tr>';
}

my  $frmVars = qq(
	 <form id="frm_vars" action="config.cgi">).$tbl.qq(	  
	  <tr class="r1">		
		 <td colspan=2 align=right><input type="submit" value="Change"/></td>
		</tr>	
		<input type="hidden" name="sys" value="1"/>
		</table></form><br>);

#
#Page printout from here!
#
my $prc_hdr = $PRC_WIDTH-2;
  print '<center><a name="top"/>';
	print "\n<div>\n" . $frm ."\n</div>\n";
	print "\n<div >\n" . $frmVars."\n</div>\n";	
	print "\n<div>\nSTATUS:" .$status. "\n</div>\n";	
	print qq(
		      <br><div id="rz" style="text-align:center; position:relative;width:"$PRC_WIDTH%" padding:0px;">
					<a href="main.cgi"><h2>Back to Main Log</h2></a><br><br><a href="login_ctr.cgi?logout=bye">LOGOUT</a></div>
					<br><hr>\n
					
					<table border="0">
						<tr><td><H3>CSV File Format</H3></td></tr>\n
						<form action="config.cgi" method="post" enctype="multipart/form-data">\n
						<tr style="border-left: 1px solid black;"><td>\n
					 		  <b>Import Categories</b>: <input type="file" name="data_cat" /></td></tr>\n
						<tr style="border-left: 1px solid black;"><td style="text-align:right;">
							 <input type="submit" name="Submit" value="Submit"/></p></td></tr>\n
						</form>\n
						<form action="config.cgi" method="post" enctype="multipart/form-data">\n
						<tr style="border-top: 1px solid black;border-right: 1px solid black;"><td>\n
					 		  <b>Import Log</b>: <input type="file" name="data_log" /></td></tr>\n
						<tr style="border-right: 1px solid black;"><td style="text-align:right;">\n
							 <input type="submit" name="Submit" value="Submit"/></p></td></tr>\n
					 	</form>\n
						 <tr><td style="text-align:right"><H3>To Server -> $sys -> $dbname</H3></td></tr>
					</table>
					</div>
					
					<br><div><a href="#top">&#x219F;</a>&nbsp;&nbsp;&nbsp;[<a href="config.cgi?csv=1">Export Log to CSV</a>] &nbsp;
					 [<a href="config.cgi?csv=2">View the Log in CSV Format</a>]</div>\n					
					<br><div>[<a href="config.cgi?csv=3">Export Categories to CSV</a>] &nbsp;
					[<a href="config.cgi?csv=4">View the Categories in CSV Format</a>]</div>\n
					<hr>

					<center>
					<div id="rz" style="text-align:left; position:relative;width:600px;">
					<h2>L-Tags Specs</h2>					
					<p>
					Life Log Tags are simple markup allowing fancy formatting and functionality 
					for your logs HTML layout.
					</p>
					<p>
					<b>&#60;&#60;B&#60;<i>{Text To Bold}</i><b>&#62;</b>
					</p>
					<p>
					<b>&#60;&#60;I&#60;<i>{Text To Italic}</i><b>&#62;</b>
					</p>					
					<p>
					<b>&#60;&#60;TITLE&#60;<i>{Title Text}</i><b>&#62;</b>
					</p>
					<p>
					<b>&#60;&#60;IMG&#60;<i>{url to image}</i><b>&#62;</b>
					</p>
					<p>
						<b>&#60;&#60;FRM&#60;<i>{file name}_frm.png}</i><b>&#62;</b><br><br>
						*_frm.png images file pairs are located in the ./images folder of the cgi-bin directory.<br>
						These are manually resized by the user. Next to the original.
						Otherwise considered as stand alone icons. *_frm.png Image resized to ->  width="210" height="120"
						<br><i>Example</i>:
						<pre>
		../cgi-bin/images/
			my_cat_simon_frm.png
			my_cat_simon.jpg	

          In loge entry, place:

	  &#60;&#60;FRM&#62;my_cat_simon_frm.png&#62; &#60;&#60;TITLE&#60;Simon The Cat&#62;
	  This is my pet, can you hold him for a week while I am on holiday?
            </pre>
					</p>
					<p>
					<b>&#60;&#60;LNK&#60;<i>{url to image}</i><b>&#62;</b><br><br>
					Explicitly tag an URL in the log entry. 
					Required if using in log IMG or FRM tags. 
					Otherwise link appears as plain text.
					</p>
					<hr>
          </p>
						<h3>Log Page Particulars</h3>
						&#x219F; or &#x21A1; - Jump links to top or bottom of page respectivelly.
					</p>
					</div>
					</center><a name="bottom"/>
					<hr>
	);

print '</center>';


print $cgi->end_html;
$db->disconnect();
exit;

sub processSubmit {

my $change = $cgi->param("cchg");
my $chgsys = $cgi->param("sys");
my $s;
my $d;

try{

if ($change == 1){

	while(my @row = $dbs->fetchrow_array()) {

	      my $cid = $row[0];
	      my $cnm = $row[1];
	      my $cds = $row[2];
	      
	      my $pnm  = $cgi->param('nm'.$cid);
	      my $pds  = $cgi->param('ds'.$cid);

	  if($pnm ne $cnm || $pds ne $cds){
		
		 if($cid!=1 && $pnm eq  ""){

		   $s = "SELECT rowid, ID_CAT FROM LOG WHERE ID_CAT =".$cid.";";
		   $d = $db->prepare($s); 
		   $d->execute();

		    while(my @r = $d->fetchrow_array()) {
		             $s = "UPDATE LOG SET ID_CAT=1 WHERE rowid=".$r[0].";";
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
	$status = "Upadated Categories!";
}

if($change > 1){

	#UNDER DEVELOPMENT!
	      my $caid  = $cgi->param('caid');
	      my $canm  = $cgi->param('canm');
	      my $cade  = $cgi->param('cade');
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
		 $status = "Added Category $canm!";
	}
	else{
		$status = "ID->".$caid." or -> Category->".$canm." is already assigned, these must be unique!";
	  print "<center><div><p><font color=red>Client Error</font>: $status</p></div></center>";
	}
	
}

if ($chgsys == 1){
	  &changeSystemSettings;		
		$status = "Changed System Settings!";
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




sub changeSystemSettings{
	try{
			$dbs = $db->prepare("SELECT * FROM CONFIG;");
		  $dbs->execute();
			while (my @r=$dbs->fetchrow_array()){ 
				my $var = $cgi->param('var'.$r[0]);
				if(defined $var){					
					switch ($r[1]) {
						case "REC_LIMIT" {$REC_LIMIT=$var;  updConfSetting($r[0],$var)}
						case "TIME_ZONE" {$TIME_ZONE=$var;  updConfSetting($r[0],$var)}
						case "PRC_WIDTH" {$PRC_WIDTH=$var;  updConfSetting($r[0],$var)}		
						case "SESSN_EXPR"{$SESSN_EXPR=$var; updConfSetting($r[0],$var)}
						case "DATE_UNI"  {$DATE_UNI=$var; updConfSetting($r[0],$var)}
						case "LANGUAGE"  {$LANGUAGE=$var; updConfSetting($r[0],$var)}
						case "AUTHORITY"  {$AUTHORITY=$var; updConfSetting($r[0],$var)}
						case "IMG_W_H"  {$IMG_W_H=$var; updConfSetting($r[0],$var)}
					 }
				}
			}
	}
	catch{
		print "<font color=red><b>SERVER ERROR->changeSystemSettings</b></font>:".$_;
	}
}

sub updConfSetting{
	my ($id, $val) = @_;
	my ($s,$d);
	$s = "UPDATE CONFIG SET VALUE='".$val."' WHERE ID=".$id.";"; 
	try{
		  $d = $db->prepare($s); 
		  $d->execute();
	}
	catch{
		print "<font color=red><b>SERVER ERROR</b>->updConfSetting[$s]</font>:".$_;
	}
}

sub exportLogToCSV{
	try{
		  
			my $csv = Text::CSV->new ( { binary => 1, strict => 1 } ); 		  
	    $dbs = $db->prepare("SELECT * FROM LOG;");
		  $dbs->execute();

		  if($csvp==2){
				 print $cgi->header(-charset=>"UTF-8", -type=>"text/html");	
				 print "<pre>\n";
			}
			else{
				 print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>"$dbname.csv");
			}
			
		 # print "ID_CAT,DATE,LOG,AMMOUNT\n";
			while (my $r=$dbs->fetchrow_arrayref()){ 
						 print $csv->print(*STDOUT, $r)."\n";
			}
			if($csvp==1){			
				 print "</pre>";
			}
			$dbs->finish();
			$db->disconnect();
			exit;
	}
	catch{
		print "<font color=red><b>SERVER ERROR</b>->exportLogToCSV</font>:".$_;
	}
}

sub exportCategoriesToCSV{
	try{
		  
			my $csv = Text::CSV->new ( { binary => 1, strict => 1 } ); 		  
	    $dbs = $db->prepare("SELECT ID, NAME, DESCRIPTION FROM CAT ORDER BY ID;");
		  $dbs->execute();

		  if($csvp==4){
				 print $cgi->header(-charset=>"UTF-8", -type=>"text/html");	
				 print "<pre>\n";
			}
			else{
				 print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>"$dbname.categories.csv");
			}
			
		  #print "ID,NAME,DESCRIPTION\n";
			while (my $row=$dbs->fetchrow_arrayref()){ 
						print $csv->print(*STDOUT, $row),"\n";
			}
			if($csvp==4){			
				 print "</pre>";
			}				
			$dbs->finish();		
			$db->disconnect();
			exit;
	}
	catch{
		print "<font color=red><b>SERVER ERROR</b>->exportLogToCSV</font>:".$_;
	}
}


sub importCatCSV{
	my $hndl = $cgi->upload("data_cat");
	my $csv = Text::CSV->new ( { binary => 1, strict => 1 } ); 	
  while (my $line = <$hndl>) {
         chomp $line;
			   if ($csv->parse($line)) { 
      		  my @flds   = $csv->fields();
						updateCATDB(@flds);
			   }else{
     			 warn "Data could not be parsed: $line\n";
  		   }		 
	}
}

sub updateCATDB{
	my @flds = @_;
	if(@flds>2){
	try{	
			my $id   = $flds[0];
			my $name = $flds[1];
			my $desc = $flds[2];
			#$acumululator .= $id."-".$name;
			
			#is it existing entry?
			$dbs = $db->prepare("SELECT ID, NAME, DESCRIPTION FROM CAT WHERE ID = '$id';");
			$dbs->execute();
			if(not defined $dbs->fetchrow_array()){
					$dbs = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
					$dbs->execute($id, $name, $desc);
					$dbs->finish;
			}
			else{
				#TODO Update
			}
		
	}
	catch{
		print "<font color=red><b>SERVER ERROR</b>->updateCATDB</font>:".$_;
	}
	}
}
sub importLogCSV{
	my $hndl = $cgi->upload("data_log");
	my $csv = Text::CSV->new ( { binary => 1, strict => 1 } ); 	
  while (my $line = <$hndl>) {
         chomp $line;
			   if ($csv->parse($line)) { 
      		  my @flds   = $csv->fields();
						updateLOGDB(@flds);
			   }else{
     			 warn "Data could not be parsed: $line\n";
  		   }		 
	}	
	$db->disconnect();
	print $cgi->redirect('main.cgi');
	exit;
}
sub updateLOGDB{
	my @flds = @_;
	if(@flds>3){
	try{	
			my $id_cat = $flds[0];
			my $date   = $flds[1];
			my $log    = $flds[2];
			my $amm    = $flds[3];
			my $pdate = DateTime::Format::SQLite->parse_datetime($date);
			#Check if valid date log entry?
			if($id_cat==0||$id_cat==""||!$pdate){
				return;
			}
			#is it existing entry?
			$dbs = $db->prepare("SELECT ID_CAT, DATE, LOG, AMMOUNT  FROM LOG WHERE date = '$date';");
			$dbs->execute();
			if(!$dbs->fetchrow_array()){
					$dbs = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?)');
					$dbs->execute( $id_cat, $pdate, $log, $amm);
			}
			#Renumerate
			$dbs = $db->prepare('select rowid from LOG ORDER BY DATE;');
			$dbs->execute();
			my @row = $dbs->fetchrow_array();
			my $cnt = 1;
 			while(my @row = $dbs->fetchrow_array()) {
			my $st_upd = $db->prepare("UPDATE LOG SET rowid=".$cnt.
			                            " WHERE rowid='".$row[0]."';");
				$st_upd->execute();
				$cnt = $cnt + 1;
			}
			$dbs->finish;
	}
	catch{
		print "<font color=red><b>SERVER ERROR</b>->exportLogToCSV</font>:".$_;
	}
	}
}


sub getConfiguration{
	try{
		$dbs = $db->prepare("SELECT * FROM CONFIG;");
		$dbs->execute();

		while (my @r=$dbs->fetchrow_array()){
			
			switch ($r[1]) {
				case "REC_LIMIT" {$REC_LIMIT=$r[2]}
				case "TIME_ZONE" {$TIME_ZONE=$r[2]}
				case "PRC_WIDTH" {$PRC_WIDTH=$r[2]}		
				case "SESSN_EXPR" {$SESSN_EXPR=$r[2]}
				case "DATE_UNI"  {$DATE_UNI=$r[2]}
				case "LANGUAGE"  {$LANGUAGE=$r[2]}				
				else {print "Unknow variable setting: ".$r[1]. " == ". $r[2]}
			}

		}
	}
	catch{
		print "<font color=red><b>SERVER ERROR</b></font>:".$_;
	}

}
