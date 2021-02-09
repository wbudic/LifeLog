#!/usr/bin/perl
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
no warnings 'portable';

use lib $ENV{'PWD'}.'/htdocs/cgi-bin/system/modules';

require CNFParser;
require Settings;

use Exception::Class ('LifeLogException');
use DBI;
use IO::Interactive qw(is_interactive interactive busy);
use IO::Prompter [ -stdio, -style=>'bold' ];

my $cnf = CNFParser->new('dbLifeLog/main.cnf');


my $help = qq(

Syntax: $0 {_} {-vim_option}... {ext_name}...

);

my ($database, $alias, $db_source, $set, $cat_id, $log) = 0;
my ($IS_PG_DB, $DSN, $DBFILE);
my $LOG_PATH = "dbLifeLog/";

my $io;
if (!is_interactive) { 
   #die "Input from terminal (pipe) not allowed!\n" 
   busy {
       $log = readline STDIN;
       say $log;
       open STDIN, "<", "/dev/tty" or die "IO Error @_";
   } 
}

foreach my $arg(@ARGV){
    #print "{{{$arg}}}"; 
    if($arg =~ /^\-/){
        if($arg=~/(^\-*\?)/){print $help; exit;  
        }elsif($arg=~/(^\-*database)/){$set=1;}
        elsif($arg=~/(^\-*alias)/){$set=2;}
        elsif($arg=~/(^\-*db_src)/){$set=3;}
        elsif($arg=~/(^\-*c.*)/){$set=4;}
        elsif($arg=~/(^\-*log)/){$set=5;}
    }elsif($arg ne $ENV{'HOME'}){           
        if($arg=~/^\w+\./){
            print "Ignoring -> $arg\n"; 
            next;
        }
        if   ($set == 1)   { undef $set; $database = $arg }
        elsif($set == 2){ undef $set; $alias = $arg }
        elsif($set == 3){ undef $set; $db_source = $arg }
        elsif($set == 4){ undef $set; $cat_id = $arg }
        elsif($set == 5){ undef $set; $log = $arg }
    }
}

if(!$database && !$alias){
$database="admin";
    #say "Error: Database -database or -alias option not set!";  exit 0;
}
if(!$alias){$alias=$database}
if(!$db_source){
    $db_source = $cnf->constant('DBI_SOURCE');
    $db_source = "DBI:SQLite:" if !$db_source;
}

$IS_PG_DB = 1 if(index (uc $db_source, 'DBI:PG') ==0);



my $passw = prompt "Enter The Password ($database): ", -echo => '*';
$passw = uc crypt $passw, hex Settings->CIPHER_KEY if $passw;

# system ("stty -echo");  
# my $password = <STDIN>;  
# system ("stty echo");

my $db = connectDB($database,$alias,$passw);
my $st = traceDBExe("SELECT alias FROM AUTH WHERE alias='$alias' and passw='$passw';");
my @c = $st->fetchrow_array();
if (@c && $c[0] eq $alias) {
    if(!$cat_id){
        $cat_id = $cnf->anons('CAT', undef);
        $cat_id =~ s/^.*>\n//;
        say $cat_id;
        $cat_id = prompt "Enter Category id (default is '01' for Unspecified): ";
        $cat_id = '01' if ($cat_id eq ""); 
    }
    if(!$log){
        my $t = prompt "Enter Log ([enter] key quits):";
        $log = $t;
        while($t ne ""){
            $t=prompt ":";
            $log .= "\n".$t;
        }

        say "\nLog:$log";
        if(!$log){
            say "Aborting, no log ahas been entered."; exit;
        }
    }
    else{
        #encode
        $log =~ s/'/''/g;
    }
    Settings::toLog($db, $log, $cat_id);
    say "Log issued to -> $DSN";
}else{
    #We log failed possible intruder access.
    if(!$passw){
        say "Error: Exiting, no password has been entered for ($alias).";  exit 0;
    }
    Settings::toLog($db,"User $alias, failed to authenticate, from command line!");
    say "Error: Get out of here! Entered password $passw doesn't match for ($alias).";  exit 0;
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
    try{
        return DBI->connect($DSN, $u, $p, {AutoCommit => 1, RaiseError => 1, PrintError => 0, show_trace=>1});
    }catch{           
       LifeLogException->throw(error=>"<p>Error->$@</p><br><p>$DSN</p>",  show_trace=>1);
    }
}

sub traceDBExe {
    my $sql = shift;
    try{
        my $st = $db->prepare($sql);
           $st -> execute() or LifeLogException->throw("Execute failed [$DBI::errstri]", show_trace=>1);
        return $st;
    }catch{
        #BUG 31 fix.
        if(Settings::isProgressDB() &&  index($sql,Settings->VW_LOG)>0){
            $db -> do(Settings::createViewLOGStmt());
            my $st = $db->prepare($sql);
               $st -> execute() or LifeLogException->throw("Execute failed [$DBI::errstri]", show_trace=>1);
            return $st;
        }
        LifeLogException->throw(error=>"DSN: [".Settings::dsn()."] Error encountered -> $@", show_trace=>1);
    }
}

END {
    $db->disconnect() if $db;
}


1;