#!/usr/bin/perl -w
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Try::Tiny;

my $s1 ="`1`2`3`te\\`s\\`t`the best`";

 $s1 =~ s/\\`/\\f/g;
 #print $s1,"\n";
foreach (  split ( /`/, $s1)  ){
    $_ =~ s/\\f/`/g;
    print $_,"\n";
}
print "Home:".$ENV{'PWD'}.$ENV{'NL'};



1;
