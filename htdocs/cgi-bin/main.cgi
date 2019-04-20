#!/usr/bin/perl
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
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Date::Parse;
use Time::localtime;
use Regexp::Common qw /URI/;

#DEFAULT SETTINGS HERE!
our $REC_LIMIT   = 25;
our $TIME_ZONE   = 'Australia/Sydney';
our $PRC_WIDTH   = '60';
our $LOG_PATH    = '../../dbLifeLog/';
our $SESSN_EXPR  = '+2m';
our $RELEASE_VER = '1.3';
#END OF SETTINGS

my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>$LOG_PATH});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');
$session->expire('+2m');


if(!$userid||!$dbname){
	print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
	exit;
}

my $database = '../../dbLifeLog/'.$dbname;
my $dsn= "DBI:SQLite:dbname=$database";
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) or die "<p>Error->"& $DBI::errstri &"</p>";

### Authenticate session to alias password
&authenticate;
&getConfiguration($db);

my $tbl_rc = 0;
my $tbl_rc_prev = 0;
my $tbl_cur_id;
my $rs_keys = $cgi->param('keywords');
my $rs_cat_idx = $cgi->param('category');
my $rs_dat_from = $cgi->param('v_from');
my $rs_dat_to = $cgi->param('v_to');
my $rs_prev = $cgi->param('rs_prev'); 
my $rs_cur = $cgi->param('rs_cur');
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

$session->expire($SESSN_EXPR);
	
print $cgi->header(-expires=>"0s", -charset=>"UTF-8"); 
print $cgi->start_html(-title => "Personal Log", 
       		     			   -script=>{-type => 'text/javascript',-src => 'wsrc/main.js'},
		     						   -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		     						   -onload => "loadedBody('".$toggle."');"
		        );	  
my $rv;
my $st;
my $today = DateTime->now;
   $today->set_time_zone( $TIME_ZONE );


my $stmtCat = "SELECT * FROM CAT;";
my $stmt    = "SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT FROM LOG ORDER BY rowid DESC, DATE DESC;";


$st = $db->prepare( $stmtCat );
$rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

my $cats = '<select id="ec" name="cat" onChange="updateSelCategory(this)"><option value="0">---</option>\n';
my %hshCats;
my $c_sel = 1;
 while(my @row = $st->fetchrow_array()) {
	if($row[0]==$c_sel){
		$cats = $cats. '<option selected value="'.$row[0].'">'.$row[1].'</option>\n';
	}
	else{	
		$cats = $cats. '<option value="'.$row[0].'">'.$row[1].'</option>\n';
	}	
	$hshCats{$row[0]} = $row[1];
 }

$cats = $cats.'</select>';


my $tbl = qq(<form id="frm_log" action="remove.cgi" onSubmit="return formDelValidation();">
<table class="tbl" border="0" width="$PRC_WIDTH%">
<tr class="r0">
	<th style="border-right: solid 1px;">Date</th><th style="border-right:solid 1px;">Time</th><th>Log</th><th>#</th><th>Category</th><th>Edit</th>
</tr>);


if($rs_keys){
	
	my @keywords = split / /, $rs_keys;
	if($rs_cat_idx){
		$stmS = $stmS ." ID_CAT='".$rs_cat_idx."' AND";
	}else{
		$stmS = $stmS ." ID_CAT='0' OR";
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
 #print $cgi->pre("### -> ".$stmt);


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
#
#Fetch entries!
#
$st = $db->prepare( $stmt );
$rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
if($rv < 0) {
	     print "<p>Error->"& $DBI::errstri &"</p>";
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
	 $log = join('' , @chnks);
	 #Decode escaped \\n
	 $log =~ s/\\n/<br>/gs;
	


         $tbl .= '<tr class="r'.$tfId.'">
	          <td id="y'.$id.'" width="10%" style="border-right: solid 1px;">'. $dt->ymd . "</td>\n". 
		          '<td id="t'.$id.'" width="10%" style="border-right: solid 1px;">' .
			                                                            $dt->hms . "</td>\n".
			  '<td id="v'.$id.'" width="50%" class="log">' . $log . "</td>\n".
			  '<td id="a'.$id.'" width="20%">' . $amm ."</td>\n".
			  '<td id="c'.$id.'" width="10%">' . $ct ."</td>\n".
			  '<td width="10%">
  			    <input class="edit" type="button" value="Edit" onclick="return edit('.$id.');"/>
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
       <b>Search Failed to Retrive any records on select: [<i>'. $stmD .'</i>] !</b></td></tr>';
    }
    elsif($rs_keys){
	    my $criter = "";
	    if($rs_cat_idx>0){
		$criter = "->Criteria[".$hshCats{$rs_cat_idx}."]";
	    }
       $tbl = $tbl . '<tr><td colspan="5">
       <b>Search Failed to Retrive any records on keywords: [<i>'. $rs_keys .'</i>]'.$criter.' !</b></td>
       </tr>';
   }
    else{
	 $tbl = $tbl . '<tr><td colspan="5"><b>Database is New or  Empty!</b></td></tr>\n';
	 }
 }

 $tbl .= '<tr class="r0"><td><a href="#top">&#x219F;</a></td><td colspan="5" align="right"> 
 <input type="hidden" name="datediff" id="datediff" value="0"/>
 <input type="submit" value="Date Diff Selected" onclick="return dateDiffSelected()"/>&nbsp;
 <input type="button" value="Select All" onclick="return selectAllLogs()"/>
 <input type="reset" value="Unselect All"/>
 <input type="submit" value="Delete Selected"/>
 </td></tr></form>
<tr class="r0"><form id="frm_srch" action="main.cgi"><td><b>Keywords:</b></td><td colspan="4" align="left">
<input name="keywords" type="text" size="60"/></td>
<td><input type="submit" value="Search"/></form></td></tr>
 </table>';

 my $frm = qq(<a name="top"></a>
 <form id="frm_entry" action="main.cgi" onSubmit="return formValidation();">
	 <table class="tbl" border="0" width="$PRC_WIDTH%">
	 <tr class="r0"><td colspan="3"><b>* LOG ENTRY FORM *</b></td></tr>
	 <tr><td colspan="3"><br/></td></tr>
	 <tr>
	 <td>Date:</td><td id="al"><input id="ed" type="text" name="date" size="16" value=") .$today->ymd.
	 " ". $today->hms .
	 qq(">&nbsp;<button type="button" onclick="return setNow();">Now</button>
 	      &nbsp;<button type="reset">Reset</button>
	      </td>
	 	<td></td>
	 </tr>
		 <tr><td>Log:</td>
		  <td id="al"><textarea id="el" name="log" rows="2" cols="60"></textarea></td>
 		  <td>Category:&nbsp;$cats</td></tr>
		 <tr><td><a href="#bottom">&#x21A1;</a>&nbsp;Ammount:</td>
		 <td id="al">
		   <input id="am" name="am" type="number" step="any">
		   <button id="btn_srch" onclick="toggleSearch(this); return false;"
		           style="float: right;">Show Search</button>
		 </td>
		 <td align="right"><input id="log_submit" type="submit" value="Submit"/>
		 </td>
	</tr></table>
	 <input type="hidden" name="submit_is_edit" id="submit_is_edit" value="0"/>
	 <input type="hidden" name="submit_is_view" id="submit_is_view" value="0"/>
	 <input type="hidden" name="rs_all" value="0"/>
	 <input type="hidden" name="rs_cur" value="0"/>
	 <input type="hidden" name="rs_prev" value="$tbl_rc_prev"/>
	 <input type="hidden" name="CGISESSID" value="$sid"/>
	 </form>
	 );


my  $srh = qq(
	 <form id="frm_srch" action="main.cgi">
	 <table class="tbl" border="0" width="$PRC_WIDTH%">
           <tr class="r0"><td colspan="4"><b>Search/View By</b></td></tr>
	   );

$cats =~ s/selected//g;
$srh .= qq(<tr><td align="right"><b>View by Category:</b></td><td>.$cats.</td><td></td>
    <td colspan="1" align="left">
    <button id="btn_cat" onclick="viewByCategory(this);" style="float:left">View</button>
    <input id="idx_cat" name="category" type="hidden" value="0"></td></tr>
    <tr><td align="right"><b>View by Date:</b></td>
    <td align="left">
    From:&nbsp;<input name="v_from" type="text" size="16"/></td><td align="left">
    To:&nbsp;<input name="v_to" type="text" size="16"/>
    <td align="left"><button id="btn_dat" onclick="viewByDate(this);">View</button></td>
    </tr>
    <tr><td align="right"><b>Keywords:</b></td>
         <td colspan="2" align="left">
       	 	 <input id="rs_keys" name="keywords" type="text" size="60" value="$rs_keys"/></td>
         <td align="left"><input type="submit" value="Search" align="left"></td></tr>);

if($rs_keys || $rs_cat_idx || $stmD){
	$srh .= '<tr><td align="left" colspan="3">
	<button onClick="resetView()">Reset Whole View</button></td></tr>';
}
	       
#$srh .='<tr><td colspan="4"><br></td></tr>
$srh.='</table></form><br>';
#
#Page printout from here!
#
print "<center>";
	print "\n<div>\n" . $frm ."\n</div>\n<br>\n";
	print '<div id="div_srh">' . $srh .'</div>';
	print "\n<div>\n" . $tbl ."\n</div>";
	print '<br><div><a href="stats.cgi">View Statistics</a></div>';
	print '<br><div><a href="config.cgi">Configure Log (Careful)</a><a name="bottom"/></div>';
print "</center>";

print $cgi->end_html;
$st->finish;
$db->disconnect();
undef($session);
exit;

### CGI END




sub processSubmit { 


	my $date = $cgi->param('date');
	my $log = $cgi->param('log');
	my $cat = $cgi->param('cat');
	my $amm = $cgi->param('am');

	my $edit_mode =  $cgi->param('submit_is_edit');
	my $view_mode =  $cgi->param('submit_is_view');
	my $view_all  =  $cgi->param('rs_all');

	
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
			print $cgi->p('<b>Insert is in the past!</b>');
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

	$tbl .=  qq!<tr class="r$tfId"><td></td>!;

	if($rs_prev && $rs_prev>0 && $tbl_start>0){

	 $tbl = $tbl . qq!<td><input type="hidden" value="$rs_prev"/>
	 <input type="button" onclick="submitPrev($rs_prev);return false;"
	  value="&lsaquo;&lsaquo;&ndash; Previous"/></td>!;

	}
	else{
                $tbl .= '<td><i>Top</i></td>';
	}


	$tbl .= '<td colspan="1"><input type="button" onclick="viewAll();return false;" value="View All"/></td>';

	if($is_end_of_rs == 1){
	  $tbl = $tbl .'<td><i>End</i></td>';
	}
	else{

	  $tbl .= qq!<td><input type="button" onclick="submitNext($tbl_cur_id);return false;"
		                      value="Next &ndash;&rsaquo;&rsaquo;"/></td>!;

	}

	$tbl = $tbl .'<td colspan="2"></td></tr>';
}

sub getConfiguration{
		my $st = $_[0]->prepare("SELECT * FROM CONFIG;");
		   $st->execute(); 
		while (my @r=$st->fetchrow_array()){
			
			switch ($r[1]) {

				case "REC_LIMIT" {$REC_LIMIT=$r[2]}
				case "TIME_ZONE" {$TIME_ZONE=$r[2]}
				case "PRC_WIDTH" {$PRC_WIDTH=$r[2]}
				else {print "Unknow variable setting: ".$r[1]. " == ". $r[2]}

			}

		}
}


sub authenticate{
try  {

	 my	$ct = ctime(stat($database));
	 if($ct < str2time("20 Apr 2019")){
		 return;
	 }


	 my $st =$db->prepare("SELECT * FROM AUTH WHERE alias='$userid' and passw='$password';");
			$st->execute();
	 if($st->fetchrow_array()){return;}
	 
	 print $cgi->header(-expires=>"+0s", -charset=>"UTF-8");    
   print $cgi->start_html(-title => "Personal Log Login", 
       		              -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		                    -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		         );	  
	 
	 print $cgi->center($cgi->div("<b>Access Denied!</b> Invalid password! alias:$userid pass:$password"));
	 print $cgi->end_html;
	 
	$db->disconnect();
	$session->flush();
	exit;

} catch{
					print $cgi->header(-expires=>"+0s", -charset=>"UTF-8"); 
					print $cgi->p("ERROR:".$_);
					print $cgi->end_html;
					exit;
}
}