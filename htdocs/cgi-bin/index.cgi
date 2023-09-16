#!/usr/bin/env perl
# A delegated CNFParser processed rendering of the Document Index Web page, a Model-View-Controller Pattern approuch.
# The index.cnf script contains the structure and page skeleton,
# all configuration as well as the HTMLIndexProcessorPlugin converting the CNF to final HTML.
# It is very convienient, as both style and script for the page is separated and developed in the index.cnf.
# Which then can be moved to a respective include file over there.
# This controller binds and provides to the parser to do its magic thing.
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use v5.30;
use strict;
use warnings;
use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;
##
# We use dynamic perl compilations. The following ONLY HERE required to carp to browser on
# system requirments or/and unexpected perl compiler errors.
##
use CGI::Carp qw(fatalsToBrowser set_message);

BEGIN {
   sub handle_errors {
      my $err = shift;
      say "<html><body><h2>Server Error</h2><pre>Error: $err</pre></body></html>";
  }
  set_message(\&handle_errors);
}

use lib "system/modules";
require CNFParser;
require CNFNode;

our $GLOB_HTML_SERVE = "'{}/*.cgi' '{}/*.htm' '{}/*.html' '{}/*.md' '{}/*.txt'";
our $script_path = $0; $script_path =~ s/\w+.cgi$//;

exit &HTMLPageBuilderFromCNF;

sub HTMLPageBuilderFromCNF {
    my $html = obtainDirListingHTML('docs');
    my $cnf  = CNFParser -> new (
                            $script_path."index.cnf",{
                             DO_ENABLED => 1, HAS_EXTENSIONS=>1,
                             ANONS_ARE_PUBLIC => 1,
                                PAGE_HEAD     => "<h1 id=\"index_head\">Index Page of Docs Directory</h1>",
                                PAGE_CONTENT  => $html,
                                PAGE_FOOT     => "<!--Not Defined-->"
                            }
                );
    my $ptr = $cnf->data();
    $ptr = $ptr->{'PAGE'};
    say $$ptr if $ptr;
    return 0
}

sub obtainDirListingHTML {
    my ($dir, $ret) = (shift,"");
    my $html = listFiles($dir,$script_path,"");
    if($html){
       $ret .="<ul><b>$dir &#8594;</b>\n";
       $ret .= $html;
        opendir (my $handle, $script_path.$dir) or die "Couldn't open directory, $!";
        while (my $node = readdir $handle) {
            my $file_full_path = "$script_path$dir/$node";
            if($node !~ /^\./ && -d $file_full_path){
               $html = obtainDirListingHTML($dir.'/'.$node);
               $ret .= $html if $html
            }
        }
        closedir $handle;
       $ret .= "</ul>";
    }
    return $ret;
}

sub listFiles ($){
    my ($dir, $script_path, $ret) = @_;
    my $path = $script_path.$dir;
    my $spec = $GLOB_HTML_SERVE; $spec =~ s/{}/$path/gp;
    my @files = glob ($spec);
    foreach my $file(@files){
            ($file =~ m/(\w+\.\w*)$/g);
            my $name = $1;
            if($file =~ /\.md$/){
                my @title = getDocTitle($file);
                $ret .= qq(\t\t\t<li><a href="$dir/$title[0]">$title[1]</a> &dash; $name</li>\n);
            }else{
                $ret .= qq(\t\t\t<li><a href="$dir/$name">$name</a></li>\n);
            }
    }
    return $ret;
}

sub getDocTitle($){
    my ($file,$ret) = shift;
    open(my $fh, '<', $file) or LifeLogException->throw("Can't open $file: $!");
    while (my $line = <$fh>) {
        if($line =~ /^#+\s*(.*)/){
           $ret = $1;
           last;
        }
    }
    close $fh;
    ($file =~ m/(\w+\.\w*)$/g);
    return ($1,$ret)
}
1;
=begin copyright
Programed by  : Will Budic
EContactHash  : 990MWWLWM8C2MI8K (https://github.com/wbudic/EContactHash.md)
Source        : https://github.com/wbudic/LifeLog
Open Source Code License -> https://github.com/wbudic/PerlCNF/blob/master/ISC_License.md
=cut copyright

