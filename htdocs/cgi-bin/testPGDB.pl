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

# my @data_sources = DBI->data_sources("Pg");
# foreach (@data_sources){
#             print $_ ,"\n";
#         }

# my $db = DBI->connect("DBI:Pg:host=localhost;dbname=admin", "admin", "admin", {AutoCommit => 1, RaiseError => 1, PrintError => 0})
#                        or LifeLogException->throw(error=>"<p>Error->"& $DBI::errstri &"</p>$!",  show_trace=>1);

#         my @tbls = $db->tables(undef, 'public');
#         foreach (@tbls){
#             print uc substr($_,7) ,"\n";
#         }

#  $db->disconnect();


# $db = DBI->connect("dbi:Pg:dbname=postgres", "will", "will69", {AutoCommit => 1, RaiseError => 1, PrintError => 0});
# $db ->do('drop database from_perl_createdDB');
# $db ->do('create database from_perl_createdDB');
# $db->disconnect();

# @data_sources = DBI->data_sources("Pg");
# foreach (@data_sources){
#             print $_ ,"\n";
#         }
my ($alias,$pass)=("admin3", "admin3");

my $SQL1=<<SQL;

CREATE ROLE $alias WITH
	LOGIN
	SUPERUSER
	CREATEDB
	CREATEROLE
	INHERIT
	NOREPLICATION
	CONNECTION LIMIT -1
	PASSWORD '$pass';

GRANT postgres TO $alias;
SQL
my $SQL2=<<SQL;
CREATE DATABASE $alias
    WITH 
    OWNER = $alias
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_AU.UTF-8'
    LC_CTYPE = 'en_AU.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;
SQL

#print $SQL,"\n";

my $db = DBI->connect("dbi:Pg:dbname=postgres");#", "will", "will69", {AutoCommit => 1, RaiseError => 1, PrintError => 0});
$db ->do($SQL1);
$db ->do($SQL2);

my @data_sources = DBI->data_sources("Pg");
foreach (@data_sources){
            print $_ ,"\n";
}

    foreach my $ln (@data_sources){
            my $i = rindex $ln, '=';
            my $n = substr $ln, $i+1;
            print $n,"\n";
    }


$db->disconnect();


$db = DBI->connect("DBI:Pg:host=localhost;dbname=admin3", "admin3", "admin3", {AutoCommit => 1, RaiseError => 1, PrintError => 0});
    my @tbls = $db->tables(undef, 'public');
    foreach (@tbls){
        print uc substr($_,7) ,"\n";
    }