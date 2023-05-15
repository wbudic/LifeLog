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
use DateTime;
##
# We is dynamic perl compilations. The following ONLY HERE required to carp to browser on 
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

#debug -> 
use lib "/home/will/dev/LifeLog/htdocs/cgi-bin/system/modules";
use lib "system/modules";
require CNFParser;
require CNFNode;

our $GLOB_HTML_SERVE = "{}/*.cgi {}/*.htm {}/*.html {}/*.md {}/*.txt";
our $script_path = $0;
$script_path =~ s/\w+.cgi$//;

my $v = q/
<<$APP_DESCRIPTION<CONST>
This application presents just
a nice multi-line template.
>>/;
# $v =~ m/\s*(<<[@%]<) ([\$@%]?\w+)(>)* | (>>)
#        /gx and my @captured = @{^CAPTURE};


$v =~ m/(<{2,3})                          
            ([\$@%]?\w+)
                 (<?)  ([\w\s]+)   (>?)
        |(<<[@%]<)  ([\$@%]?\w+) (>?)
        |(>>)
       /gx and my @captured = @{^CAPTURE};





exit main();

sub main {    
    my $html = obtainDirListingHTML('docs');
    my $cnf = CNFParser->new(
                            $script_path."index.cnf",{
                             DO_enabled => 1, 
                             ANONS_ARE_PUBLIC => 1,
                                                   PAGE_HEAD    => "<h2>Index Page of Docs</h2>", 
                                                   PAGE_CONTENT => $html, 
                                                   PAGE_FOOT    => "<!--Not Defined-->"
                            }
                        );
    my $ptr = $cnf->data();
    $ptr = $ptr->{'PAGE'};   
    say $$ptr if $ptr;    
    return 0
}

sub obtainDirListingHTML {
    my ($dir, $ret) = (shift,"");    
    $ret .="<b>$dir &#8594;</b><ul>\n";
    $ret .= listFiles($dir,$script_path);
    my $handle;
    opendir ($handle, $script_path.$dir) or die "Couldn't open directory, $!";
    while (my $node = readdir $handle) {
        my $file_full_path = "$script_path$dir/$node";
        if($node !~ /^\./ && -d $file_full_path){
           $ret .= obtainDirListingHTML($dir.'/'.$node);
        }
    }
    closedir $handle;
    
    $ret .= "</ul>";
    return $ret;
}
sub listFiles ($){
    my ($dir, $script_path, $ret) = @_;
    my $path = $script_path.$dir;
    my $spec = $GLOB_HTML_SERVE; $spec =~ s/{}/$path/gp;
    my @files = glob ($spec);        
    foreach my $file(@files){
            if($file =~ /\.md$/){
                my @title = getDocTitle($file);            
                $ret .= qq(\t\t\t<li><a href="$dir/$title[0]">$title[1]</a></li>\n);
            }else{
                ($file =~ m/(\w+\.\w*)$/g);
                $ret .= qq(\t\t\t<li><a href="$dir/$1">$1</a></li>\n);
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






