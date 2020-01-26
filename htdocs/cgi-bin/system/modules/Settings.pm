#!/usr/bin/perl -w
package Settings;

use strict;
use warnings;
use Switch;

use DBI;

#DEFAULT SETTINGS HERE!
our $RELEASE_VER  = '1.7';
our $REC_LIMIT    = 25;
our $TIME_ZONE    = 'Australia/Sydney';
our $LANGUAGE     = 'English';
our $PRC_WIDTH    = '60';
our $LOG_PATH     = '../../dbLifeLog/';
our $SESSN_EXPR   = '+30m';
our $DATE_UNI     = '0';
our $AUTHORITY    = '';
our $IMG_W_H      = '210x120';
our $AUTO_WRD_LMT = 1000;
our $FRAME_SIZE   = 0;
our $RTF_SIZE     = 0;
our $THEME        = 'Standard';
our $KEEP_EXCS    = 0;

### Page specific settings Here
our $TH_CSS        = 'main.css';
our $BGCOL         = '#c8fff8';
#Set to 1 to get debug help. Switch off with 0.
our $DEBUG         = 0;
#END OF SETTINGS


### Private Settings sofar (id -> name : def.value):
#200 -> '^REL_RENUM' : this.$RELEASE_VER (Used in login_ctr.cgi)
#201 -> '^EXCLUDES'  : 0 (Used in main.cgi)




sub new {
    return bless {}, shift;
}
sub release        {return $RELEASE_VER;}
sub logPath        {return $LOG_PATH;}
sub theme          {return $THEME;}
sub language       {return $LANGUAGE;}
sub timezone       {return $TIME_ZONE;}
sub sessionExprs   {return $SESSN_EXPR;}
sub imgWidthHeight {return $IMG_W_H;}
sub pagePrcWidth   {return $PRC_WIDTH;}
sub recordLimit    {return $REC_LIMIT;}
sub frameSize      {return $FRAME_SIZE;}
sub universalDate  {return $DATE_UNI;}
sub autoWordLimit  {return $AUTO_WRD_LMT;}
sub windowRTFSize  {return $RTF_SIZE;}
sub keepExcludes   {return $KEEP_EXCS;}
sub bgcol          {return $BGCOL;}
sub css            {return $TH_CSS;}
sub debug          {my $ret=shift; if($ret){$DEBUG = $ret;}; return $DEBUG;}



sub getConfiguration {
    my $db = shift;
    try {
        my $st = $db->prepare("SELECT ID, NAME, VALUE FROM CONFIG;");
        $st->execute();

        while ( my @r = $st->fetchrow_array() ) {

            switch ( $r[1] ) {
                case "RELEASE_VER"  { $RELEASE_VER  = $r[2] }
                case "REC_LIMIT"    { $REC_LIMIT    = $r[2] }
                case "TIME_ZONE"    { $TIME_ZONE    = $r[2] }
                case "PRC_WIDTH"    { $PRC_WIDTH    = $r[2] }
                case "SESSN_EXPR"   { $SESSN_EXPR   = $r[2] }
                case "DATE_UNI"     { $DATE_UNI     = $r[2] }
                case "LANGUAGE"     { $LANGUAGE     = $r[2] }
                case "IMG_W_H"      { $IMG_W_H      = $r[2] }
                case "AUTO_WRD_LMT" { $AUTO_WRD_LMT = $r[2] }
                case "FRAME_SIZE"   { $FRAME_SIZE   = $r[2] }
                case "RTF_SIZE"     { $RTF_SIZE     = $r[2] }
                case "THEME"        { $THEME        = $r[2] }
                case "DEBUG"        { $DEBUG        = $r[2] }
                case "KEEP_EXCS"    { $KEEP_EXCS    = $r[2] }
            }

        }
        return &new;
    }
    catch {
        print "<font color=red><b>SERVER ERROR</b></font>:" . $_;
    }
}


sub getTheme {

        switch ($THEME){
            case "Sun"   { $BGCOL = '#D4AF37'; $TH_CSS = "main_sun.css"; }
            case "Moon"  { $BGCOL = '#000000'; $TH_CSS = "main_moon.css"; }
            case "Earth" { $BGCOL = '#26be54'; $TH_CSS = "main_earth.css"; }
            else{
                # Standard;
                $BGCOL    = '#c8fff8';
                $TH_CSS   = 'main.css';
            }
        }

}


sub renumerate {
    my $db = shift;
    #Renumerate Log! Copy into temp. table.
    my $sql;
    my $dbs = dbExecute($db, 'CREATE TABLE life_log_temp_table AS SELECT * FROM LOG;');
       $dbs = dbExecute($db, 'SELECT rowid, DATE FROM LOG WHERE RTF == 1 ORDER BY DATE;');
    #update  notes with new log id
    while(my @row = $dbs->fetchrow_array()) {
        my $sql_date = $row[1];
        #$sql_date =~ s/T/ /;
        $sql_date = DateTime::Format::SQLite->parse_datetime($sql_date);
        $sql = "SELECT rowid, DATE FROM life_log_temp_table WHERE RTF = 1 AND DATE = '".$sql_date."';";
        $dbs = dbExecute($db, $sql);
        my @new  = $dbs->fetchrow_array();
        if(scalar @new > 0){
            $db->do("UPDATE NOTES SET LID =". $new[0]." WHERE LID==".$row[0].";");
        }
    }

    # Delete Orphaned Notes entries.
    $dbs = dbExecute($db, "SELECT LID, LOG.rowid from NOTES LEFT JOIN LOG ON
                                    NOTES.LID = LOG.rowid WHERE LOG.rowid is NULL;");
    while(my @row = $dbs->fetchrow_array()) {
        $db->do("DELETE FROM NOTES WHERE LID=$row[0];");
    }
    $dbs = dbExecute($db, 'DROP TABLE LOG;');
    $dbs = dbExecute($db, qq(CREATE TABLE LOG (
                            ID_CAT TINY        NOT NULL,
                            DATE   DATETIME    NOT NULL,
                            LOG    VCHAR (128) NOT NULL,
                            AMOUNT INTEGER,
                            AFLAG TINY DEFAULT 0,
                            RTF BOOL DEFAULT 0,
                            STICKY BOOL DEFAULT 0
                            );));
    $dbs = dbExecute($db, 'INSERT INTO LOG (ID_CAT,DATE,LOG,AMOUNT,AFLAG, RTF)
                                    SELECT ID_CAT, DATE, LOG, AMOUNT, AFLAG, RTF
                                    FROM life_log_temp_table ORDER by DATE;');
    $dbs = dbExecute($db, 'DROP TABLE life_log_temp_table;');
}

sub dbExecute {
    my ($db,$sql) = @_;
    my $ret	= $db->prepare($sql);
       $ret->execute() or die "<p>ERROR with->$sql</p>";
    return $ret;
}

sub printDebugHTML {
    my $msg = shift;
    print qq(<!-- $msg -->);
}

sub toLog {
    my ($db,$stamp,$log) = @_;
    # try {
        #Apostrophe in the log value is doubled to avoid SQL errors.
        $log =~ s/'/''/g;
        $db->do("INSERT INTO LOG (ID_CAT, DATE, LOG) VALUES(6,'$stamp', \"$log\");");
    # }
    # catch {
    #     print "<font color=red><b>SERVER ERROR toLog(6,$stamp,$log)</b></font>:" . $_;
    # }
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


#TODO move this subroutine to settings.
sub obtainProperty {
    my($db, $name) = @_;
    die "Invalid use of subroutine obtainProperty($db, $name)" if(!$db || !$name);
    my $dbs = Settings::dbExecute($db, "SELECT ID, VALUE FROM CONFIG WHERE NAME IS '$name';");
    my @row = $dbs->fetchrow_array();
    if(scalar @row > 0){
       return $row[1];
     }
     else{
       return 0;
     }
}
#TODO move this subroutine to settings.
sub configProperty {
    my($db, $id, $name, $value) = @_;
    die "Invalid use of subroutine configProperty($db,$name,$value)" if(!$db || !$name|| !$value);

    my $dbs = Settings::dbExecute($db, "SELECT ID, NAME FROM CONFIG WHERE NAME IS '$name';");
    if($dbs->fetchrow_array()){
       Settings::dbExecute($db, "UPDATE CONFIG SET VALUE = '$value' WHERE NAME IS '$name';");
    }
    else{
       Settings::dbExecute($db,"INSERT INTO CONFIG (ID, NAME, VALUE) VALUES ($id, '$name', '$value');");
    }
}

1;