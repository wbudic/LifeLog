#!/usr/bin/perl -w
#
# Programed by: Will Budic
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


#DEFAULT SETTINGS HERE!
use lib "system/modules";
require Settings;


my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>&Settings::logPath});
   $session->expire(&Settings::sessionExprs);
my $sssCreatedDB = $session->param("cdb");
my $sid=$session->id();
my $cookie = $cgi->cookie(CGISESSID => $sid);


my $alias = $cgi->param('alias');
my $passw = $cgi->param('passw');
my ($debug,$frm) = "";
#Codebase release version. Release in the created db or existing one can be different, through time.
my $RELEASE = Settings::release();

#This is the OS developer release key, replace on istallation. As it is not secure.
my $cipher_key = '95d7a85ba891da';

if($cgi->param('logout')){&logout}

&checkAutologinSet;
if(&processSubmit==0){

    print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie);
    print $cgi->start_html(
    -title   => "Personal Log Login",
    -BGCOLOR => &Settings::bgcol,
    -script => [
                { -type => 'text/javascript', -src => 'wsrc/main.js' },    ],
    -style  => [
                { -type => 'text/css', -src => 'wsrc/'.&Settings::css }
            ]
);

my @ht = split(m/\s/,`hostname -I`);
my $hst = `hostname` . "($ht[0])";

$frm = qq(
     <form id="frm_login" action="login_ctr.cgi" method="post"><table border="0" width=").&Settings::pagePrcWidth.qq(%">
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
      <tr class="r0"><td colspan="2">Your Host -> <b>$hst</b></td><td><input type="submit" value="Login"/></td></tr>
    </table></form>);

print qq(<br><br><div id="rz">
                        <center>
                            <h2>Welcome to Life Log</h2><div>$frm</div><br>
                            <a href="https://github.com/wbudic/LifeLog" target="_blank">Get latest version of this application here!</a><br>
                        </center><div>);

Settings::printDebugHTML($debug) if (&Settings::debug);
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
            #CheckTables will return 1 if it was an logout set in config table.
            if(&checkCreateTables()==0){
                $session->param('alias', $alias);
                $session->param('passw', $passw);
                $session->param('database', 'data_'.$alias.'_log.db');
                $session->flush();
                print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie, -location=>"main.cgi");
                return 1; #activate redirect to main, main will check credentials.
            }
    }
    else{
        $alias = $passw = "";
    }
    &Settings::removeOldSessions;  #and prompt for login returning 0
return 0;
}
 catch{
        print $cgi->header;
        print "<font color=red><b>SERVER ERROR processSubmit()</b></font>: $_ dump ->". $session->dump();
        print $cgi->end_html;
 }
}

sub checkAutologinSet {
try{
        #We don't need to slurp as it is expected setting in header.
        my @cre;
        open(my $fh, '<', &Settings::logPath.'main.cnf' ) or die "Can't open main.cnf: $!";
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
             my $database = &Settings::logPath.'data_'.$cre[0].'_log.db';
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
                         &Settings::removeOldSessions;
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
       $today->set_time_zone( &Settings::timezone );
    my $database = &Settings::logPath.'data_'.$alias.'_log.db';
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
             AMOUNT INTEGER DEFAULT 0,
             AFLAG TINY DEFAULT 0,
             RTF BOOL DEFAULT 0,
             STICKY BOOL DEFAULT 0
        );
        CREATE INDEX idx_log_dates ON LOG (DATE);
        );

        if($sssCreatedDB){
            print $cgi->header;
            print $cgi->start_html;
            print "<center><font color=red><b>A new alias login detect! <br>
            Server security measure has been triggered -> Sorry further new alias login/creation not allowed!</b></font><br><br>Contact your network admin.</center>".$_;
            print $cgi->end_html;
            exit;
        }

        $db->do($stmt);

        $st = $db->prepare('INSERT INTO LOG(ID_CAT,DATE,LOG) VALUES (?,?,?)');
        $st->execute( 3, $today, "DB Created!");
        $session->param("cdb", "1");
    }

    # From v.1.6 view use server side views, for pages and correct record by ID and PID lookups.
    # This should make queries faster, less convulsed, and log renumeration less needed, for accurate pagination.
    $st = $db->prepare(selSQLView('VW_LOG'));
    $st->execute();
    if(!$st->fetchrow_array()) {
        $rv = $db->do('CREATE VIEW VW_LOG AS
                              SELECT rowid as ID,*, (select count(rowid) from LOG as recount where a.rowid >= recount.rowid) as PID
                              FROM LOG as a ORDER BY DATE DESC;');
        if($rv < 0){print "<p>Error->"& $DBI::errstri &"</p>";}
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


    my $stmt = qq(
        CREATE TABLE AUTH(
                alias varchar(20) PRIMARY KEY,
                passw TEXT,
                email varchar(44),
                action TINY
        ) WITHOUT ROWID;
        CREATE INDEX idx_auth_name_passw ON AUTH (ALIAS, PASSW);
        );


        $rv = $db->do($stmt);
        if($rv < 0){print "<p>Error->"& $DBI::errstri &"</p>"};
        $st = $db->prepare("SELECT ALIAS, PASSW, EMAIL, ACTION FROM AUTH WHERE alias='$alias' AND passw='$passw';");
        $st->execute();
        my @res = $st->fetchrow_array();
        if(scalar @res == 0) {
            $st = $db->prepare('INSERT INTO AUTH VALUES (?,?,?,?);');
            $st->execute($alias, $passw,"",0);
        }
    }
    #
    # Scratch FTS4 implementation if present.
    #
    $st = $db->prepare(selSQLTbl('NOTES_content'));
    $st->execute();
    if($st->fetchrow_array()) {
        $rv = $db->do('DROP TABLE NOTES;');
        if($rv < 0){print "<p>Error->"& $DBI::errstri &"</p>"};
    }
    #
    # New Implementation as of 1.5, cross SQLite Database compatible.
    #
    $st = $db->prepare(selSQLTbl('NOTES'));
    $st->execute();
    if(!$st->fetchrow_array()) {
        my $stmt = qq(
            CREATE TABLE NOTES (LID PRIMARY KEY NOT NULL, DOC TEXT);
        );
        $rv = $db->do($stmt);
        if($rv < 0){print "<p>Error->"& $DBI::errstri &"</p>"};
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
                #Has configuration been wiped out?
                $st = $db->prepare('SELECT count(ID) FROM CONFIG;'); $st->execute();
                $changed = 1 if(!$st->fetchrow_array());
    }
    #We got an db now, lets get settings from there.
    Settings::getConfiguration($db);
    if(!$changed){
        #Run db fix renum if this is an relese update? Relese in software might not be what is in db, which counts.
        #$st = Settings::dbExecute($db, 'SELECT NAME, VALUE FROM CONFIG WHERE NAME == "RELEASE_VER";');
        $st	= $db->prepare('SELECT ID, NAME, VALUE FROM CONFIG WHERE NAME IS "RELEASE_VER";');
        $st->execute() or die "<p>ERROR with->$DBI::errstri</p>";
        my @pair = $st->fetchrow_array();
        my $cmp = $pair[2] eq $RELEASE;
        $debug .= "Upgrade cmp(RELESE_VER:'$pair[2]' eq Settings::release:'$RELEASE') ==  $cmp";
        #Settings::debug(1);
        if(!$cmp){
            Settings::renumerate($db);
            #App private inner db properties, start from 200.
            #^REL_RENUM is marker that an renumeration is issued during upgrade.
            my $pv = &Settings::obtainProperty($db, '^REL_RENUM');
            if($pv){
                $pv += 1;
            }
            else{
                $pv = "1";
            }
            &Settings::configProperty($db, 200, '^REL_RENUM',$pv);
            &Settings::configProperty($db, $pair[0], 'RELEASE_VER', $RELEASE);
            &Settings::toLog($db,&dbTimeStamp, "Upgraded LifeLog from ".$pair[2]." to $RELEASE version, this is the $pv upgrade.");
            &populate($db);
        }
    }
    else{
        &populate($db);
    }
    #
     $db->disconnect();
    #
    #Still going through checking tables and data, all above as we might have an version update in code.
    #Then we check if we are login in intereactively back. Interective, logout should bring us to the login screen.
    #Bypassing auto login. So to start maybe working on another database, and a new session.
    return $cgi->param('autologoff') == 1;
}
 catch{
    print $cgi->header;
    print "<font color=red><b>SERVER ERROR</b></font>:".$_;
    print $cgi->end_html;
    exit;
 }

}
#TODO move this subroutine to settings.
sub dbTimeStamp {
    my $dat = DateTime->now;
    $dat -> set_time_zone(Settings::timezone());
    return DateTime::Format::SQLite->format_datetime($dat);
}

sub populate {

        my $db = shift;
        my ($did,$name, $value, $desc);
        my $inData = 0;
        my $err = "";
        my %vars = ();
        my @lines;
        my $table_type = 0;

        open(my $fh, "<:perlio", &Settings::logPath.'main.cnf' ) or die "Can't open main.cnf: $!";
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

                    last if ($line =~ /<MIG<>/);
                    my @tick = split("`",$line);

                     if( index( $line, '<<CONFIG<' ) == 0 ){$table_type = 0; $inData = 0;}
                    elsif( index( $line, '<<CAT<' ) == 0 )   {$table_type = 1; $inData = 0;}
                    elsif( index( $line, '<<LOG<' ) == 0 )   {$table_type = 2; $inData = 0;}
                    elsif( index( $line, '<<~MIG<>' ) == 0 ) {next;} #Migration is complex main.cnf contains though SQL alter statements.

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
                                                                                      $insConfig->execute($id,$name,$value,$tick[1]);
                                                                                }
                                                                    }
                                                                }
                                                        }else{
$err .= "Invalid, spec'ed {uid}|{variable}`{description}-> $line\n";
                                                        }

                                                }#rof
                                    }
                                    elsif($table_type==0){
                                                        $err .= "Invalid, spec'd entry -> $line\n";
                                    }elsif($table_type==1){
                                                            my @pair = $tick[0] =~ m[(\S+)\s*\|\s*(\S+)]g;
                                                            if ( scalar(@pair)==2 ) {
                                                                    my $st = $db->prepare("SELECT ID FROM CAT WHERE NAME LIKE '$pair[1]';");
                                                                        $st->execute();
                                                                        $inData = 1;
                                                                        if(!$st->fetchrow_array()) {
                                                                            $insCat->execute($pair[0],$pair[1],$tick[1]);
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
        die "Configuration script ".&Settings::logPath."/main.cnf [$fh] contains errors." if $err;
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

sub selSQLView{
      my $name = $_[0];
return "SELECT name FROM sqlite_master WHERE type='view' AND name='$name';"
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
    <form action="login_ctr.cgi"><input type="hidden" name="autologoff" value="1"/><input type="submit" value="No, no, NO! Log me In Again."/></form><br>
    </br>
    <iframe width="60%" height="600px" src="https://www.youtube.com/embed/qTFojoffE78?autoplay=1"
      frameborder="0"
        allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>
    </iframe>
    </center></font>
    );

    print $cgi->end_html;
    exit;
}

### CGI END
