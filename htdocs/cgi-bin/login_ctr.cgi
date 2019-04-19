#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Try::Tiny; 
use CGI;
use CGI::Session '-ip_match';
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Text::CSV;
use Crypt::CBC;
use Crypt::IDEA;


#DEFAULT SETTINGS HERE!
our $REC_LIMIT = 25;
our $TIME_ZONE = 'Australia/Sydney';
our $PRC_WIDTH = '60';
#END OF DEFAULT SETTINGS

my $cgi = CGI->new;
my $session = new CGI::Session(undef,$cgi);
#dev session setting change to +1h, hard coded for now. - WB
$session->expire('+2m');
my $sid=$session->id();
my $cookie = $cgi->cookie(CGISESSID => $sid);

my $alias = $cgi->param('alias');
my $passw = $cgi->param('passw');
if(!$alias){$alias=""};
if(!$passw){$passw=""}

#This is the OS developer release key and cipher, replace on istallation. As it is not secure.
my $cipher_key = '95d7a85ba891da896d0d87aca6d742d5';
my $cipher = new Crypt::CBC({key => $cipher_key, cipher => 'IDEA'});


if(&processSubmit){

}else{

print $cgi->header(-expires=>"+6os", -charset=>"UTF-8", -cookie=>$cookie);    
print $cgi->start_html(-title => "Personal Log Login", 
       		           -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		               -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		    );	  
my  $frm = qq(
	 <form id="frm_login" action="login_ctr.cgi"><table border="0" width="$PRC_WIDTH%">
	        <tr class="r0">
		 <td colspan="3"><center>LOGIN</center></td>
		</tr>
	        <tr class="r1" style="border-left:1px solid black; border-right:1px solid black;">
		 <td align="right">Alias:</td><td><input type="text" name="alias" value="$alias"/></td><td></td>
		</tr>
	        <tr class="r1" style="border-left:1px solid black; border-right:1px solid black;">
		 <td align="right">Password:</td><td><input type="text" name="passw" value="$passw"/></td><td></td>
		</tr>
		<tr class="r1">
		<td colspan="3" style="border-left:1px solid black; border-right:1px solid black;"><font color="red">NOTICE!</font> &nbsp;If here the first time? Write down your alias and password, before proceeding. So you can comeback in the future to continue. Only you can know it.
		<input type="hidden" name="CGISESSID" value="$sid"/>
		<input type="hidden" name="login" value="1"/></td></tr>
	    <tr class="r0"><td colspan="2"></td><td><input type="submit" value="Login"/></td></tr>
</table></form>);
	 

print "<center>";
	print "\n<div>\n" . $frm ."\n</div>\n<br/>";
print "</center>";
}


print $cgi->end_html;
exit;

sub processSubmit{
	if($alias&&$passw){
 			$passw = $cipher->encrypt_hex($passw);
			&checkCreateTables;
			$session = CGI::Session->load();
			$session->param('alias', $alias);
			$session->param('passw', $passw);
			$session->param('database', 'data_'.$alias.'_log.db');
			$session->param('cipher', $cipher_key);
			$session->save_param($cgi);
			print $cgi->redirect('main.cgi');
	
			return 1;
	}
return 0;
}

sub checkCreateTables{
try{
	my $today = DateTime->now;
	   $today->set_time_zone( $TIME_ZONE );
	my $database = '../../dbLifeLog/'.'data_'.$alias.'_log.db';
	my $dsn= "DBI:SQLite:dbname=$database";
	my $db = DBI->connect($dsn, $alias, $passw, { RaiseError => 1 }) 
		      or die "<p>Error->"& $DBI::errstri &"</p>";
  my $rv;
	my $st = $db->prepare(selSQLTbl('LOG'));
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
		if($rv < 0){print "<p>Error->"& $DBI::errstri &"</p>";}
		
		$st = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?)');
		$st->execute( 3, $today, "DB Created!",0);
  }
	$st = $db->prepare(selSQLTbl('CAT'));
	$st->execute();
	if(!$st->fetchrow_array()) {
		 my $stmt = qq(
		 CREATE TABLE CAT(
			 ID TINY PRIMARY KEY NOT NULL,
			 NAME VCHAR(16),
			 DESCRIPTION VCHAR(64)
		 );
		 ); 
		$rv = $db->do($stmt);

		$st = $db->prepare('INSERT INTO CAT VALUES (?,?,?)'); 
		$st->execute(1,"Unspecified", "For quick uncategories entries.");
		$st->execute(3,"File System", "Operating file system short log.");
		$st->execute(6,"System Log", "Operating system inportant log.");
		$st->execute(9,"Event", "Event that occured, meeting, historical important.");
		$st->execute(28,"Personal", "Personal log of historical importants, diary type.");
		$st->execute(32, "Expense", "Significant yearly expense.");
		$st->execute(35, "Income", "Significant yearly income.");
		$st->execute(40, "Work", "Work related entry, worth monitoring.");
		$st->execute(45, "Food", "Quick reference to recepies, observations.");
	}
  $st = $db->prepare(selSQLTbl('AUTH'));
	$st->execute();
	if(!$st->fetchrow_array()) {
    my $stmt = qq(
		CREATE TABLE AUTH(
				alias TEXT PRIMARY KEY,
				passw TEXT				  
		) WITHOUT ROWID;
		); 
		$rv = $db->do($stmt);
		if($rv < 0){print "<p>Error->"& $DBI::errstri &"</p>"};

	}

  $st = $db->prepare("SELECT * FROM AUTH WHERE alias='$alias' AND passw='$passw';");
	$st->execute();
	if(!$st->fetchrow_array()) {
	    $st = $db->prepare('INSERT INTO AUTH VALUES (?,?)');
	    $st->execute($alias, $passw);
	}

	$st = $db->prepare(selSQLTbl('CONFIG'));
	$st->execute();
  if(!$st->fetchrow_array()) {
    my $stmt = qq(
		CREATE TABLE CONFIG(
 		    ID INT PRIMARY KEY NOT NULL,
				NAME VCHAR(16),
				VALUE VCHAR(64)
		);
		);
		$rv = $db->do($stmt);

		$st = $db->prepare('INSERT INTO CONFIG VALUES (?,?)');
		$st->execute("REC_LIMIT", $REC_LIMIT);
		$st->execute("TIME_ZONE", $TIME_ZONE);
		$st->execute("PRC_WIDTH", $PRC_WIDTH);
	}
}
 catch{
		print "<font color=red><b>SERVER ERROR</b></font>:".$_;
 }
}

sub selSQLTbl{
	  my $name = @_;
return "SELECT name FROM sqlite_master WHERE type='table' AND name='$name';"
}

### CGI END


