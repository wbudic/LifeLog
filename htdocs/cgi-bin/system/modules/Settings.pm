#!/usr/bin/perl -w
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
package Settings;

use v5.10;
use strict;
use warnings;
use Exception::Class ('SettingsException');
use Syntax::Keyword::Try;
use CGI;
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;

use DBI;
use experimental qw( switch );

#This is the default developer release key, replace on istallation. As it is not secure.
use constant CIPHER_KEY => '95d7a85ba891da';

#DEFAULT SETTINGS HERE!
our $RELEASE_VER  = '2.1';
our $TIME_ZONE    = 'Australia/Sydney';
our $LANGUAGE     = 'English';
our $PRC_WIDTH    = '60';
our $LOG_PATH     = '../../dbLifeLog/';
our $SESSN_EXPR   = '+30m';
our $DATE_UNI     = '0';
our $AUTHORITY    = '';
our $IMG_W_H      = '210x120';
our $REC_LIMIT    = 25;
our $AUTO_WRD_LMT = 1000;
our $AUTO_WRD_LEN = 17; #Autocompletion word length limit. Internal.
our $VIEW_ALL_LMT = 1000;
our $DISP_ALL     = 1;
our $FRAME_SIZE   = 0;
our $RTF_SIZE     = 0;
our $THEME        = 'Standard';
our $TRACK_LOGINS = 1;
our $KEEP_EXCS    = 0;
our $COMPRESS_ENC = 0; #HTTP Compressed encoding.
our $DBI_SOURCE   = "DBI:SQLite:";
our $DSN;
our $DBFILE;
our $IS_PG_DB     = 0;

my ($cgi, $sss, $sid, $alias, $pass, $dbname, $pub);


#Annons here, variables that could be overiden in  code or database, per need.
our %anons = ();
our %tz_map;

### Page specific settings Here
our $TH_CSS        = 'main.css';
our $BGCOL         = '#c8fff8';
#Set to 1 to get debug help. Switch off with 0.
our $DEBUG         = 1;
#END OF SETTINGS

### Private Settings sofar (id -> name : def.value):
#200 -> '^REL_RENUM' : this.$RELEASE_VER (Used in login_ctr.cgi)
#201 -> '^EXCLUDES'  : 0 (Used in main.cgi)

our $SQL_PUB = undef;

sub anons {my @ret=sort(keys %anons); return @ret;}
#Check call with defined(Settings::anon('my_anon'))
sub anon {my $n=shift; return $anons{$n}}
sub anonsSet {my $a = shift;%anons=%{$a}}

sub release        {return $RELEASE_VER}
sub logPath        {return $LOG_PATH}
sub theme          {return $THEME}
sub language       {return $LANGUAGE}
sub timezone       {return $TIME_ZONE}
sub sessionExprs   {return $SESSN_EXPR}
sub imgWidthHeight {return $IMG_W_H}
sub pagePrcWidth   {return $PRC_WIDTH}
sub frameSize      {return $FRAME_SIZE}
sub universalDate  {return $DATE_UNI;}
sub recordLimit    {return $REC_LIMIT}
sub autoWordLimit  {return $AUTO_WRD_LMT}
sub autoWordLength {return $AUTO_WRD_LEN}
sub viewAllLimit   {return $VIEW_ALL_LMT}
sub displayAll     {return $DISP_ALL}
sub trackLogins    {return $TRACK_LOGINS}
sub windowRTFSize  {return $RTF_SIZE}
sub keepExcludes   {return $KEEP_EXCS}
sub bgcol          {return $BGCOL}
sub css            {return $TH_CSS}
sub compressPage   {return $COMPRESS_ENC}
sub debug          {my $r = shift; if(!$r){$r = $DEBUG}else{$DEBUG=$r}  return $r}
sub dbSrc          {my $r = shift; if($r) {$DBI_SOURCE=$r; $IS_PG_DB = 1 if(index (uc $r, 'DBI:PG') ==0)}  
                    return $DBI_SOURCE}
sub dbFile         {my $r = shift; if($r) {$DBFILE=$r} return $DBFILE}
sub dbName         {return $dbname;}
sub dsn            {return $DSN}
sub isProgressDB   {return $IS_PG_DB}
sub sqlPubors      {return $SQL_PUB}

sub trim {my $r=shift; $r=~s/^\s+|\s+$//g; return $r}

sub fetchDBSettings {
try {
    $CGI::POST_MAX = 1024 * 1024 * 5;  # max 5GB file post size limit.
    $cgi     = CGI->new();    
    $sss     = new CGI::Session("driver:File", $cgi, {Directory=>$LOG_PATH});
    $sid     = $sss->id();
    $dbname  = $sss->param('database');
    $alias   = $sss->param('alias');
    $pass    = $sss->param('passw');
    $pub     = $cgi->param('pub');
    if($pub){#we override session to obtain pub(alias)/pass from file main config.
        open(my $fh, '<', logPath().'main.cnf' ) or LifeLogException->throw("Can't open main.cnf: $!");        
        while (my $line = <$fh>) {
                    chomp $line;
                    my $v = Settings::parseAutonom('PUBLIC_LOGIN',$line);
                    if($v){my @cre = split '/', $v; 
                           $alias = $cre[0];                           
                           $pass = uc crypt $cre[1], hex Settings->CIPHER_KEY;
                    }                    
                       $v = Settings::parseAutonom('PUBLIC_CATS',$line);
                    if($v){my @cats= split(',',$v);
                        foreach(@cats){
                            $SQL_PUB .= "ID_CAT=".trim($_)." OR ";
                        }
                        $SQL_PUB =~ s/\s+OR\s+$//;
                    }
                    last if Settings::parseAutonom('CONFIG',$line);
        }
        close $fh; 
        if(!$SQL_PUB){$alias=undef}       
    }
    if(!$alias){
        print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
        exit;
    }
    ##From here we have data source set, currently Progress DB SQL and SQLite SQL compatible.
    dbSrc($sss->param('db_source'));
    my $ret  = connectDB($alias, $pass);
    getConfiguration($ret);
    
    getTheme();
    $sss->expire($SESSN_EXPR);
    return $ret;
}catch{    
    SettingsException->throw(error=>$@, show_trace=>$DEBUG);
    exit;
}
}
sub cgi     {return $cgi}
sub session {return $sss}
sub sid     {return $sid}
sub dbname  {return $dbname}
sub alias   {return $alias}
sub pass    {return $pass}
sub pub     {return $pub}

sub today {
    my $ret = DateTime->now();
    if(!$anons{'auto_set_timezone'}){
       setTimezone($ret);
    }       
    return $ret;
}

sub setTimezone {    
    my $ret = shift;
    my $to  = shift; #optional for testing purposes.
    my $v= $anons{'TIME_ZONE_MAP'};
    if($v){
       if(!%tz_map){
           %tz_map={}; chomp($v);
           foreach (split('\n',$v)){
             my @p = split('=', $_);
             $tz_map{trim($p[0])} = trim($p[1]);
           }
       }
       if($to){$v = $tz_map{$to};}else{$v = $tz_map{$TIME_ZONE};}      
       if($v){$TIME_ZONE=$v}
    }
    $ret = DateTime->now() if(!$ret);
    $ret -> set_time_zone($TIME_ZONE);
    return $ret;
}

sub createCONFIGStmt {
if($IS_PG_DB){return qq(
    CREATE TABLE CONFIG(
        ID INT NOT NULL UNIQUE GENERATED BY DEFAULT AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
        NAME VARCHAR(28)  UNIQUE,
        VALUE             VARCHAR(28),
        DESCRIPTION       VARCHAR(128),
        PRIMARY KEY(ID)
    );
    CREATE INDEX idx_config_name ON CONFIG (NAME);
)}

return qq(
    CREATE TABLE CONFIG(
        ID INT  PRIMARY KEY NOT NULL,
        NAME VCHAR(16)  UNIQUE,
        VALUE VCHAR(28),
        DESCRIPTION VCHAR(128)
    );
    CREATE INDEX idx_config_name ON CONFIG (NAME);
)
}
sub createCATStmt {

if($IS_PG_DB){
    return qq(    
    CREATE TABLE CAT(
        ID INT             GENERATED BY DEFAULT AS IDENTITY,
        NAME               VARCHAR(16),
        DESCRIPTION        VARCHAR(225),
        PRIMARY KEY(ID)
    );
    CREATE INDEX idx_cat_name ON CAT (NAME);
)}

return qq(    
    CREATE TABLE CAT(
        ID INT             PRIMARY KEY NOT NULL,
        NAME               VARCHAR(16),
        DESCRIPTION        VARCHAR(225)
    );
    CREATE INDEX idx_cat_name ON CAT (NAME);
)}
sub createLOGStmt {
if($IS_PG_DB){
  return qq(
    CREATE TABLE LOG (
        ID INT UNIQUE GENERATED ALWAYS AS IDENTITY,
        ID_CAT INT        NOT NULL,
        ID_RTF INTEGER    DEFAULT 0,
        DATE TIMESTAMP    NOT NULL,
        LOG VARCHAR (128) NOT NULL,
        AMOUNT INTEGER,
        AFLAG INT         DEFAULT 0,
        STICKY BOOL       DEFAULT FALSE,
        PRIMARY KEY(ID)
    );)
} 
  return qq(
    CREATE TABLE LOG (
        ID_CAT INT        NOT NULL,
        ID_RTF INTEGER    DEFAULT 0,
        DATE DATETIME     NOT NULL,
        LOG VARCHAR (128) NOT NULL,
        AMOUNT INTEGER,
        AFLAG INT         DEFAULT 0,
        STICKY BOOL       DEFAULT 0
    );
)}

sub selLogIDCount {
    if($IS_PG_DB){return 'select count(ID) from LOG;'}
    return 'select count(rowid) from LOG;'
}

sub selStartOfYear {
    if($IS_PG_DB){return "date>= date_trunc('year', now())"}
    return "date>=date('now','start of year')"
}

sub createViewLOGStmt {
if($IS_PG_DB){
  return qq(
    CREATE VIEW VW_LOG AS
     SELECT *, (select count(ID) from LOG as recount where a.id >= recount.id) as PID
         FROM LOG as a ORDER BY Date(DATE) DESC;
    );
} 
return qq(
CREATE VIEW VW_LOG AS
    SELECT rowid as ID,*, (select count(rowid) from LOG as recount where a.rowid >= recount.rowid) as PID
        FROM LOG as a ORDER BY Date(DATE) DESC, Time(DATE) DESC;
)}

sub createAUTHStmt {

if($IS_PG_DB){
  return qq(
    CREATE TABLE AUTH(
        ALIAS varchar(20)   PRIMARY KEY,
        PASSW TEXT,
        EMAIL               varchar(44),
        ACTION INT
    );
    CREATE INDEX idx_auth_name_passw ON AUTH (ALIAS, PASSW);      
)}
return qq(
    CREATE TABLE AUTH(
        ALIAS varchar(20)   PRIMARY KEY,
        PASSW TEXT,
        EMAIL               varchar(44),
        ACTION INT
    ) WITHOUT ROWID;
    CREATE INDEX idx_auth_name_passw ON AUTH (ALIAS, PASSW);
)}



sub createNOTEStmt {
    return qq(CREATE TABLE NOTES (LID INT PRIMARY KEY NOT NULL, DOC TEXT);)
}
sub createLOGCATSREFStmt {
if($IS_PG_DB){
return qq(
    CREATE TABLE LOGCATSREF (
        LID INT NOT NULL,
        CID INT NOT NULL,
		primary key(LID)		
    );    
)}
# CONSTRAINT fk_log  FOREIGN KEY(LID) REFERENCES LOG(ID) ON DELETE CASCADE, 
# CONSTRAINT fk_cats FOREIGN KEY(CID) REFERENCES CAT(ID) ON DELETE CASCADE 
return qq(
    CREATE TABLE LOGCATSREF (
        LID INT NOT NULL,
        CID INT NOT NULL,
    FOREIGN KEY (LID) REFERENCES LOG(ID),
    FOREIGN KEY (CID) REFERENCES CAT(ID)
    );
)}

sub getConfiguration {
    my ($db, $hsh) = @_;
    try {
        my $st = $db->prepare("SELECT ID, NAME, VALUE FROM CONFIG;");
           $st->execute();
        while ( my @r = $st->fetchrow_array() ){
                given ( $r[1] ) {
                when ("RELEASE_VER") {$RELEASE_VER  = $r[2]}
                when ("TIME_ZONE")   {$TIME_ZONE    = $r[2]}
                when ("PRC_WIDTH")   {$PRC_WIDTH    = $r[2]}
                when ("SESSN_EXPR")  {$SESSN_EXPR   = $r[2]}
                when ("DATE_UNI")    {$DATE_UNI     = $r[2]}
                when ("LANGUAGE")    {$LANGUAGE     = $r[2]}
                when ("LOG_PATH")    {} #ommited and code static can't change for now.
                when ("IMG_W_H")     {$IMG_W_H      = $r[2]}
                when ("REC_LIMIT")   {$REC_LIMIT    = $r[2]}
                when ("AUTO_WRD_LMT"){$AUTO_WRD_LMT = $r[2]}
                when ("VIEW_ALL_LMT"){$VIEW_ALL_LMT = $r[2]}
                when ("DISP_ALL")    {$DISP_ALL     = $r[2]}
                when ("FRAME_SIZE")  {$FRAME_SIZE   = $r[2]}
                when ("RTF_SIZE")    {$RTF_SIZE     = $r[2]}
                when ("THEME")       {$THEME        = $r[2]}
                when ("DEBUG")       {$DEBUG        = $r[2]}
                when ("KEEP_EXCS")   {$KEEP_EXCS    = $r[2]}
                when ("TRACK_LOGINS"){$TRACK_LOGINS = $r[2]}
                when ("COMPRESS_ENC"){$COMPRESS_ENC = $r[2]}                
                default              {$anons{$r[1]} = $r[2]}
                }
        }
        #Anons are murky grounds. -- @bud
        if($hsh){
            my $stIns = $db->prepare("INSERT INTO CONFIG (ID, NAME, VALUE, DESCRIPTION) VALUES(?,?,?,?)");
            foreach my $key (keys %{$hsh}){
                if(index($key,'$')!=0){#per spec. anons are not prefixed with an '$' as signifier.
                    my $val = %{$hsh}{$key};
                    my $existing = $anons{$key};
                    #exists? Overwrite for $self config but not in DB! (dynamic code base set anon)
                    $anons{$key} = $val;
                    if(not defined $existing){
                        #Make it now config global. Note another source latter calling this subroutine
                        #can overwrite this, but not in the database. Where it is now set by the following.
                        #Find free ID.
                        my @res = selectRecords($db,"SELECT MAX(ID) FROM CONFIG;")->fetchrow_array();
                        #ID's under 300 are reserved, for constants.
                        my $id = $res[0]+1;
                        while($id<300){ $id += ($id*1.61803398875); }#Golden ratio step it to best next available.
                        $stIns->execute(int($id), $key, $val, "Anonymous application setting.");
                    }
                }
            }
        }
    }
    catch {
        SettingsException->throw(error=>$@, show_trace=>$DEBUG);
    };
}


sub getTheme {
    given ($THEME){
        when ("Sun")   { $BGCOL = '#D4AF37'; $TH_CSS = "main_sun.css"; }
        when ("Moon")  { $BGCOL = '#000000'; $TH_CSS = "main_moon.css"; }
        when ("Earth") { $BGCOL = '#26ac0c'; $TH_CSS = "main_earth.css";} # Used to be $BGCOL = '#26be54';
        default{
            # Standard;
            $BGCOL    = '#c8fff8';
            $TH_CSS   = 'main.css';
        }
    }
}

#From v.1.8 Changed
sub renumerate {
    my $db = shift;
    #Renumerate Log! Copy into temp. table.
    my $sql;
    selectRecords($db,'CREATE TABLE life_log_temp_table AS SELECT * FROM LOG;');
    my $CI = 'rowid'; $CI = 'ID' if $IS_PG_DB;
    #update  notes table with new log id only for reference sake.
    my $st = selectRecords($db, "SELECT $CI, DATE FROM LOG WHERE ID_RTF > 0 ORDER BY DATE;");
    while(my @row =$st->fetchrow_array()) {
        my $sql_date = $row[1];
        #$sql_date =~ s/T/ /;
        $sql_date = DateTime::Format::SQLite->parse_datetime($sql_date);
        $sql = "SELECT $CI, DATE FROM life_log_temp_table WHERE ID_RTF > 0 AND DATE = '".$sql_date."';";
        my @new  = selectRecords($db, $sql)->fetchrow_array();
        if(scalar @new > 0){
             try{#can fail here, for various reasons.
                $sql="UPDATE NOTES SET LID =". $new[0]." WHERE LID==".$row[0].";";
                $db->do($sql);
             }
             catch{
                 SettingsException->throw(error=>"Database error encountered. sql->$sql", show_trace=>$DEBUG);
             };
        }
    }

    # Delete any possible orphaned Notes records.
    $st->finish();
    $st = selectRecords($db, "SELECT LID, LOG.$CI from NOTES LEFT JOIN LOG ON NOTES.LID = LOG.$CI WHERE LOG.$CI is NULL;");
    while($st->fetchrow_array()) {
        $db->do("DELETE FROM NOTES WHERE LID=".$_[0].";")
    }
    $st->finish();
    if($IS_PG_DB){$db->do('DROP TABLE LOG CASCADE;');}else{$db->do('DROP TABLE LOG;');}
    
    $db->do(&createLOGStmt);
    $db->do('INSERT INTO LOG (ID_CAT, ID_RTF, DATE, LOG, AMOUNT,AFLAG,STICKY)
                       SELECT ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY FROM life_log_temp_table ORDER by DATE;');    
    $db->do('DROP TABLE life_log_temp_table;');
}

sub selectRecords {
    my ($db, $sql) = @_;
    if(scalar(@_) < 2){
                SettingsException->throw("ERROR Argument number is wrong->db is:$db\n", show_trace=>$DEBUG);
    }
    try{
                my $pst	= $db->prepare($sql);
                $pst->execute();
                return 0 if(!$pst);
                return $pst;
    }catch{
                SettingsException->throw(error=>"Database error encountered!\n ERROR->".$@." SQL-> $sql DSN:".$DSN, show_trace=>$DEBUG);
    };
}

sub getTableColumnNames {
        my ($db, $table_name) = @_;
        if(scalar(@_) < 2){
                SettingsException->throw("ERROR Argument number is wrong->db is:$db\n", show_trace=>$DEBUG);
        }
        
        my $pst = selectRecords($db, "SELECT name FROM PRAGMA_table_info('$table_name');");
        my @ret = ();
        while(my @r = $pst->fetchrow_array()){
            push @ret, $r[0];
        }
        
}

sub printDebugHTML {
    my $msg = shift;
    print qq(<!-- $msg -->);
}

sub toLog {
    my ($db,$log,$cat) = @_;
    my $stamp = getCurrentSQLTimeStamp();
        if(!$cat){
            my @arr = selectRecords($db,"SELECT ID FROM CAT WHERE NAME LIKE 'System Log' or NAME LIKE 'System';")->fetchrow_array();
            if(@arr){$cat = $arr[0];}else{$cat = 6;}
        }
       $log =~ s/'/''/g;
       $db->do("INSERT INTO LOG (ID_CAT, DATE, LOG) VALUES($cat,'$stamp', '$log');");
}

sub countRecordsIn {
    my ($db,$name) = @_;
     if(scalar(@_) < 2){
        SettingsException->throw("ERROR Argument number is wrong.name:$name\n", show_trace=>$DEBUG);
    }
    my $ret = selectRecords($db, "SELECT count(ID) FROM $name;");
    if($ret){
       $ret ->fetchrow_array();
       $ret = 0 if not $ret;
    }
    return $ret;
}

sub getCurrentSQLTimeStamp {
     my $dt;
     if(anon('auto_set_timezone')){$dt = DateTime->from_epoch(epoch => time())}
     else{                         $dt = DateTime->from_epoch(epoch => time(), time_zone=> $TIME_ZONE)}     
     # 20200225  Found that SQLite->format_datetime, changes internally to UTC timezone, which is wrong.
     # Strange that this format_datetime will work from time to time, during day and some dates. (A Pitfall)
    #return DateTime::Format::SQLite->format_datetime($dt);
    return join ' ', $dt->ymd('-'), $dt->hms(':');
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

sub obtainProperty {
    my($db, $name) = @_;
    SettingsException->throw("Invalid use of subroutine obtainProperty($db, $name)", show_trace=>$DEBUG) if(!$db || !$name);
    my $dbs = selectRecords($db, "SELECT ID, VALUE FROM CONFIG WHERE NAME LIKE '$name';");
    my @row = $dbs->fetchrow_array();
    if(scalar @row > 0){
       return $row[1];
    }
    else{
       return 0;
    }
}

sub configProperty {
    my($db, $id, $name, $value) = @_;
    $id = '0' if not $id;
    if($db eq undef || $value eq undef){
        SettingsException->throw(
            error => "ERROR Invalid number of arguments in call -> Settings::configProperty('$db',$id,'$name','$value')\n",  show_trace=>$DEBUG
            );
    };
    if($name eq undef && $id){

        my $sql = "UPDATE CONFIG SET VALUE='".$value."' WHERE ID=".$id.";";
        try{
            $db->do($sql);
        }
        catch{

            SettingsException->throw(
                error => "ERROR with $sql -> Settings::configProperty('$db',$id,'$name','$value')\n",
                show_trace=>$DEBUG
                );
        }
    }
    else{
        my $dbs = selectRecords($db, "SELECT ID, NAME FROM CONFIG WHERE NAME LIKE '$name';");
        if($dbs->fetchrow_array()){
            $db->do("UPDATE CONFIG SET VALUE = '$value' WHERE NAME LIKE '$name';");
        }
        else{
            my $sql = "INSERT INTO CONFIG (ID, NAME, VALUE) VALUES ($id, '$name', '$value');";
            try{
                $db->do($sql);
            }
            catch{

                SettingsException->throw(
                    error => "ERROR $@ with $sql -> Settings::configProperty('$db',$id,'$name','$value')\n",
                    show_trace=>$DEBUG
                    );
            }
        }
    }
}

sub connectDB {
    my ($a,$p) = @_;
    $a = $alias if(!$a);
    $p = $alias if(!$p);
    $dbname = 'data_'.$a.'_log.db';
    $DBFILE = $LOG_PATH.$dbname if(!$DBFILE);    
    if ($IS_PG_DB)  {
        $DSN = $DBI_SOURCE .'dbname='.$a; $DBFILE = $a;        
    }else{
        $DSN = $DBI_SOURCE .'dbname='.$DBFILE;        
    }
    try{
        return DBI->connect($DSN, $a, $p, {AutoCommit => 1, RaiseError => 1, PrintError => 0, show_trace=>1});
    }catch{
           LifeLogException->throw(error=>"<p>Error->$@</p>",  show_trace=>1);
    }
}

sub parseAutonom { #Parses autonom tag for its crest value, returns undef if tag not found or wrong for passed line.
    my $t = '<<'.shift.'<';
    my $line = shift;
    if(rindex ($line, $t, 0)==0){#@TODO change the following to regex parsing:
        my $l = length $t;
        my $e = index $line, ">", $l + 1;
        return substr $line, $l, $e - $l;
    }
    return;
}

1;