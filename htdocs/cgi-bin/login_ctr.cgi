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

use lib "system/modules";
require Settings;

my $cgi = CGI->new();
my $session = new CGI::Session("driver:File",$cgi, {Directory=>Settings::logPath()});
   $session->expire(Settings::sessionExprs());
my $sssCreatedDB = $session->param("cdb");
my $sid=$session->id();
my $cookie = $cgi->cookie(CGISESSID => $sid);

my $db;
my $alias = $cgi->param('alias');
my $passw = $cgi->param('passw');
my ($DBG,$frm) = "";
#Codebase release version. Release in the created db or existing one can be different, through time.
my $SCRIPT_RELEASE = Settings::release();

#anons - Are parsed end obtained only here, to be transfered to the DB config.
my $BACKUP_ENABLED = 0;
my $AUTO_SET_TIMEZONE = 0;
my $TIME_ZONE_MAP = 0;
my ($DB_NAME,$PAGE_EXCLUDES);

try{
    checkAutologinSet();
    logout() if($cgi->param('logout'));
    if(processSubmit()==0){

        print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie);
        print $cgi->start_html(
                    -title   => "Personal Log Login",
                    -BGCOLOR => &Settings::bgcol,
                    -script=> [{-type => 'text/javascript', -src => 'wsrc/main.js'},
                                {-type => 'text/javascript', -src => 'wsrc/jquery.js'},
                                {-type => 'text/javascript', -src => 'wsrc/jquery-ui.js'}],
                    -style => [{-type => 'text/css', -src => "wsrc/".&Settings::css},
                                {-type => 'text/css', -src => 'wsrc/jquery-ui.css'},
                                {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'},
                                {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'}],
                    -onload  => "onBodyLoadGeneric()"
        );

    my @ht = split(m/\s/,`hostname -I`);
    my $hst = "";
       $hst = `hostname` . "($ht[0])" if (@ht);

    $frm = qq(
        <form id="frm_login" action="login_ctr.cgi" method="post"><table border="0" width=").Settings::pagePrcWidth().qq(%">
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
        <tr class="r0"><td colspan="2">Host -> <b>$hst</b></td><td><input type="submit" value="Login"/></td></tr>
        </table></form>);

    print qq(<br><br><div id="rz">
            <center>
                <h2>Welcome to Life Log</h2><div>$frm</div><br>
                <a href="https://github.com/wbudic/LifeLog" 
                target="_blank" style="font-size:small">LifeLog v.).Settings::release().qq(</a><br>
            </center><div>);

    Settings::printDebugHTML($DBG) if Settings::debug();
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
            $dbg = "--DEBUG OUTPUT--\n$DBG" if Settings::debug();
            print $cgi->header,
            "<hr><font color=red><b>SERVER ERROR</b></font> on ".DateTime->now().
            "<pre>".$pwd."/$0 -> [\n$err]","\n$dbg</pre>",
            $cgi->end_html;
 };
exit;

sub processSubmit {
    if($alias&&$passw){

            $passw = uc crypt $passw, hex Settings->CIPHER_KEY;
            #CheckTables will return 1 if it was an logout set in config table.
            if(checkCreateTables()==0){
                $session->param('alias', $alias);
                $session->param('passw', $passw);
                $session->param('db_source', Settings::dbSrc());
                $session->param('db_file',   Settings::dbFile());
                $session->param('database',  Settings::dbName());                
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
    Settings::removeOldSessions();  #and prompt for login returning 0
    return 0;
}

sub checkAutologinSet {
    my (@cre, $v);
    # We don't need to slurp whole file as next are expected settings in begining of the config file.
    open(my $fh, '<', Settings::logPath().'main.cnf' ) or LifeLogException->throw("Can't open main.cnf: $!");
    while (my $line = <$fh>) {
        chomp $line;
        $v = Settings::parseAutonom('AUTO_LOGIN',$line);
        if($v){@cre = split '/', $v; next}
        $v = Settings::parseAutonom('BACKUP_ENABLED',$line);
        if($v){$BACKUP_ENABLED = $v; next}
        $v = Settings::parseAutonom('DBI_SOURCE',$line);
        if($v){Settings::dbSrc($v); next}
        $v = Settings::parseAutonom('AUTO_SET_TIMEZONE',$line);                
        if($v){$AUTO_SET_TIMEZONE = $v; next}
        $v = Settings::parseAutonom('DBI_LOG_VAR_SIZE',$line);
        if($v){Settings::dbVLSZ($v); next}
        # From here are config file only autonoms. Don't need or harm being in database configuration.
        $v = Settings::parseAutonom('DBI_MULTI_USER_DB',$line);
        if($v){$DB_NAME=$v;Settings::dbName($v);next}
        if($line =~ /<<TIME_ZONE_MAP</){
            $TIME_ZONE_MAP = substr($line,16);
            while ($line = <$fh>) {
                chomp $line;
                last if($line =~ />$/);
                $TIME_ZONE_MAP .= $line . "\n";
            }
            next;
        }
        $v = Settings::parseAutonom('PAGE_VIEW_EXCLUDES',$line);
        if($v){$PAGE_EXCLUDES=$v;next}
        last if Settings::parseAutonom('CONFIG',$line); #By specs the config tag, is not an autonom, if found we stop reading. So better be last one spec. in file.
    }
    close $fh;
    # Autologin credential in file next.
    if(@cre &&scalar(@cre)>1){

            if($alias && $passw && $alias ne $cre[0]){ # Is this an new alias login attempt? If so, autologin is of the agenda.
                return;                                # Note, we do assign entered password even passw as autologin is set. Not entering one bypasses this.
            }                                          # If stricter access is required set it to zero in main.cnf, or disable in config.
            $passw = $cre[1] if (!$passw);
            $db = Settings::connectDB($alias, $passw);            
            #check if autologin enabled.
            my $st = Settings::selectRecords($db,"SELECT VALUE FROM CONFIG WHERE NAME='AUTO_LOGIN';");                        
            if($st){
                my @set = $st->fetchrow_array();
                if($set[0]=="1"){
                        $alias = $cre[0];
                        $passw = $passw; 
                        Settings::removeOldSessions();
                }
                $st->finish();
            }
            $db -> disconnect();
    }

}

sub checkPreparePGDB {
    my $create =1;
    $passw = $cgi->param('passw'); #We let PG handles password encryption (security) itself.
    my @data_sources = DBI->data_sources("Pg");
    foreach my $ln (@data_sources){
            my $i = rindex $ln, '=';
            my $n = substr $ln, $i+1;
            if($n eq $alias){ $create = 0; last;}
    }
    if($create){
        # TODO Default expected to exist db is postgres, username and password. This cgi connects locally.
        # Modify this to take any other situations or create main.cnf anon properties for all this. 
        # To the user with roes and database creation powers.
        my $db = DBI->connect('dbi:Pg:dbname=postgres;host=localhost','postgres', 'postgres');
        Settings::debug(1);
        $db->do(qq(
            CREATE ROLE $alias WITH
                LOGIN
                SUPERUSER
                CREATEDB
                CREATEROLE
                INHERIT
                NOREPLICATION
                CONNECTION LIMIT -1
                PASSWORD '$passw';
        ));
        $db->do(qq(
            CREATE DATABASE $alias
                WITH 
                OWNER = $alias
                ENCODING = 'UTF8'
                LC_COLLATE = 'en_AU.UTF-8'
                LC_CTYPE = 'en_AU.UTF-8'
                TABLESPACE = pg_default
                CONNECTION LIMIT = -1;
        ));
        $db->disconnect(); undef $db;
        return 1;
    }    
    return 0;
}

sub checkCreateTables {

try{    
    my ($pst, $sql,$rv, $changed) = 0;
    
    # We live check database for available tables now only once.
    # If brand new database, this sill returns fine an empty array.
    my %curr_tables = ();
    #my %curr_colums = (); # %("table", @{...columns...})

    if(Settings::isProgressDB()){        
        $changed = checkPreparePGDB();
        $db = Settings::connectDB($DB_NAME, $alias, $passw); 
        my @tbls = $db->tables(undef, 'public');
        foreach (@tbls){
            my $t = uc substr($_,7);
            $curr_tables{$t} = 1;
        }
    }
    else{
        $db = Settings::connectDB($DB_NAME, $alias, $passw); 
        $pst = Settings::selectRecords($db,"SELECT name FROM sqlite_master WHERE type='table' or type='view';");        
        while(my @r = $pst->fetchrow_array()){
            $curr_tables{$r[0]} = 1;
        }
    }
    if($curr_tables{'CONFIG'}) {
        #Set changed if has configuration data been wiped out.
        $changed = 1 if Settings::countRecordsIn($db, 'CONFIG') == 0;
    }
    else{
        #v.1.3 -> v.1.4
        #has alter table CONFIG add DESCRIPTION VCHAR(128);
        $rv = $db->do(Settings::createCONFIGStmt());
        $changed = 1;
    }
    # Now we got a db with CONFIG, lets get settings from there.
    # Default version is the scripted current one, which could have been updated.
    # We need to maybe update further, if these versions differ.
    # Source default and the one from the CONFIG table in the (present) database.    
    Settings::getConfiguration($db,{
         backup_enabled=>$BACKUP_ENABLED,auto_set_timezone=>$AUTO_SET_TIMEZONE,TIME_ZONE_MAP=>$TIME_ZONE_MAP, db_log_var_limit=>Settings::dbVLSZ()
         });    
    my $DB_VERSION  = Settings::release();
    my $hasLogTbl   = $curr_tables{'LOG'};
    my $hasNotesTbl = $curr_tables{'NOTES'};
    my @annons = Settings::anons();
    LifeLogException -> throw("Annons!") if (@annons==0);#We even added above the backup_enabled anon, so WTF?
    if($curr_tables{'life_log_temp_table'}){#A possible of some old migration lingering...
       $db->do('DROP TABLE `life_log_temp_table`;');
    }
    # Reflect anons to db config.
    $sql = "SELECT ID, NAME, VALUE FROM CONFIG WHERE";
    foreach my $ana(@annons){$sql .=  " NAME LIKE '$ana' OR";};$sql =~ s/OR$//; $sql .=';';
    $pst =  Settings::selectRecords($db, $sql);
    while(my @row = $pst->fetchrow_array()) {
        my ($sup,$vid,$n,$sv, $dv) = ("",$row[0], $row[1], Settings::anon($row[1]), $row[2]);
        try{
           if($dv ne $sv){
               $sup = "UPDATE CONFIG SET VALUE='$sv' WHERE ID=$vid;";
               $db->do($sup);
           }
        }catch{$@.="\n$sup"; die "Failed[$@]"}
    }
    #Is it pre or around v.2.1, where ID_RTF is instead of RTF in the LOG table?
    if($hasLogTbl && !Settings::isProgressDB()){ 
        $pst = Settings::selectRecords($db, "SELECT * from pragma_table_info('LOG') where name like 'ID_RTF';");
        my @row = $pst = $pst->fetchrow_array();  
        if(scalar (@row)>0 &&$row[0]==1){
            $db->do("ALTER TABLE LOG RENAME COLUMN ID_RTF TO RTF;");           
        }        
    }
    #
    # From v.1.8 Log has changed, to have LOG to NOTES relation.
    #
    if($hasLogTbl && $SCRIPT_RELEASE > $DB_VERSION && $DB_VERSION < 1.8){
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
            if($DB_VERSION > 1.6){
                #is above v.1.6 notes table.
                $db->do('DROP TABLE '.Settings->VW_LOG);                
            }
            $db->do('DROP TABLE LOG;');
            #v.1.8 Has fixes, time also properly to take into the sort. Not crucial to drop.
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
                my $stmt= "UPDATE LOG SET RTF =". $nid." WHERE DATE == '".$date."';";
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
    elsif($hasLogTbl && $SCRIPT_RELEASE > $DB_VERSION && $DB_VERSION < 2.0){
        #dev 1.9 main log view has changed in 1.8..1.9, above scope will perform anyway, its drop, to be recreated later.
        $db->do('DROP VIEW '.Settings->VW_LOG);delete($curr_tables{Settings->VW_LOG});
        delete($curr_tables{Settings->VW_LOG});
        $changed = 1;
    }elsif($SCRIPT_RELEASE > $DB_VERSION){$changed = 1;}

    if(!$hasLogTbl) {

        if($sssCreatedDB){
            print $cgi->header, $cgi->start_html,
            q(<center><font color=red><b>A new alias login detect! <br>
            Server security measure has been triggered -> Sorry further new alias login/creation not allowed!</b>
            </font><br><br>Contact your network admin.</center>).$_,$cgi->end_html;
            exit;
        }

        $db->do(Settings::createLOGStmt());

        my $st = $db->prepare('INSERT INTO LOG(ID_CAT,DATE,LOG) VALUES (?,?,?)');        
           $st->execute( 3, Settings::today(), "DB Created!");            
           $session->param("cdb", "1");
    }

    # From v.1.6 view uses server side views, for pages and correct record by ID and PID lookups.
    # This should make queries faster, less convulsed, and log renumeration less needed for accurate pagination.
    if(!$curr_tables{Settings->VW_LOG}) {
        $db->do(Settings::createViewLOGStmt()) or LifeLogException -> throw("ERROR:".$@);
    }
    if(!$curr_tables{Settings->VW_LOG_WITH_EXCLUDES}) {
        # To cover all possible situations, this test elses too. 
        # As an older existing view might need to be recreated, to keep in synch.
        if($PAGE_EXCLUDES){
           $db->do(createPageViewExcludeSQL());
           Settings::configProperty($db, 204, '^PAGE_EXCLUDES',$PAGE_EXCLUDES);          
        }        
    }else{ # Updating here too if excludes in config file have been removed.
           my @ret=Settings::selectRecords($db, "SELECT value FROM CONFIG WHERE NAME='^PAGE_EXCLUDES';")->fetchrow_array();
           if(!$ret[0] && $PAGE_EXCLUDES){
               $db->do('DROP VIEW '.Settings->VW_LOG_WITH_EXCLUDES);
               $db->do(createPageViewExcludeSQL());
               Settings::configProperty($db, 204, '^PAGE_EXCLUDES',$PAGE_EXCLUDES);
               
           }elsif($ret[0]){
               if($PAGE_EXCLUDES && $PAGE_EXCLUDES ne $ret[0]){
                   $db->do('DROP VIEW '.Settings->VW_LOG_WITH_EXCLUDES);
                   $db->do(createPageViewExcludeSQL());
               }{
                   $db->do("DELETE FROM CONFIG WHERE NAME='^PAGE_EXCLUDES'");
               }
            }
    }

    if(!$curr_tables{'CAT'}) {
        $db->do(Settings::createCATStmt());
        $changed = 1;
    }else{
        # If empty something happened to it. It shouldn't be EMPTY!
        my @ret=Settings::selectRecords($db, "SELECT count(0) from CAT;")->fetchrow_array();
        $changed = 1 if (!$ret[0]);
    }
    #Have cats been wiped out?
    $changed = 1 if Settings::countRecordsIn($db, 'CAT') == 0;

    #TODO Future table for multiple cats per log if ever required.
    if(!$curr_tables{'LOGCATSREF'}) {
        $db->do(Settings::createLOGCATSREFStmt());
    }

    if(!$curr_tables{'AUTH'}) {
        $db->do(Settings::createAUTHStmt());
        my $st = $db->prepare('INSERT INTO AUTH VALUES (?,?,?,?);');
           $st->execute($alias, $passw,"",0);
           $st->finish();
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
    if(!$hasNotesTbl) {$db->do(Settings::createNOTEStmt())}

    if(Settings::isProgressDB()){        
        my @tbls = $db->tables(undef, 'public');
        foreach (@tbls){
            my $t = uc substr($_,7);
            $curr_tables{$t} = 1;
        }
        if(!$curr_tables{Settings->VW_LOG}) {
            LifeLogException -> throw(Settings->VW_LOG." not created! Try logging in again.");
        }
    }

    if($changed){
        #It is also good to run db fix (config page) to renum if this is an release update?
        #Release in software might not be what is in db, which counts.
        #This here next we now update.
        my @r = Settings::selectRecords($db, 'SELECT ID, VALUE FROM CONFIG WHERE NAME LIKE \'RELEASE_VER\';')->fetchrow_array();
        my $did = $r[0];
        my $dnm = $r[1];
        my $cmp = $dnm eq $SCRIPT_RELEASE;
        $DBG .= "Upgrade cmp(RELESE_VER:'$dnm' eq Settings::release:'$SCRIPT_RELEASE') ==  $cmp";
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
            Settings::configProperty($db, 200, '^REL_RENUM',$pv);
            Settings::configProperty($db, $did>0?$did:0, 'RELEASE_VER', $SCRIPT_RELEASE);
            Settings::toLog($db, "Upgraded Life Log from v.$dnm to v.$SCRIPT_RELEASE version, this is the $pv upgrade.") if $pv;
        }
        &populate($db);
    }
    Settings::toLog($db, "Log accessed by $alias.") if(Settings::trackLogins());
    #
     $db->disconnect();
    #
    #Still going through checking tables and data, all above as we might have an version update in code.
    #Then we check if we are login in intereactively back. Interective, logout should bring us to the login screen.
    #Bypassing auto login. So to start maybe working on another database, and a new session.
    return $cgi->param('autologoff') == 1;
}catch{
    LifeLogException -> throw(error=>$@,show_trace=>1);
}
}

sub createPageViewExcludeSQL {
    
    my ($where,$days) = 0;
    my $parse = $PAGE_EXCLUDES;
    my @a = split('=',$parse);
    if(scalar(@a)==2){
        $days  = $a[0];
        $parse = $a[1];
    }    
    if(Settings::isProgressDB()){$where = "WHERE a.date >= (timestamp 'now' - interval '$days days') OR"}
    else{$where = "WHERE a.date >= date('now', '-$days day') OR"}
    @a = split(',',$parse);
    foreach (@a){
        $where .= " ID_CAT!=$_ AND";
    }
    $where =~ s/\s+OR$//;
    $where =~ s/\s+AND$//;
    return Settings::createViewLOGStmt(Settings->VW_LOG_WITH_EXCLUDES,$where);
    
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

    my $cnfIns = 'INSERT INTO CONFIG (ID,NAME,VALUE,DESCRIPTION) VALUES (?,?,?,?)'; #for silly bckwrds compatbl;
       $cnfIns = 'INSERT INTO CONFIG (NAME,VALUE,DESCRIPTION) VALUES (?,?,?)' if(Settings::isProgressDB());
    my $insCnf = $db->prepare($cnfIns);
    my $insCat = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
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
                                                                            my @arr = Settings::selectRecords($db,"SELECT ID FROM CONFIG WHERE NAME LIKE '$name';")->fetchrow_array();                                                                                 
                                                                            $inData = 1;                                                                                
                                                                            if(!@arr) {
                                                                                $DBG .= "conf.ins->".$name.",".$value.",".$tick[1]."\n";
                                                                               if(Settings::isProgressDB()) {$insCnf->execute($name,$value,$tick[1])}
                                                                               else{$insCnf->execute($id,$name,$value,$tick[1])}
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
                                                                                $DBG .= "cat.ins->".$pair[0].",".$pair[1].",".$tick[1]."\n";
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

    if(Settings::trackLogins()){
    try{
        $alias = $session->param('alias');
        $passw = $session->param('passw');
        if($alias){
            my $db = Settings::connectDB($DB_NAME, $alias, $passw);
            Settings::toLog($db, "Log has properly been logged out by $alias.");
            $db->disconnect();
        }
    }catch{
        my $err = $@;
        my $dbg = "" ;
        my $pwd = `pwd`;
        $pwd =~ s/\s*$//;
        $dbg = "--DEBUG OUTPUT--\n$DBG" if Settings::debug();
        print $cgi->header,
        "<font color=red><b>SERVER ERROR</b></font> on ".DateTime->now().
        "<pre>".$pwd."/$0 -> &".caller." -> [$err]","\n$dbg</pre>",
        $cgi->end_html;
        exit;
    }
    }


    print $cgi->header(-expires=>"0s", -charset=>"UTF-8", -cookie=>$cookie);
    print $cgi->start_html(-title => "Personal Log Login", -BGCOLOR=>"black",
                           -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
            );

    print qq(<font color="white"><center><h2>You have properly logged out of the Life Log Application!</h2>
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
1;
### CGI END
