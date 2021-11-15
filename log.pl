#!/usr/bin/perl -w
#
# Server side command line logging utility.
# Use to log entries to an database, without having to access via browser.
# 
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use v5.14;
use feature 'switch';

use warnings;
use strict;
no warnings ('portable', 'once');

use lib $ENV{'PWD'}.'/htdocs/cgi-bin/system/modules';

require CNFParser;
require Settings;
$CGI::Carp::WRAP = 0;     

use Exception::Class ('LifeLogException');
use DBI;
use IO::Prompter [ -stdio, -style=>'bold' ];

my $cnf = CNFParser->new('dbLifeLog/main.cnf');

my $TITLE = "LifeLog Command Line Access Utility (".Settings::release().")";
my $LIMIT = 100; 
my $LIMIT_REC = Settings::viewAllLimit();
my ($VW_NAME,$COL_NAME,$COL_TYPE, $SELECT, $INSERT);

my $help = qq(
$TITLE\n
Syntax: $0 {-option} {value}...{-dump}={file.log} | {-dump} {dump.log}\n
Arguments:
-database   - Database name (usually same as the alias).
-system     - Automatically login from anon property <<AUTO_LOGIN</> which has to be set in the main.inf.
            - Options -database and -alias are ignored if this flag is set.
-db_src     - (Optional) Driver source, defaults to <<DBI_SOURCE<DBI:SQLite:> set in main.cnf.            
-sys_table  - Create/Use sys table, for the logs. Format: -sys_table=table_name:col_name:sql_type.
            - i.e. -sys_table=BITCOIN:VALUE:NUMBER  or -sys_table=MESSAGES:MSG:TEXT
            - The -system option, all previous mentioned, don't need to be set as this overrides and implies when this option is set.
    -insert - (Optional) Similar to -log, value for the sys_table.
	-list       - List by category entries we are not logging. Next argument can be a single or list of catecory id's.
		    - i.e. -list '1:6:9' or just -list to list all categories up to 10.
-alias      - alias for login into database.            
-cat_id     - (Optional) New log entry category id. Will be prompted for if not provided.
-log        - (Optional) Log message or text to be logged is next argument.
-uvar       - (Optional) Reads in an user variable for the insert value.

This program requires an interactive shell, for unspeciefied but required arguments will be terminal asked, i.e password. 
Piping to this program is not anymore being supported.

	Limitations:
	    Currently date based entries are not possible to be added, and it is not recomended to use this utility for batch processing. 
	    To access any LifeLog based database, password has to be entered in the terminal. Can be bypassed with -system option flag.
	    There is a limit to log message size to $LIMIT_REC characters (can't be changed).
	    There is a limit of data presented and dumped to a \$LIMIT=$LIMIT of entries (modify in $0 to \$LIMIT=\"\"; if you want unlimited).
	    Data dumps are only by category from the latest entry as returned by the view of VW_LOG.
    Examples:
    $0 -db_src "DBI:Pg:host=localhost;" -database lifelog -sys_table=BITCOIN:VALUE:INTEGER

    The following -nbuilt can be used by modifying this perl file (not recommended):
    ./log.pl -inbuilt

    The following will put into LOF field an current user variable, the table REMOTE_MONITOR will be created if it doesn't exists.
    ./log.pl -system -sys_table REMOTE_MONITOR:LOG:VARCHAR(1024) -uvar LAST_MONITOR_READING

    The following selects an externaly created view AVG_BITCOIN and greps the data as output only:
    $0 -database lifelog -list 01:2:3
    -db_src "DBI:Pg:host=localhost;" -database lifelog -sys_table=AVG_BITCOIN -list -system | grep "|"
    Result:
    46804.49|Avg: 46804.49|Min: 44321|Max: 48043|

);


	my ($database, $alias, $passw, $db_source, $set, $insert, $table, $cat_id,$list, $dump, $out) = 0;
	my ($IS_PG_DB, $DSN, $DBFILE);
	my $LOG_PATH = "dbLifeLog/";
    my $log;
  
	foreach my $arg(@ARGV){
	    #print "{{{$arg}}}"; 
	    if($arg =~ /^\-/){
                if   ($arg=~/(^\-*\?)/){print $help; exit}  
                elsif($arg=~/(^\-*database)/){$set=1;}
                elsif($arg=~/(^\-*alias)/){$set=2;}
                elsif($arg=~/(^\-*db_src)/){$set=3;}
                elsif($arg=~/(^\-*c.*)/){$set=4;}
                elsif($arg=~/(^\-*log)/){$set=5;}
                elsif($arg=~/(^\-*list)/){$set=6;$list=-1}
                elsif($arg=~/(^\-*dump)/){
                    foreach(split /=/, $arg){
                      $dump = $_; 
                      if($dump =~ m/^~\//) {
                                   $dump =~ s/~/$ENV{'HOME'}/
                      }
                    }
                    if($dump && $dump !~ /(^\-*dump)/){$out = "You have set log output file to -> $dump\n"}else{$set=7}
                }
                elsif($arg=~/(^\-*system)/){$set = 8; $passw = $database}
                elsif($arg=~/(^\-*sys_table)/){$set = 9; foreach(split /=/, $arg){$table = $_;}
                    if($table && $table =~ /(^\-*sys_table)/){$table = undef}
                }
                elsif($arg=~/(^\-*insert)/){$set = 10;}
                elsif($arg=~/(^\-uvar)/)   {$set = 11;}
                elsif($arg=~/(^\-*inbuilt)/){
                    # Use Inbuild here and configurate here in perl script. Why not?
                    # Tip - Setup main.inf and login with bellow creadentials, to create the lifelog database.
                    $db_source = "DBI:Pg:host=localhost;";
                    $database  = "lifelog";
                    $alias     = "lifelog";
                    $passw     = "lifelog";
                    $table     = "BITCOIN:VALUE:INTEGER";
                }
	    }elsif($arg ne $ENV{'HOME'}){          

                if($arg=~/^\w+\./){
                    print "Ignoring -> $arg\n"; 
                    next;
                }
                next if ! $set;
                if   ($set == 1 ){$database = $arg}
                elsif($set == 2 ){$alias = $arg}
                elsif($set == 3 ){$db_source = $arg}
                elsif($set == 4 ){$cat_id = $arg}
                elsif($set == 5 ){$log = $arg}
                elsif($set == 6 ){$list="";
                    foreach(split /:/, $arg){$list .= "ID_CAT=$_ OR ";}
                    if($list =~ m/ OR $/){$list =~ s/ OR $//;}else{$list.="ID_CAT=".$arg}
                }
                elsif($set == 7 ){$dump = $arg}
                elsif($set == 9 ){$table = $arg if (!$table)}
                elsif($set == 10){$insert = $arg}
                elsif($set == 11){$insert = `~/uvar.sh -r $arg`}
                undef $set;
        }else{
            print "<<<<<$arg>>>>\n"
        }
	}#rof
    say "WARNING! Argument type $set, has not been provided!" if($set);

if($insert){
   $log = $insert;
}    

if($set && $set > 7 && !$db_source){
    my $prp = $cnf->anon('AUTO_LOGIN', undef);
    my @a = split('/', $prp);
    if(@a==2){
        $alias=$database=$a[0]; $passw=$a[1];
    }else{
        say "Error: Autonom property not set AUTO_LOGIN<".$prp."> in main.inf to operate system table -> $table."; exit 0;
    }		
    undef $set;
}

if($list){
    if($list eq -1){
       if($cat_id){$list = $cat_id}else{$list="<11"}
    }
    $cat_id = $list;
}

if(!$db_source){
    $db_source = $cnf->constant('DBI_SOURCE');
    $db_source = "DBI:SQLite:" if !$db_source;
}

$IS_PG_DB = 1 if(index (uc $db_source, 'DBI:PG') ==0);

if(!$database){$database = prompt "\n$TITLE\nPlease enter database name: "}
if(!$alias){$alias = prompt "\n$TITLE\nPlease enter alias name: "}
if(!$passw){$passw = prompt "\n$TITLE\nPlease enter password for database -> $database: ", -echo => '*'}
$passw = uc crypt $passw, hex Settings->CIPHER_KEY if $passw && !$IS_PG_DB;
	
  
my $db = connectDB($database,$alias,$passw);
my $st = traceDBExe("SELECT alias FROM AUTH WHERE alias='$alias' and passw='$passw';");
my @c = $st->fetchrow_array();
if (@c && $c[0] eq $alias) {
    if($table){checkCreateTable()}
    elsif(!$cat_id){
            $cat_id = $cnf->anon('CAT', undef);
            $cat_id =~ s/^.*>\n//;
            say "Sample Categories:\n$cat_id";
            $cat_id = prompt "Enter Category id (default is '01' for Unspecified): ";
            $cat_id = '01' if ($cat_id eq ""); 
    }
    
    if(!$log&&!$list){
        my $t = prompt "Enter Log ([enter] key quits):";
        $log = $t;
        while($t ne ""){
            $t=prompt ":";
            $log .= "\n".$t if $t;
        }

        say "\nLog:$log";
        if(!$log){
            say "Aborting, no log has been entered."; exit;
        }
    }
    else{
        #encode
        $log =~ s/'/''/g if $log;
    }
    if($list){
        my ($fh, $is_view, $cnt) = (undef,0,0);
        if($table) {
            if($IS_PG_DB){
             $SELECT = "SELECT * FROM public.\"$table\";"; 
            }else{
             $SELECT = "SELECT * FROM '$table';"; 
            }
            $is_view = 1;
        }
        if (!$SELECT){
             $SELECT = "SELECT DATE, LOG FROM VW_LOG WHERE $list LIMIT $LIMIT_REC"; 
        }
        $st = traceDBExe($SELECT);
        if ($dump){print $out if $out; open($fh, '>', $dump)}else{$fh=*STDOUT}
        my $dot = "-" x 80;
        print $fh $dot."\n";
            print $fh $TITLE."\nDSN: $DSN\n"."DATE: ".gmtime()."\nSQL: $SELECT\n";
        print $fh $dot."\n";
        while(@c=$st->fetchrow_array()){
            if($LIMIT && $cnt>$LIMIT){last}
            if($is_view){
                foreach(@c){print $fh $_."|";}
                print "\n";
            }else{
                print $fh "".$c[0]."|".$c[1]."\n"; 
            }
            $cnt++;
        }
        print $fh $dot."\n";
        close $fh if $dump;
        print "Done, written to dump file $cnt entries!\n" if $dump;
    }
    else{
        if($INSERT){
            # try{
                if($log ne""){
                    my $stamp = Settings::getCurrentSQLTimeStamp();                
                    my $pst = $db->prepare($INSERT);                
                    $pst->execute("$stamp", $log);
                    say "Insert issued to -> $DSN: for $table $stamp=>'$log'";
                }
               
            # }catch{                

            #     # if (my $ex = $@) {
            #     #     print STDERR "DBI Exception:\n";
            #     #     print STDERR "  Exception Type: ", ref $ex, "\n";
            #     #     print STDERR "  Error:          ", $ex->error, "\n";
            #     #     print STDERR "  Err:            ", $ex->err, "\n";
            #     #     print STDERR "  Errstr:         ", $ex->errstr, "\n";
            #     #     print STDERR "  State:          ", $ex->state, "\n";
            #     #     print STDERR "  Return Value:   ", ($ex->retval || 'undef'), "\n";
            #     # } 


            #     LifeLogException->throw(error=>"DSN: [$DSN]\nSQL:$INSERT\nError encountered -> $@", show_trace=>1);
            # };
        }
        else{
            Settings::toLog($db, $log, $cat_id);
            say "Log issued to -> $DSN: for LifeLog.LOG";
        }
                
    }
}else{
    #We log failed possible intruder access.
    if(!$passw){
        say "Error: Exiting, no password has been entered for ($alias).";  exit 0;
    }
    Settings::toLog($db,"User $alias, failed to authenticate, from command line!");
    say "Error: Get out of here! Entered password doesn't match for ($alias).";  exit 0;
}

sub connectDB {
    my ($d,$u,$p) = @_;
    $u = $alias if(!$u);
    $p = $alias if(!$p);
    my $db =$u;
    if(!$d){$db = 'data_'.$u.'_log.db';$d=$u}
    else{   $db = 'data_'.$d.'_log.db';$database = $d if !$database}
    $DBFILE = $LOG_PATH.$db;
    if ($IS_PG_DB)  {
        $DSN = $db_source .'dbname='.$d;
    }else{
        $DSN = $db_source .'dbname='.$DBFILE;        
    }    
    try{$u=$p="lifelog";
        return DBI->connect($DSN, $u, $p, {AutoCommit => 1, RaiseError => 1, PrintError => 0, show_trace=>1});
    }catch{           
       LifeLogException->throw(error=>"Error->$@\n[$DSN]",  show_trace=>1);
    }
}

sub traceDBExe {
    my $sql = shift;
    try{
        print "<<traceDBExe<$sql>>>\n" if($sql !~ /^SELECT/);
        my $st = $db->prepare($sql);
           $st -> execute() or LifeLogException->throw("Execute failed [$DBI::errstri]", show_trace=>1);
        return $st;
    }catch{
        #BUG 31 fix.
        if($IS_PG_DB &&  index($sql,Settings->VW_LOG)>0){
            $db -> do(Settings::createViewLOGStmt());
            my $st = $db->prepare($sql);
               $st -> execute() or LifeLogException->throw("Execute failed [$DBI::errstri]", show_trace=>1);
            return $st;
        }
        LifeLogException->throw(error=>"DSN: [".Settings::dsn()."] Error encountered -> $@", show_trace=>1);
    }
}


sub checkCreateTable {
   print "$TITLE\nUsing spec -> $table\n";
   my($table,$col,$typ) =  split(':',$table); # our global $table is different to the one we use with SQL.   
   if($table && $col && $typ){
      $table = uc $table;
      $VW_NAME = "VW_$table";
      $COL_NAME = uc $col;
      $COL_TYPE = uc $typ;
      if($IS_PG_DB){
          #TODO
            my %tables = ();
            my @tbls = $db->tables(undef, 'public');
            foreach (@tbls){
                my $t = uc substr($_,7);
                $tables{$t} = 1;
            }
            if(!$tables{$table}){
                traceDBExe("CREATE TABLE $table (DATE TIMESTAMP NOT NULL, $COL_NAME $COL_TYPE NOT NULL);");
                traceDBExe(qq(CREATE VIEW $VW_NAME AS
          SELECT rowid as ID,*, (select count(rowid) from LOG as recount where a.rowid >= recount.rowid) as PID
          FROM $table as a ORDER BY Date(DATE) DESC;
));
            }

      }else{
                my $pst = traceDBExe("SELECT count(name) FROM sqlite_master WHERE type='table' and name like '$table';");
                my @res = $pst->fetchrow_array();
                if($res[0]==0){
                    traceDBExe("CREATE TABLE $table (DATE DATETIME NOT NULL, $COL_NAME $COL_TYPE NOT NULL);");
                }
                $pst = traceDBExe("SELECT count(name) FROM sqlite_master WHERE type='view' and name like '$VW_NAME';");
                @res = $pst->fetchrow_array();
                if($res[0]==0){
                    traceDBExe(
                                qq(CREATE VIEW $VW_NAME AS
                                        SELECT rowid as ID,*, (select count(rowid) from LOG as recount where a.rowid >= recount.rowid) as PID
                                        FROM $table as a ORDER BY Date(DATE) DESC, Time(DATE) DESC;
                    ));
                }
       }      
      $SELECT = "SELECT DATE, $COL_NAME FROM $VW_NAME LIMIT $LIMIT_REC;";
      $INSERT = "INSERT INTO $table(DATE, $COL_NAME) VALUES(?,?)";
  }
}

END {$db->disconnect() if ($db)}