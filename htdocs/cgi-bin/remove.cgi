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

use DateTime qw();
use DateTime::Format::SQLite;
use DateTime::Format::Human::Duration;


#DEFAULT SETTINGS HERE!
our $REC_LIMIT   = 25;
our $TIME_ZONE   = 'Australia/Sydney';
our $PRC_WIDTH   = '60';
our $LOG_PATH    = '../../dbLifeLog/';
our $SESSN_EXPR  = '+2m';
our $RELEASE_VER = '1.3';
#END OF SETTINGS


#####################
	&getConfiguration;
#####################

my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>$LOG_PATH});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');

if(!$userid||!$dbname){
	print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
	exit;
}

my $database = '../../dbLifeLog/'.$dbname;
my $dsn= "DBI:SQLite:dbname=$database";
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) or die "<p>Error->"& $DBI::errstri &"</p>";

my $today = DateTime->now;
   $today->set_time_zone( $TIME_ZONE );

my $stm;
my $stmtCat = "SELECT ID, NAME FROM CAT;";
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
		   <table class="tbl_rem" width="'.$PRC_WIDTH.'%">
		   <tr class="hdr" style="text-align:left;"><th>Date</th> <th>Time</th><th>Log</th><th>Category</th></tr>';


my $datediff = $cgi->param("datediff");
my $confirmed = $cgi->param('confirmed');
if ($datediff){
	     print $cgi->header(-expires=>"+6os");    
	     print $cgi->start_html(-title => "Date Difference Report", 
			     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
			     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

		);	  
		&DisplayDateDiffs;
}elsif (!$confirmed){
	     print $cgi->header(-expires=>"+6os");    
	     print $cgi->start_html(-title => "Personal Log Record Removal", 
			     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
			     -style =>{-type => 'text/css', -src => 'wsrc/main.css'}

		);	  

		&NotConfirmed;
}else{
		&ConfirmedDelition;
}


print $cgi->end_html;
$db->disconnect();
exit;

sub DisplayDateDiffs{
    $tbl = '<table class="tbl" width="'.$PRC_WIDTH.'%">
	    <tr class="r0"><td colspan="2"><b>* DATE DIFFERENCES *</b></td></tr>';

    $stm = 'SELECT DATE, LOG FROM LOG WHERE '; 
    my  @prms = $cgi->param('chk');

	foreach (@prms){
		$stm .= "rowid = '" . $_ ."'";
		if(  \$_ != \$prms[-1]  ) {
			$stm = $stm." OR ";
		}
	}
	$stm .= ';';
	$st = $db->prepare( $stm );
	$st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

	my $dt_prev = $today;
	while(my @row = $st->fetchrow_array()) {

		 my $dt = DateTime::Format::SQLite->parse_datetime( $row[0] );
		 my $dif = dateDiff($dt_prev, $dt);
		 $tbl .= '<tr class="r1"><td>'. $dt->ymd . '</td> 
			        </td><td style="text-align:left;">'.$row[1]."</td></tr>".
		         '<tr class="r0"><td colspan="2">'.$dif. '</td> </tr>';	
		$dt_prev = $dt;
	}
    $tbl .= '</table>';

print '<center><div>'.$tbl.'</div><br><div><a href="main.cgi">Back to Main Log</a></div></center>';
}


sub dateDiff{
	my($d1,$d2)=@_;
	my $span = DateTime::Format::Human::Duration->new();
	my $dur = $span->format_duration($d2 - $d1);
return sprintf( "%s <br>between %s and %s", $dur, boldDate($d1), boldDate($d2));

}

sub boldDate{
	my($d)=@_;
return "<b>".$d->ymd."</b> ".$d->hms;
}


sub ConfirmedDelition{

	my $stmS = 'DELETE FROM LOG WHERE '; 

	foreach my $prm ($cgi->param('chk')){
		$stm = qq(DELETE FROM LOG WHERE rowid = '$prm';);
	    $st = $db->prepare( $stm );
		$rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
		$stm = qq(DELETE FROM NOTES WHERE LID = '$prm';);
		$rv = $st->execute();

		if($rv < 0) {
		     print "<p>Error->"& $DBI::errstri &"</p>";
			 exit;
		}
		
	}
	
	
	$st->finish;

	print $cgi->redirect('main.cgi');

}

sub NotConfirmed{

#Get prms and build confirm table and check
my $stm = $stmS ." ";
	foreach my $prm ($cgi->param('chk')){
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
my $rs = "r1";
while(my @row = $st->fetchrow_array()) {

	 my $ct = $hshCats{$row[1]};
	 my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );
	 
	 $tbl = $tbl . '<tr class="r1"><td class="'.$rs.'">'. $dt->ymd . "</td>" . 
		  '<td class="'.$rs.'">' . $dt->hms . "</td>" .
		  '<td class="'.$rs.'" style="font-weight:bold; color:maroon;">' . $row[3] . "</td>\n".
		  '<td class="'.$rs.'">' . $ct. '<input type="hidden" name="chk" value="'.$row[0].'"></td></tr>';
	if($rs eq "r1"){
	   $rs = "r0";
	}
	else{
		$rs = "r1";
	}
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

sub getConfiguration{
	try{
		my $dbs = $db->prepare("SELECT * FROM CONFIG;");
		$dbs->execute();

		while (my @r=$dbs->fetchrow_array()){
			
			switch ($r[1]) {

				case "REC_LIMIT" {$REC_LIMIT=$r[2]}
				case "TIME_ZONE" {$TIME_ZONE=$r[2]}
				case "PRC_WIDTH" {$PRC_WIDTH=$r[2]}		
				case "SESSN_EXPR" {$SESSN_EXPR=$r[2]}
				else {print "Unknow variable setting: ".$r[1]. " == ". $r[2]}

			}

		}
	}
	catch{
		print "<font color=red><b>SERVER ERROR</b></font>:".$_;
	}
}