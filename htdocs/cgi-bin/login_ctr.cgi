#!/usr/bin/perl -w
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
package main;
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

#DEFAULT SETTINGS HERE!
our $REC_LIMIT   = 25;
our $TIME_ZONE   = 'Australia/Sydney';
our $LANGUAGE	   = 'English';
our $PRC_WIDTH   = '60';
our $LOG_PATH    = '../../dbLifeLog/';
our $SESSN_EXPR  = '+30m';
our $DATE_UNI    = '0';
our $RELEASE_VER = '1.3';
#END OF SETTINGS


my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>$LOG_PATH});
   $session->expire($SESSN_EXPR);
my $sid=$session->id();
my $cookie = $cgi->cookie(CGISESSID => $sid);


my $alias = $cgi->param('alias');
my $passw = $cgi->param('passw');
my $frm;


#This is the OS developer release key, replace on istallation. As it is not secure.
my $cipher_key = '95d7a85ba891da';

if($cgi->param('logout')){&logout}

if(&processSubmit==0){

  print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie);  
  print $cgi->start_html(-title => "Personal Log Login", -BGCOLOR=>"#c8fff8",
       		               -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		                     -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		    );	  

  $frm = qq(
	 <form id="frm_login" action="login_ctr.cgi" method="post"><table border="0" width="$PRC_WIDTH%">
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
		 <td colspan="3" style="border-left:1px solid black; border-right:1px solid black;"><font color="red">NOTICE!</font> &nbsp;
		 Alias will create a new database if it doesn't exist. Note down your password.		 
		 <input type="hidden" name="CGISESSID" value="$sid"/>
		 <input type="hidden" name="login" value="1"/></td></tr>
	  <tr class="r0"><td colspan="2"></td><td><input type="submit" value="Login"/></td></tr>
    </table></form>);

		print qq(<br><br><div id=rz>
						<center>
							<h2>Welcome to Life Log</h2><div>$frm</div><br/>
							<a href="https://github.com/wbudic/LifeLog" target="_blank">Get latest version of this application here!</a><br>
						</center><div>);
		print $cgi->end_html;

}
else{
	print $cgi->start_html;
	print $cgi->end_html;
}

exit;

sub processSubmit{
try{
	if($alias&&$passw){
 			
			$passw = uc crypt $passw, hex $cipher_key;
			&checkCreateTables;
			#ssion = CGI::Session->load();
			$session->param('alias', $alias);
			$session->param('passw', $passw);
			$session->param('database', 'data_'.$alias.'_log.db');	
			$session->flush();						
			print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie, -location=>"main.cgi");  
			return 1;
	}
	else{
		&removeOldSessions;
	}
return 0;
}
 catch{	 	
		print $cgi->header;
		print "<font color=red><b>SERVER ERROR</b></font> dump ->". $session->dump();
    print $cgi->end_html;
 }
}

sub checkCreateTables{
try{
	my $today = DateTime->now;
	   $today->set_time_zone( $TIME_ZONE );
	my $database = $LOG_PATH.'data_'.$alias.'_log.db';
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
		insertDefCats($db);
	}
	#Have cats been wiped out?
	$st = $db->prepare('SELECT count(ID) FROM CAT;');
	$st->execute();
	if($st->fetchrow_array()==0) {
		 insertDefCats($db);
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
		$st = $db->prepare("SELECT * FROM AUTH WHERE alias='$alias' AND passw='$passw';");
 		$st->execute();
		if(!$st->fetchrow_array()) {
	    $st = $db->prepare('INSERT INTO AUTH VALUES (?,?)');
	    $st->execute($alias, $passw);
		}
	}

 
	$st = $db->prepare(selSQLTbl('CONFIG'));
	$st->execute();
  if(!$st->fetchrow_array()) {
    my $stmt = qq(
										CREATE TABLE CONFIG(
												ID TINY PRIMARY KEY NOT NULL,
												NAME VCHAR(16),
												VALUE VCHAR(64)
										);
		);
		$rv = $db->do($stmt);
	}
  populateConfig($db);
	$db->disconnect();
}
 catch{	 	
	  print $cgi->header;
		print "<font color=red><b>SERVER ERROR</b></font>:".$_;
    print $cgi->end_html;
		exit;
 }
}
sub populateConfig{

		open(my $fh, '<', './main.cnf' ) or die "Can't open main.cnf: $!";
		my $db = shift;
		my ($did,$name, $value);

		my $st = $db->prepare("SELECT count(*) FROM CONFIG;");
		   $st->execute();
		my $cnt = $st->fetchrow_array();
		if($cnt != 0){
			 return;
		}
try{		
    while (my $line = <$fh>) {
					chomp $line;				
					my %hsh = $line =~ m[(\S+)\s*=\s*(\S+)]g;
					for my $key (keys %hsh) {
								my %nash = $key =~ m[(\S+)\s*\|\$\s*(\S+)]g;									
								
						for my $id (keys %nash) {
							    $did = $id;
								  $name  = $nash{$id};
								  $value = $hsh{$key};
						 	 my $st = $db->prepare("SELECT * FROM CONFIG WHERE NAME LIKE '$name';");
									$st->execute();								
							 if(!$st->fetchrow_array()){
									#TODO Check if script id is unique to database? If not script prevails to database entry. 
									#if user setting from previous release, must be migrated later.
									$st = $db->prepare('INSERT INTO CONFIG VALUES (?,?,?)');
									$did = $id;
									$st->execute($id, $name,$value);                  
								}
							}
					}
		}      
    
    close $fh;	
 } catch{	 	
	  close $fh;	
	  print $cgi->header;
		print "<font color=red><b>SERVER ERROR</b></font> [$did, $name,$value]:".$_;
    print $cgi->end_html;
		exit;
 }
}

sub selSQLTbl{
	  my $name = $_[0];
return "SELECT name FROM sqlite_master WHERE type='table' AND name='$name';"
}

sub insertDefCats{
	  my
	  $st = $_[0]->prepare('INSERT INTO CAT VALUES (?,?,?)'); 
		$st->execute(1,"Unspecified", "For quick uncategorised entries.");
		$st->execute(3,"File System", "Operating file system short log.");
		$st->execute(6,"System Log", "Operating system important log.");
		$st->execute(9,"Event", "Event that occured, meeting, historically important.");
		$st->execute(28,"Personal", "Personal log of historical importants, diary type.");
		$st->execute(32, "Expense", "Significant yearly expense.");
		$st->execute(35, "Income", "Significant yearly income.");
		$st->execute(40, "Work", "Work related entry, worth monitoring.");
		$st->execute(45, "Food", "Quick reference to recepies, observations.");
		$st->finish();
}


sub removeOldSessions{
	opendir(DIR, $LOG_PATH);
	my @files = grep(/cgisess_*/,readdir(DIR));
	closedir(DIR);
	my $now = time - (24 * 60 * 60);
	foreach my $file (@files) {
		my $mod = (stat("$LOG_PATH/$file"))[9];
		if($mod<$now){
		    unlink "$LOG_PATH/$file";
		}
	}
}

sub logout{

	$session->delete();
	$session->flush();
	print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie);
	print $cgi->start_html(-title => "Personal Log Login", -BGCOLOR=>"black", 
		                     -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		    );	
	
	print qq(<font color="white"><center><h2>You have properly loged out of the Life Log Application!</h2>
	<br>
	<form action="login_ctr.cgi"><input type="submit" value="No, no, NO! Log me In Again."/></form><br>
	</br>
	<iframe width="60%" height="600px" src="https://www.youtube.com/embed/HQ5SEieVbSI?autoplay=1" 
	  frameborder="0" 
		allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
	</iframe>
	</center></font>
	);	

	print $cgi->end_html;
	exit;
}

### CGI END
