#!perl -w
$ENV{DBI_AUTOPROXY} = 'dbi:Gofer:transport=null;policy=pedantic';
END { delete $ENV{DBI_AUTOPROXY}; };
$ENV{DBI_PUREPERL} = 2;
END { delete $ENV{DBI_PUREPERL}; };
require './t/07kids.t'; # or warn $!;
