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
our $PRC_WIDTH   = '70';
our $LOG_PATH    = '../../dbLifeLog/';
our $SESSN_EXPR  = '+30m';
our $DATE_UNI    = '0';
our $RELEASE_VER = '1.4';
our $AUTHORITY   = '';
our $IMG_W_H     = '210x120';
our $AUTO_WRD_LMT= 200;
our $AUTO_LOGIN  = 0;
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

&checkAutologinSet;
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
		 <td align="right">Password:</td><td><input type="password" name="passw" value="$passw"/></td><td></td>
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

sub checkAutologinSet {
try{
		#We don't need to slurp as it is expected setting in header.
		my @cre;
		open(my $fh, '<', $LOG_PATH.'main.cnf' ) or die "Can't open main.cnf: $!";		
		while (my $line = <$fh>) {
					chomp $line;
					if(rindex ($line, "<<AUTO_LOGIN<", 0)==0){
						 my $end = index $line, ">", 14;
						 my $crest = substr $line, 13, $end - 13;
						 @cre = split '/', $crest;
						 last;
					}
		}
    close $fh;
		if(@cre &&scalar(@cre)>1){			
			 my $database = $LOG_PATH.'data_'.$cre[0].'_log.db';
			 my $dsn= "DBI:SQLite:dbname=$database";
			 my $db = DBI->connect($dsn, $cre[0], $cre[1], { RaiseError => 1 }) 
								or die "<p>Error->"& $DBI::errstri &"</p>";
					#check if enabled.	
			 my $st = $db->prepare("SELECT VALUE FROM CONFIG WHERE NAME='AUTO_LOGIN';");
		 			$st->execute();
			 my @set = $st->fetchrow_array();
					if(@set && $set[0]=="1"){
						 $alias = $cre[0];
						 $passw = $cre[1];						 
					}
			 $db->disconnect();
		}
}
 catch{	 	
	  print $cgi->header;
		print "<font color=red><b>SERVER ERROR</b></font>:".$_;
    print $cgi->end_html;
		exit;
 }
}

sub checkCreateTables {
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

	my $changed = 0;

	if(!$st->fetchrow_array()) {
		my $stmt = qq(
		CREATE TABLE LOG (
			 ID_CAT TINY NOT NULL,
			 DATE DATETIME  NOT NULL,
			 LOG VCHAR(128) NOT NULL,
			 AMMOUNT INTEGER DEFAULT 0
		);
		CREATE INDEX idx_log_dates ON LOG (DATE);
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
						CREATE INDEX idx_cat_name ON CAT (NAME);
		 ); 
		$rv = $db->do($stmt);
		$changed = 1;
		#insertDefCats($db);
	}
	#Have cats been wiped out?
	$st = $db->prepare('SELECT count(ID) FROM CAT;');
	$st->execute();
	if($st->fetchrow_array()==0) {
		 $changed = 1;
	}

  $st = $db->prepare(selSQLTbl('AUTH'));
	$st->execute();
	if(!$st->fetchrow_array()) {
	#
	# @TODO
	# AUTH Action Flags 
	# 00|DEFAULT`No action idle use.|
	# 02|CONF_UPD`Configuration file update with db.
	# 03|EMAIL`Issue email.|
  # 06|DESTRUCT`Self destruct, remove alias and all data.
  # 08|CHNG_PASS`Change password.	
	# 10|CHNG_ALIAS`Change alias.	
	
    my $stmt = qq(
		CREATE TABLE AUTH(
				alias varchar(20) TEXT PRIMARY KEY,
				passw TEXT,
				email varchar(44),
				action TINY,				  
		) WITHOUT ROWID;
		CREATE INDEX idx_auth_name_passw ON AUTH (ALIAS, PASSW);
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
	#
	#TODO Future table.
	#
	$st = $db->prepare(selSQLTbl('NOTES'));
	$st->execute();
	if(!$st->fetchrow_array()) {
my $stmt = qq(
										CREATE VIRTUAL TABLE NOTES USING fts4(
												ID INT PRIMARY KEY NOT NULL,
												ID_LOG INT,
												AUTHOR,
												CONTENT TEXT NOT NULL,
												compress=zip, uncompress=unzip
										);
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
		#v.1.3 -> v.1.4
		#alter table CONFIG add DESCRIPTION VCHAR(128);

    my $stmt = qq(
										CREATE TABLE CONFIG(
												ID TINY PRIMARY KEY NOT NULL,
												NAME VCHAR(16),
												VALUE VCHAR(28),
												DESCRIPTION VCHAR(128)
										);
										CREATE INDEX idx_config_name ON CONFIG (NAME);
		);
		$rv = $db->do($stmt);
		$st->finish();
		$changed = 1;
	}
	else{
				#PRAGMA table_info(CONFIG); <-To check current structure
				#populateConfig($db);

				#Has configuration been wiped out?
				$st = $db->prepare('SELECT count(ID) FROM CONFIG;');
				$st->execute();
				$changed = 1 if($st->fetchrow_array()==0);
				
	}
	#
	 &populate($db) if $changed;
	#
	$db->disconnect();
}
 catch{	 	
	  print $cgi->header;
		print "<font color=red><b>SERVER ERROR</b></font>:".$_;
    print $cgi->end_html;
		exit;
 }
}

sub populate {

		
		my $db = shift;
		my ($did,$name, $value, $desc);
		my $inData = 0;
		my $err = "";
		my %vars = ();
		my @lines;
		my $table_type = 0;

		open(my $fh, "<:perlio", $LOG_PATH.'main.cnf' ) or die "Can't open main.cnf: $!";
		read $fh, my $content, -s $fh;
	  	   @lines  = split '\n', $content;
	  close $fh;
#TODO Check if script id is unique to database? If not script prevails to database entry. 
#So, if user settings from a previous release, must be migrated later.
try{
	  
		my $insConfig = $db->prepare('INSERT INTO CONFIG VALUES (?,?,?,?)');
		my $insCat    = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
						$db->begin_work();
    foreach my $line (@lines) {
					
					my @tick = split("`",$line);

 					if( index( $line, '<<CONFIG<' ) == 0 ){$table_type = 0; $inData = 0;}
					if( index( $line, '<<CAT<' ) == 0 )   {$table_type = 1; $inData = 0;}
					if( index( $line, '<<LOG<' ) == 0 )   {$table_type = 2; $inData = 0;}
					if( scalar @tick  == 2 ) {

						my %hsh = $tick[0] =~ m[(\S+)\s*=\s*(\S+)]g;
									if ( scalar %hsh ) {
											for my $key ( keys %hsh ) {
														my %nash = $key =~ m[(\S+)\s*\|\$\s*(\S+)]g;
														if ( scalar(%nash) ) {
																for my $id ( keys %nash ) {
																	my $name  = $nash{$id};
																	my $value = $hsh{$key};
																	if($vars{$id}){
$err .= "UID{$id} taken by $vars{$id}-> $line\n";
																	}
																	else{
																			my $st = $db->prepare("SELECT rowid FROM CONFIG WHERE NAME LIKE '$name';");
																				$st->execute();
																				$inData = 1;
																				if(!$st->fetchrow_array()) {
																					  $insConfig->execute($id,$name,$value,$tick[1])	if(!$st->fetchrow_array());
																				}
																	}
																}
														}else{
$err .= "Invalid, spec'ed {uid}|{variable}`{description}-> $line\n";
														}

												}#rof
									}
									elsif($table_type==0){
														$err .= "Invalid, speced entry -> $line\n";
									}elsif($table_type==1){
															my @pair = $tick[0] =~ m[(\S+)\s*\|\s*(\S+)]g;
															if ( scalar(@pair)==2 ) {												
																	my $st = $db->prepare("SELECT rowid FROM CONFIG WHERE NAME LIKE '$pair[1]';");
																		$st->execute();
																		$inData = 1;
																		if(!$st->fetchrow_array()) {
																			$insCat->execute($pair[0],$pair[1],$tick[1]) if(!$st->fetchrow_array());
																		}
															}
															else {
$err .= "Invalid, spec'ed {uid}|{category}`{description}-> $line\n";
															}
									}elsif($table_type==2){
											#TODO Do we really want this?
									}											
					}elsif($inData && length($line)>0){

										if(scalar(@tick)==1){
											$err .= "Corrupt Entry, no description supplied -> $line\n";
										}
										else{	
											$err .= "Corrupt Entry -> $line\n";
										}

					}
		}    
		die "Configuration script $LOG_PATH.'main.cnf' [$fh] contains errors." if $err;
		$db->commit();
	} catch{	 		
	  print $cgi->header;
	  print "<font color=red><b>SERVER ERROR!</b></font><br> ".$_."<br><pre>$err</pre>";
	  print $cgi->end_html;
		exit;
 }
}

sub selSQLTbl{
	  my $name = $_[0];
return "SELECT name FROM sqlite_master WHERE type='table' AND name='$name';"
}

sub insertDefCats {
	  my
	  $st = $_[0]->prepare('INSERT INTO CAT VALUES (?,?,?)'); 
	  		$_[0]->begin_work();
		$st->execute(1, "Unspecified", "For quick uncategorised entries.");
		$st->execute(3, "File", "Operating file system short log.");
		$st->execute(6, "System Log", "Operating system important log.");
		$st->execute(9, "Event", "Event that occured, meeting, historically important.");
		$st->execute(28,"Personal", "Personal log of historical importance, diary type.");
		$st->execute(32,"Expense", "Significant yearly expense.");
		$st->execute(35,"Income", "Significant yearly income.");
		$st->execute(40,"Work", "Work related entry, worth monitoring.");
		$st->execute(45,"Food", "Quick reference to recepies, observations.");
		$_[0]->commit();
		$st->finish();
}


sub removeOldSessions {
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
