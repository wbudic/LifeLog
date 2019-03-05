#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Try::Tiny;
 
use CGI;
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Regexp::Common qw /URI/;

my $driver   = "SQLite"; 
my $database = "../../dbLifeLog/data_log.db";
my $dsn = "DBI:$driver:dbname=$database";
my $userid = $ENV{'DB_USER'};
my $password = $ENV{'DB_PASS'};

my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) 
   or die "<p>Error->"& $DBI::errstri &"</p>";




#SETTINGS HERE!
our $REC_LIMIT = 25;
our $TIME_ZONE = 'Australia/Sydney';
#END OF SETTINGS

my $q = CGI->new;
my $tbl_rc = 0;
my $tbl_rc_prev = 0;
my $tbl_cur_id;
my $rs_keys = $q->param('keywords');
my $rs_cat_idx = $q->param('category');
my $rs_dat_from = $q->param('v_from');
my $rs_dat_to = $q->param('v_to');
my $rs_prev = $q->param('rs_prev'); 
my $rs_cur = $q->param('rs_cur');
my $stmS = "SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT from LOG WHERE";
my $stmE = " ORDER BY DATE DESC;";
my $stmD = "";
if(!$rs_dat_to){
	$rs_dat_to = 'now';
}

if($rs_dat_from && $rs_dat_to){
	$stmD = " DATE BETWEEN date('".$rs_dat_from."') AND date('".$rs_dat_to."') ";
}

my $toggle =""; if($rs_keys||$rs_cat_idx||$stmD){$toggle=1;};
	
print $q->header(-expires=>"+6os", -charset=>"UTF-8");    

print $q->start_html(-title => "Personal Log", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		     -onload => "loadedBody('".$toggle."');"
		        );	  

my $rv;
my $st;
my $today = DateTime->now;
$today->set_time_zone( $TIME_ZONE );

#####################
	&checkCreateTables;
#####################

my $stmtCat = "SELECT * FROM CAT;";
my $stmt    = "SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT FROM LOG ORDER BY DATE DESC, rowid DESC;";


$st = $db->prepare( $stmtCat );
$rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my $cats = '<select id="ec" name="cat" onChange="updateSelCategory(this)">\n';
my %hshCats;

 while(my @row = $st->fetchrow_array()) {
	$cats = $cats. '<option value="'.$row[0].'">'.$row[1].'</option>\n';
	$hshCats{$row[0]} = $row[1];
 }

$cats = $cats.'</select>';


my $tbl = qq(<form id="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();">
<table class="tbl">
<tr class="r0">
	<th>Date</th><th>Time</th><th>Log</th><th>#</th><th>Category</th><th>Edit</th>
</tr>);


if($rs_keys){
	
	my @keywords = split / /, $rs_keys;
	if($rs_cat_idx){
		$stmS = $stmS ." ID_CAT='".$rs_cat_idx."' AND";
	}	
	if($stmD){
		$stmS = $stmS .$stmD." AND";
	}

	if(@keywords){
		foreach (@keywords)
		{
			$stmS = $stmS . " LOWER(LOG) REGEXP '\\b" . lc $_."\\b'";
			if(  \$_ != \$keywords[-1]  ) {
				$stmS = $stmS." OR ";
			}
		}
		$stmt = $stmS . $stmE;
	}
}
elsif($rs_cat_idx){

	if($stmD){
	      $stmt = $stmS.$stmD. " AND ID_CAT='".$rs_cat_idx."'" .$stmE;
	}
	else{
      	     $stmt = $stmS." ID_CAT='".$rs_cat_idx."'" .$stmE;
      	}
}
else{
      if($stmD){
      	     $stmt = $stmS.$stmD.$stmE;
      }
}
###############
	&processSubmit;
###############
 #
 # Enable to see main query statement issued!
 #print $q->pre("### -> ".$stmt);

#
#Fetch entries!
#
$st = $db->prepare( $stmt );
$rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
if($rv < 0) {
	     print "<p>Error->"& $DBI::errstri &"</p>";
}

my $tfId = 0;
my $id = 0;
my $tbl_start = index $stmt, "<=";
my $re_a_tag = qr/<a\s+.*?>.*<\/a>/si ;

if($tbl_start>0){
	#check if we are at the beggining of the LOG table?
	
	my $stc = $db->prepare('select rowid from LOG order by rowid DESC LIMIT 1;');
	   $stc->execute();
	my @row =$stc->fetchrow_array();
	if($row[0] == $rs_prev && $rs_cur == $rs_prev){
		$tbl_start = -1;
	}
	$stc->finish();
}


 while(my @row = $st->fetchrow_array()) {

	 $id = $row[0];
	 my $ct = $hshCats{$row[1]};
	 my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );
	 my $log = $row[3]; 
	 my $amm = sprintf "%.2f", $row[4];

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

	 #Replace with a full link an HTTP URI
	 my @chnks = split(/($re_a_tag)/si , $log) ;  
  	 foreach my $ch_i ( @chnks ) {
	     next if $ch_i =~ /$re_a_tag/ ;
	        $ch_i =~ s/https/http/gsi;
	        $ch_i =~ s/($RE{URI}{HTTP})/<a href="$1" target=_blank>$1<\/a>/gsi;
	 }	
	 $log = join('' , @chnks) ;


         $tbl = $tbl . '<tr class="r'.$tfId.'"><td id="y'.$id.'">'. $dt->ymd . '</td>'. 
		          '<td id="t'.$id.'">' . $dt->hms . "</td>" .
			  '<td id="v'.$id.'" class="log">' . $log . '</td>'.
			  '<td id="a'.$id.'">' . $amm .'</td>'.
			  '<td id="c'.$id.'">' . $ct .'</td>'.
			  '<td><input class="edit" type="button" value="Edit"
			 	 onclick="return edit('.$id.');"/>
			  <input name="chk" type="checkbox" value="'.$id.'"/>
			  </td>
			</tr>';
	$tbl_rc += 1;	

	if($REC_LIMIT>0 && $tbl_rc==$REC_LIMIT){

		&buildNavigationButtons;
		last;
	}
 }

 #End of table?
 if($rs_prev && $tbl_rc < $REC_LIMIT){
	$st = $db->prepare( "SELECT count(*) FROM LOG;" );
	$st->execute();	
	my @row = $st->fetchrow_array(); 
	if($row[0]>$REC_LIMIT){
	   &buildNavigationButtons(1);
	}
 }

 if($tbl_rc==0){
	 
    if($stmD){
       $tbl = $tbl . '<tr><td colspan="5">
       <b>Search Failed to Retrive any records on select: [<i>'. $stmD .'</i>] !</b></td>
       </tr>';
    }
    elsif($rs_keys){
       $tbl = $tbl . '<tr><td colspan="5">
       <b>Search Failed to Retrive any records on keywords: [<i>'. $rs_keys .'</i>] !</b></td>
       </tr>';
   }
    else{
	 $tbl = $tbl . '<tr><td colspan="5"><b>Database is New or  Empty!</b></td></tr>\n';
	 }
 }

 $tbl = $tbl . '<tr class="r0"><td colspan="6" align="right">

 <input type="hidden" name="datediff" id="datediff" value="0"/>
 <input type="submit" value="Date Diff Selected" onclick="return dateDiffSelected()"/>&nbsp;
 <input type="reset" value="Unselect All"/>
 <input type="submit" value="Delete Selected"/>
 </td></tr></form>
<tr class="r0"><form id="frm_srch" action="main.cgi"><td>Keywords:</td><td colspan="4">
<input name="keywords" type="text" size="60"/></td>
<td><input type="submit" value="Search"/></form></td></tr>
 </table>';

my  $frm = qq(<a name="top"></a>
 <form id="frm_log" action="main.cgi" onSubmit="return formValidation();">
	 <table class="tbl" border=0>
	 <tr class="r0"><td colspan="3"><b>* LOG ENTRY FORM *</b></td></tr>
	 <tr><td colspan="3"><br/></td></tr>
	 <tr>
	 <td>Date:</td><td id="al"><input id="ed" type="text" name="date" size="16" value=") .$today->ymd.
	 " ". $today->hms .
	 qq(">&nbsp;<button type="button" onclick="return setNow();">Now</button>
 	      &nbsp;<button type="reset">Reset</button>
	      </td>
	 	<td>Category:</td>
	 </tr>
		 <tr><td>Log:</td>
		  <td id="al"><textarea id="el" name="log" rows="2" cols="60"></textarea></td>
 		  <td>).$cats.qq(</td></tr>
		 <tr><td><a href="#bottom">&#x21A1;</a>&nbsp;Ammount:</td>
		 <td id="al">
		   <input id="am" name="am" type="number" step="any">
		   <button id="btn_srch" onclick="toggleSearch(this); return false;"i style="float: right;">Show Search</button>
		 </td>
		 <td><input type="submit" value="Submit"/>
		 </td>
	</tr></table>
	 <input type="hidden" name="submit_is_edit" id="submit_is_edit" value="0"/>
	 <input type="hidden" name="submit_is_view" id="submit_is_view" value="0"/>
	 <input type="hidden" name="rs_all" value="0"/>
	 <input type="hidden" name="rs_cur" value="0"/>
	 <input type="hidden" name="rs_prev" value=").$tbl_rc_prev.q("/> </form>
	 );


my  $srh = qq(
	 <form id="frm_srch" action="main.cgi">
	 <table class="tbl" border=0>
		 <tr class="r0"><td colspan="4"><b>Search/View By</b></td></tr>
	<tr><td>Keywords:</td><td colspan="2">
	<input name="keywords" type="text" size="60" value=").$rs_keys.qq("/></td>
	<td><input type="submit" value="Search"/></td></tr>);

my $ctmsg = '<p id="ctmsg">&nbsp;&nbsp;(Use the Category dropdown to change).</p>';
if($rs_keys || $rs_cat_idx || $stmD){
	$srh = $srh.'<tr><td colspan="2">
	<button onClick="resetView()">Reset Whole View</button></td><td colspan="3"></td></tr>';
	$ctmsg = "";
}



$srh = $srh.'<tr><td>View by Category:</td>
    <td colspan="3"><button id="btn_cat" onclick="viewByCategory(this);">Unspecified</button><input id="idx_cat" name="category" type="hidden" value="">'.$ctmsg.'</td></tr>
    <tr><td>View by (YYYY-MM-DD)<br>Date:</td>
    <td>From:&nbsp;<input name="v_from" type="text" size="10"/></td><td>To:&nbsp;<input name="v_to" type="text" size="10"/>
    <td><button id="btn_dat" onclick="viewByDate(this);">View</button></td>
    </tr>
    <tr><td colspan="4"><br></td></tr>
</table>
</form><br>';
#
#Page printout from here!
#
print "<center>";
	print "\n<div>\n" . $frm ."\n</div>\n<br/>";
	print '<div id="div_srh">' . $srh .'</div>';
	print "\n<div>\n" . $tbl ."\n</div>";
	print '<br><div><a href="stats.cgi">View Statistics</a></div>';
	print '<br><div><a href="config.cgi">Configure Log (Careful)</a><a name="bottom"/></div>';
print "</center>";


print $q->end_html;
$st->finish;
$db->disconnect();
exit;

### CGI END



sub buildNavigationButtons{

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

	$tbl = $tbl . '<tr class="r'.$tfId.'"><td><a href="#top">&#x219F;</a></td>';

	if($rs_prev && $rs_prev>0 && $tbl_start>0){

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

	$tbl = $tbl .'<td colspan="2"></td></tr>';
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
	       		   LOG='".$log."', AMMOUNT='".$amm."' WHERE rowid=".$edit_mode.";"; 
		my $st = $db->prepare($stm); 
			  $st->execute();
		return;
	}

	if($view_all && $view_all=="1"){
		$REC_LIMIT = 0;
	}

	if($view_mode && $view_mode == "1"){

		if($rs_cur){
			 $stmt = 'SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT from LOG 
			          where rowid <= "'.$rs_cur.'" ORDER BY DATE DESC;';
			 return;
		}
	}

	if($log && $date && $cat){

		#check for double entry
		#
		my $st = $db->prepare(
			  "SELECT DATE,LOG FROM LOG where DATE='".$date."' AND LOG='".$log."';"
			);

		$st->execute();
		if(my @row = $st->fetchrow_array()){
			return;
		}
		
		$st = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?)');
		$st->execute( $cat, $date, $log, $amm);
		#
		# After Insert renumeration check
		#
		my $dt = DateTime::Format::SQLite->parse_datetime($date);
		my $dtCur = DateTime->now();
		$dtCur->set_time_zone($TIME_ZONE);
		$dtCur = $dtCur - DateTime::Duration->new(days => 1);

		if($dtCur> $dt){
			print $q->p('<b>Insert is in the past!</b>');
			#Renumerate directly (not proper SQL but faster);
			$st = $db->prepare('select rowid from LOG ORDER BY DATE;');
			$st->execute();
			my @row = $st->fetchrow_array();
			my $cnt = 1;
 			while(my @row = $st->fetchrow_array()) {

			my $st_upd = $db->prepare("UPDATE LOG SET rowid=".$cnt.
						" WHERE rowid='".$row[0]."';");
				$st_upd->execute();
				$cnt = $cnt + 1;
			}
		}
	}
}
catch{
	print "ERROR:".$_;
}	
}



sub checkCreateTables(){

	$st = $db->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='LOG';");
	$st->execute();

	if(!$st->fetchrow_array()) {
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

				$st = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?)');

				$st->execute( 3, $today, "DB Created!",0);

				
	}

	$st = $db->prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='CAT';");
	$st->execute();
	if(!$st->fetchrow_array()) {
			        my $stmt = qq(

				CREATE TABLE CAT(
				  ID INT PRIMARY KEY NOT NULL,
				  NAME VCHAR(16),
				  DESCRIPTION VCHAR(64)
				);
							   
				);

				$rv = $db->do($stmt);

				if($rv < 0) {
					      print "<p>Error->"& $DBI::errstri &"</p>";
				} 

				$st = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');

		$st->execute(1,"Unspecified", "For quick uncategories entries.");
		$st->execute(3,"File System", "Operating file system short log.");
		$st->execute(6,"System Log", "Operating system inportant log.");
		$st->execute(9,"Event", "Event that occured, meeting, historical important.");
		$st->execute(28,"Personal", "Personal log of historical importants, diary type.");
		$st->execute(32, "Expense", "Significant yearly expense.");
		$st->execute(35, "Income", "Significant yearly income.");
		$st->execute(40, "Work", "Work related entry, worth monitoring.");
	}

}

