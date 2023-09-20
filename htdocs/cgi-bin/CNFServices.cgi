#!/usr/bin/env perl
# CNF Services operator. The plugins and services themselve should return html.
# Idea is that this CGI file contains the actuall CNF to interact in realtime with a web page.
#
use v5.30;
use strict;
use warnings;
use Exception::Class ('CNFHTMLServiceError');
use Syntax::Keyword::Try;
use CGI;
use CGI::Session '-ip_match';
no warnings qw(experimental::signatures);
use feature qw(signatures);
##
# We use dynamic perl compilations. The following ONLY HERE required to carp to browser on
# system requirments or/and unexpected perl compiler errors.
##
use CGI::Carp qw(fatalsToBrowser set_message);

BEGIN {
   sub handle_errors {
      my $err = shift;
      say "<html><body><h2>Server Error</h2><code style='color:crimson; font-weight:bold'>$err<code></body></html>";
   }
   set_message(\&handle_errors);
}

use lib "system/modules";
require CNFParser;
require CNFNode;

our $GLOB_HTML_SERVE = "'{}/*.cgi' '{}/*.htm' '{}/*.html' '{}/*.md' '{}/*.txt'";
our $script_path = $0; $script_path =~ s/\w+.cgi$//;

exit &CNFHTMLService;

sub CNFHTMLService {
    my ($cgi,$ptr)   = (CGI -> new(),undef);
    my  $cnf  = CNFParser -> new (undef,{ DO_ENABLED => 1, HAS_EXTENSIONS=>1, ANONS_ARE_PUBLIC => 1, CGI=>$cgi });
        $cnf->parse(undef,_getServiceScript($cgi));
        $ptr = $cnf->data();
        $ptr = $ptr->{'PAGE'};
    say $$ptr if $ptr;
    return 0
}

sub _getServiceScript($cgi) {
     my $service = $cgi->param('service'); $service = "undef" if not $service;
     if($service eq 'feeds'){
        return _CNF_Script_For_Feeds();
     }
     CNFHTMLServiceError->throw(error=>"UNKNOWN SERVICE -> $service", show_trace=>1)
}

sub _CNF_Script_For_Feeds {
<<__CNF_IS_COOL__;
<<@<%LOG>
            file      = web_server.log
            # Should it mirror to console too?
            console   = 0
            # Disable/enable output to file at all?
            enabled   = 0
            # Tail size cut, set to 0 if no tail cutting is desired.
            tail      = 1000
>>
<<PROCESS_RSS_FEEDS<PLUGIN>

    RUN_FEEDS = yes
    CONVERT_TO_CNF_NODES = yes
    OUTPUT_TO_CONSOLE = false
    OUTPUT_TO_MD = no
    BENCHMARK = no
    TZ=Australia/Sydney
    OUTPUT_DIR = "./rss_output"


    CONVERT_CNF_HTML  = yes
    CNF_TREE_STORE    = true

    package     : RSSFeedsPlugin
    subroutine  : process
    property    : RSS_FEEDS

>>
// Following is a table having a list of details for available RSS feeds to process.
|| The more rows have here the longer it takes to fetch them, what is it, once a day, week, month?
<<    RSS_FEEDS     <DATA>
ID`Name`URL`Description~
#`CPAN`http://search.cpan.org/uploads.rdf`CPAN modules news and agenda.~
#`The Perl Foundation RSS Feed`https://news.perlfoundation.org/rss.xml`The Perl Foundation is dedicated to the advancement
of the Perl programming language through open discussion, collaboration, design, and code.
 The Perl Foundation is a non-profit organization* based in Holland, Michigan~
#`Perl Weekly`https://perlweekly.com/perlweekly.rss`A free, once a week e-mail round-up of hand-picked news and articles about Perl.
The Perl Weekly ( http://perlweekly.com/ ) is a newsletter including links to blog posts and other news items
 related to the Perl programming language.~
>>

__CNF_IS_COOL__
}


1;

=begin copyright
Programed by  : Will Budic
EContactHash  : 990MWWLWM8C2MI8K (https://github.com/wbudic/EContactHash.md)
Source        : https://github.com/wbudic/LifeLog
    This source file is copied and usually placed in a local directory, outside of its repository project.
    So it could not be the actual or current version, can vary or has been modiefied for what ever purpose in another project.
    Please leave source of origin in this file for future references.
Open Source Code License -> https://github.com/wbudic/PerlCNF/blob/master/ISC_License.md
=cut copyright