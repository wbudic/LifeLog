#!/usr/bin/perl -w
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;
use CGI;
use CGI::Session '-ip_match';
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
#Bellow perl 5.28+
#use experimental 'smartmatch';

#DEFAULT SETTINGS HERE!
use lib "system/modules";
require Settings;
my $BACKUP_ENABLED = 0;

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

if($cgi->param('logout')){&logout}

try{
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
    my $hst = "";
       $hst = `hostname` . "($ht[0])" if (@ht);

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
}
 catch {
            my $err = $@;
            my $dbg = "" ;
            my $pwd = `pwd`;
            $pwd =~ s/\s*$//;
            $dbg = "--DEBUG OUTPUT--\n$debug" if $debug;
            print $cgi->header,
            "<hr><font color=red><b>SERVER ERROR</b></font> on ".DateTime->now.
            "<pre>".$pwd."/$0 -> &".caller." -> [$err]","\n$dbg</pre>",
            $cgi->end_html;
 };
exit;

sub processSubmit {
    if($alias&&$passw){

            $passw = uc crypt $passw, hex Settings->CIPHER_KEY;
            #CheckTables will return 1 if it was an logout set in config table.
            if(&checkCreateTables()==0){
                $session->param('alias', $alias);
                $session->param('passw', $passw);
                $session->param('database', 'data_'.$alias.'_log.db');
                $session->flush();
                ### To MAIN PAGE
                print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie, -location=>"main.cgi");
                ###
                return 1; #activated redirect to main, main will check credentials.
            }
    }
    else{
        $alias = $passw = "";
    }
    &Settings::removeOldSessions;  #and prompt for login returning 0
    return 0;
}

sub checkAutologinSet {

    #We don't need to slurp as it is expected setting in header.
    my (@cre, $end,$crest);
    open(my $fh, '<', &Settings::logPath.'main.cnf' ) or LifeLogException->throw("Can't open main.cnf: $!");
    while (my $line = <$fh>) {
                chomp $line;
                if(rindex ($line, "<<AUTO_LOGIN<", 0)==0){
                        $end = index $line, ">", 14;
                        $crest = substr $line, 13, $end - 13;
                        @cre = split '/', $crest;
                       next;
                }
                elsif(rindex ($line, "<<BACKUP_ENABLED<", 0)==0){
                        $end = index $line, ">", 18;
                        $BACKUP_ENABLED = substr $line, 17, $end - 17;
                    last; #we expect as last anon to be set.
                }
                elsif(rindex ($line, "<<CONFIG<",0) == 0){last;}
    }
    close $fh;
    if(@cre &&scalar(@cre)>1){##TODO we already connected here to the db, why do it again later?

            if($alias && $passw && $alias ne $cre[0]){ # Is this an new alias login attempt?
                return;                                # Note, we do assign entered password even passw as autologin is set. Not entering one bypasses this.
            }                                          # If stricter access is required set it to zero in main.cnf, or disable in config.
            $passw = $cre[1] if (!$passw);
            my $database = &Settings::logPath.'data_'.$cre[0].'_log.db';
            my $dsn= "DBI:SQLite:dbname=$database";
            my $db = DBI->connect($dsn, $cre[0], $cre[1], { RaiseError => 1 })
                       or LifeLogException->throw("<p>Error->"& $DBI::errstri &"</p>");
                #check if enabled.
            my $st = $db->prepare("SELECT VALUE FROM CONFIG WHERE NAME='AUTO_LOGIN';");
            $st->execute();
            my @set = $st->fetchrow_array();
            if(@set && $set[0]=="1"){
                    $alias = $cre[0];
                    $passw = $passw; #same as entered, by the not knowing to leave it blank.
                    &Settings::removeOldSessions;
            }
            $db->disconnect();
    }

}

sub checkCreateTables {

    my $today = DateTime->now;
       $today-> set_time_zone( &Settings::timezone );
    my $database = &Settings::logPath.'data_'.$alias.'_log.db';
    my $dsn= "DBI:SQLite:dbname=$database";
    my $db = DBI->connect($dsn, $alias, $passw, { RaiseError => 1 }) or LifeLogException->throw($DBI::errstri);
    my ($pst, $sql,$rv, $changed) = 0;
    # We live check database for available tables now only once.
    # If brand new database, this sill returns fine an empty array.
    my $pst = Settings::selectRecords($db,"SELECT name FROM sqlite_master WHERE type='table' or type='view';");
    my %curr_tables = ();
    while(my @r = $pst->fetchrow_array()){
        $curr_tables{$r[0]} = 1;
    }
    if($curr_tables{'CONFIG'}) {
        #Set changed if has configuration data been wiped out.
        $changed = 1 if Settings::countRecordsIn($db, 'CONFIG') == 0;
    }
    else{
        #v.1.3 -> v.1.4
        #has alter table CONFIG add DESCRIPTION VCHAR(128);
        $rv = $db->do(&Settings::createCONFIGStmt);
        $changed = 1;
    }
    # Now we got a db with CONFIG, lets get settings from there.
    # Default version is the scripted current one, which could have been updated.
    # We need to maybe update further, if these versions differ.
    # Source default and the one from the CONFIG table in the (present) database.
    my $DEF_VERSION = Settings::release();
                      Settings::getConfiguration($db,{backup_enabled=>$BACKUP_ENABLED});
    my $DB_VERSION  = Settings::release();
    my $hasLogTbl   = $curr_tables{'LOG'};
    my $hasNotesTbl = $curr_tables{'NOTES'};
    my @annons = Settings::anons();
    LifeLogException -> throw("Annons!") if (@annons==0);#We even added above the backup_enabled anon, so WTF?

    # Reflect anons to db config.
    $sql = "SELECT ID, NAME, VALUE FROM CONFIG WHERE";
    foreach my $ana(@annons){$sql .=  " NAME LIKE '$ana' OR";};$sql =~ s/OR$//; $sql .=';';
    $pst =  Settings::selectRecords($db, $sql);
    while(my @row = $pst->fetchrow_array()) {
        my ($vid,$n,$sv, $dv) = ($row[0], $row[1], Settings::anon($row[1]), $row[2]);
        $db->do("UPDATE CONFIG SET VALUE='$sv' WHERE ID=$vid;") if($dv ne $sv);
    }
    #
    # From v.1.8 Log has changed, to have LOG to NOTES relation.
    #
    if($hasLogTbl && $DEF_VERSION > $DB_VERSION && $DB_VERSION < 1.8){
        # We must upgrade now. If existing LOG table is now invalid old version containing boolean RTF.
        Settings::debug(1);
        my @names = @{Settings::getTableColumnNames($db, 'LOG')};
        #perl 5.28+ <--
        #if ( 'RTF' ~~ @names ) {
        if(grep( /RTF/, @names)){
            $db->do('DROP TABLE life_log_login_ctr_temp_table;') if($curr_tables{'life_log_login_ctr_temp_table'});
            $db->do('CREATE TABLE life_log_login_ctr_temp_table AS SELECT * FROM LOG;');
            my %notes_ids = ();
            if($hasNotesTbl){
                $pst =  Settings::selectRecords($db, 'SELECT rowid, DATE FROM LOG WHERE RTF > 0 ORDER BY DATE;');
                while(my @row = $pst->fetchrow_array()) {
                        my $sql_date = $row[1];;
                        $sql_date = DateTime::Format::SQLite->parse_datetime($sql_date);
                        my $pst2  = Settings::selectRecords($db, "SELECT rowid, DATE FROM life_log_login_ctr_temp_table WHERE RTF > 0 AND DATE = '".$sql_date."';");
                        my @rec   = $pst2->fetchrow_array();
                        if(@rec){
                            $db->do("UPDATE NOTES SET LID =". $rec[0]." WHERE LID ==".$row[0].";");
                            $pst2  = Settings::selectRecords($db, "SELECT rowid FROM NOTES WHERE LID == ".$rec[0].";");
                            @rec   = $pst2->fetchrow_array();
                            if(@rec){
                                    $notes_ids{$sql_date} = $rec[0];
                            }
                        }
                }

            }
            $db->do('DROP TABLE LOG;');
            #v.1.8 Has fixes, time also properly to take into the sort. Not crucial to drop.
            $db->do('DROP TABLE VW_LOG;');delete($curr_tables{'VW_LOG'});
            $db->do(&Settings::createLOGStmt);
            $db->do('INSERT INTO LOG (ID_CAT, DATE, LOG, AMOUNT,AFLAG)
                                SELECT ID_CAT, DATE, LOG, AMOUNT, AFLAG FROM life_log_login_ctr_temp_table ORDER by DATE;');
            $db->do('DROP TABLE life_log_login_ctr_temp_table;');

            #Experimental sofar NOTES table has LID changed to proper number type.
            $db->do(qq(CREATE TABLE life_log_rename_column_new_table (
        	            LID	INTEGER NOT NULL PRIMARY KEY,    DOC	TEXT);));
            $db->do('INSERT INTO life_log_rename_column_new_table SELECT `LID`,`DOC` FROM `NOTES`;');
            $db->do('DROP TABLE `NOTES`;');
            $db->do('ALTER TABLE `life_log_rename_column_new_table` RENAME TO `NOTES`');


            #Update new LOG with notes RTF ids, in future versions, this will never be required anymore.
            foreach my $date (keys %notes_ids){
                #next if(ref($notes_ids{$date}) eq 'HASH');
                my $nid = $notes_ids{$date};
                my $stmt= "UPDATE LOG SET ID_RTF =". $nid." WHERE DATE == '".$date."';";
                try{
                    $db->do($stmt);
                }
                 catch{
                        LifeLogException -> throw(error=>"Upgrade statement -> [$stmt] failed!", show_trace=>1);
                 }
            }
            undef %notes_ids;
        }
        #Version change still detected above.
        #Need to run slow populuate check from config file.
        $changed = 1;
    }

    if(!$hasLogTbl) {

        if($sssCreatedDB){
            print $cgi->header;
            print $cgi->start_html;
            print "<center><font color=red><b>A new alias login detect! <br>
            Server security measure has been triggered -> Sorry further new alias login/creation not allowed!</b></font><br><br>Contact your network admin.</center>".$_;
            print $cgi->end_html;
            exit;
        }

        $db->do(&Settings::createLOGStmt);

        my $st = $db->prepare('INSERT INTO LOG(ID_CAT,DATE,LOG) VALUES (?,?,?)');
            $st->execute( 3, $today, "DB Created!");
            $session->param("cdb", "1");
    }

    # From v.1.6 view use server side views, for pages and correct record by ID and PID lookups.
    # This should make queries faster, less convulsed, and log renumeration less needed for accurate pagination.
    if(!$curr_tables{'VW_LOG'}) {
        $rv = $db->do(&Settings::createVW_LOGStmt);
    }
    if(!$curr_tables{'CAT'}) {
        $db->do(&Settings::createCATStmt);
        $changed = 1;
    }else{
        # If empty something happened to it. It shouldn't be EMPTY!
        my @ret=Settings::selectRecords($db, "SELECT count(0) from CAT;")->fetchrow_array();
        $changed = 1 if (!$ret[0]);
    }
    #Have cats been wiped out?
    $changed = 1 if Settings::countRecordsIn($db, 'CAT') == 0;

    #TODO Multiple cats per log future table.
    if(!$curr_tables{'LOGCATSREF'}) {
        $db->do(&Settings::createLOGCATSREFStmt);
    }

    if(!$curr_tables{'AUTH'}) {
        $db->do(&Settings::createAUTHStmt);
        my $st = $db->prepare('INSERT INTO AUTH VALUES (?,?,?,?);');
           $st->execute($alias, $passw,"",0);
    }
    #
    # Scratch FTS4 implementation if present.
    #
    if($curr_tables{'NOTES_content'}) {
        $db->do('DROP TABLE NOTES;');
        $db->do('DROP NOTES_content;');
        $hasNotesTbl = 0;
    }
    #
    # New Implementation as of 1.5, cross SQLite Database compatible.
    #
    if(!$hasNotesTbl) {$db->do(&Settings::createNOTEStmt);}

    if($changed){
        #It is also good to run db fix (config page) to renum if this is an release update?
        #Release in software might not be what is in db, which counts.
        #This here next we now update.
        my @r = Settings::selectRecords($db, 'SELECT ID, VALUE FROM CONFIG WHERE NAME IS "RELEASE_VER";')->fetchrow_array();
        my $did = $r[0];
        my $dnm = $r[1];
        my $cmp = $dnm eq $RELEASE;
        $debug .= "Upgrade cmp(RELESE_VER:'$dnm' eq Settings::release:'$RELEASE') ==  $cmp";
        #Settings::debug(1);
        if(!$cmp){
            Settings::renumerate($db);
            #App private inner db properties, start from 200.
            #^REL_RENUM is marker that an renumeration is issued during upgrade.
            my $pv = &Settings::obtainProperty($db, '^REL_RENUM');
            if($pv){
                $pv++;
            }
            else{
                $pv = 0;
            }
            &Settings::configProperty($db, 200, '^REL_RENUM',$pv);
            &Settings::configProperty($db, $did>0?$did:0, 'RELEASE_VER', $RELEASE);
            &Settings::toLog($db, "Upgraded Life Log from v.$dnm to v.$RELEASE version, this is the $pv upgrade.") if $pv;
        }
        &populate($db);
    }
    Settings::toLog($db, "Log accessed by $alias.") if(&Settings::trackLogins);
    #
        $db->disconnect();
    #
    #Still going through checking tables and data, all above as we might have an version update in code.
    #Then we check if we are login in intereactively back. Interective, logout should bring us to the login screen.
    #Bypassing auto login. So to start maybe working on another database, and a new session.
    return $cgi->param('autologoff') == 1;

}


sub populate {

    my $db = shift;
    my ($did,$name, $value, $desc);
    my $inData = 0;
    my $err = "";
    my %vars = ();
    my @lines;
    my $tt = 0;

    open(my $fh, "<:perlio", &Settings::logPath.'main.cnf' ) or LifeLogException->throw( "Can't open main.cnf: $!");
    read $fh, my $content, -s $fh;
             @lines  = split '\n', $content;
    close $fh;

    my $insConfig = $db->prepare('INSERT INTO CONFIG VALUES (?,?,?,?)');
    my $insCat    = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
                    $db->begin_work();
    foreach my $line (@lines) {

                    last if ($line =~ /<MIG<>/);#Not doing it with CNF1.0

                       if( index( $line, '<<CONFIG<' ) == 0 )  {$tt = 0; $inData = 0;}
                    elsif( index( $line, '<<CAT<'    ) == 0 )  {$tt = 1; $inData = 0;}
                    elsif( index( $line, '<<LOG<'    ) == 0 )  {$tt = 2; $inData = 0;}

                    my @tick = split("`",$line);
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
                                     elsif($tt==0){
$err .= "Invalid, spec'd entry -> $line\n";
                                    }elsif($tt==1){
                                                            my @pair = $tick[0] =~ m[(\S+)\s*\|\s*(\S+\s*\S*)]g;
                                                            if ( scalar(@pair)==2 ) {
                                                                        # In older DB versions the Category name could be different, user modified.
                                                                        # The unique id and name interwined, changed. Hence we check on name first.
                                                                        # Then check if the  ID is available. If not just skip, the import. Reseting can fix that latter.
                                                                        if(!Settings::selectRecords($db, "SELECT ID FROM CAT WHERE NAME LIKE '$pair[1]';")->fetchrow_array()) {
                                                                            if(!Settings::selectRecords($db, "SELECT ID FROM CAT WHERE ID = $pair[0];")->fetchrow_array()){
                                                                               $insCat->execute($pair[0],$pair[1],$tick[1]);
                                                                            }
                                                                        }
                                                                        $inData = 1;
                                                            }
                                                            else {
$err .= "Invalid, spec'ed {uid}|{category}`{description}-> $line\n";
                                                            }
                                    }elsif($tt==2){
                                            #TODO Do we really want this? Insert into log from config script.
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
    LifeLogException->throw(error=>"Configuration script ".&Settings::logPath."/main.cnf [$fh] contains errors. Err:$err", show_trace=>1) if $err;
    $db->commit();
}

sub selSQLTbl {
      my $name = $_[0];
return "SELECT name FROM sqlite_master WHERE type='table' AND name='$name';"
}

sub selSQLView {
      my $name = $_[0];
return "SELECT name FROM sqlite_master WHERE type='view' AND name='$name';"
}


sub logout {

    if(&Settings::trackLogins){
    try{
        $alias = $session->param('alias');
        $passw = $session->param('passw');
        my $database = &Settings::logPath.'data_'.$alias.'_log.db';
        my $dsn= "DBI:SQLite:dbname=$database";
        my $db = DBI->connect($dsn, $alias, $passw, { RaiseError => 1 })
                    or LifeLogException->throw($DBI::errstri);
        Settings::toLog($db, "Log properly loged out by $alias.");
        $db->disconnect();
    }catch{
        my $err = $@;
        my $dbg = "" ;
        my $pwd = `pwd`;
        $pwd =~ s/\s*$//;
        $dbg = "--DEBUG OUTPUT--\n$debug" if $debug;
        print $cgi->header,
        "<font color=red><b>SERVER ERROR</b></font> on ".DateTime->now.
        "<pre>".$pwd."/$0 -> &".caller." -> [$err]","\n$dbg</pre>",
        $cgi->end_html;
        exit;
    }
    }


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

    $session->delete();
    $session->flush();


    exit;
}

### CGI END
