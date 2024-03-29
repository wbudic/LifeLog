#!/usr/bin/env perl
# CNF Services operator. The plugins and services themselve should return html.
# Idea is that this CGI file contains the actuall CNF to interact in realtime with a web page.
#
use v5.30;
use strict;
use warnings;
use Exception::Class ('CNFHTMLServiceError');
use Syntax::Keyword::Try;
use utf8;
use CGI::Tiny;
use Path::Tiny;
no warnings qw(experimental::signatures);
use feature qw(signatures);
##
# We use dynamic perl compilations. The following ONLY HERE required to carp to browser on
# system requirments or/and unexpected perl compiler errors.
##
use CGI::Carp qw(fatalsToBrowser set_message);

##
# This is a entry point script (main).
##
use lib::relative "system/modules";
require CNFParser;
require CNFNode;

our $GLOB_HTML_SERVE = "'{}/*.cgi' '{}/*.htm' '{}/*.html' '{}/*.md' '{}/*.txt'";
our $script_path = $0; $script_path =~ s/\w+.cgi$//;
use constant LOG_Settings =>q(
<<@<%LOG>
    file      = web_server.log
    # Should it mirror to console too?
    console   = 0
    # Disable/enable output to file at all?
    enabled   = 0
    # Tail size cut, set to 0 if no tail cutting is desired.
    tail      = 1000
>>
);

cgi {
  my $cgi = $_;
     $cgi->set_error_handler(
        sub {
            my ($cgi, $error, $rendered) = @_;
            chomp $error;
            $cgi->render(text=>qq(<html><body><font style="color:crimson; font-weight:bold">You have unfortunately hit an cgi-bin::CNFHTMLServiceError</font>
                                            <div class='content-debug_output'><pre style="background:transparent">$error</pre><br> </div>
                                </body></html>
                                )
                    );
        }
     );
  exit CNFHTMLService($cgi);
};


sub CNFHTMLService {

    my ($cgi,$ptr)   = (shift, undef);
    my  $cnf  = CNFParser -> new (undef,{ DO_ENABLED => 1, HAS_EXTENSIONS=>1, ANONS_ARE_PUBLIC => 1, CGI=>$cgi });
        $cnf->parse(undef,_getServiceScript($cgi));
        $ptr = $cnf->data();
        $ptr = $ptr->{'PAGE'};
    #say $$ptr if $ptr;
    $cgi -> render(text=>$$ptr);
    return 0
}

sub _getServiceScript($cgi) {
     my $service = $cgi->param('service');
     unless ($service){
        $cgi->set_response_status(404);
        CNFHTMLServiceError->throw(error=>'The Service parameter \'service\' is not set!', show_trace=>1);
     }
     if($service eq 'feeds'){
        return _CNF_Script_For_Feeds();
     }
}

sub _CNF_Script_For_Feeds {
LOG_Settings . <<__CNF_IS_COOL__;
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
#`The Cipher Brief RSS Feed`https://www.thecipherbrief.com/feed`The Cipher Brief is the go-to digital platform for the latest security news and high-level analysis. Each day, we offer multiple expert perspectives, engaging the private sector to find solutions and foster dialogue on what events mean for businesses and organizations around the world. More than just reporting on the news, The Cipher Brief helps readers understand what the news means to you.~
#`Viral Now`https://viralnow.uk/feed/`ViralNow is a dynamic online platform at the forefront of curating and delivering trending and viral content. ViralNow brings you the latest and most engaging stories, videos, and articles from around the world.~
#`The Sydney Morning Herald - World RSS Feed`http://www.smh.com.au/rssheadlines/world/article/rss.xml`The Sydney Morning Herald is Australia's leading news source. The Sydney Morning Herald sets the standard for journalistic excellence for Sydney, Australia, and the rest of the world. From breaking news, to travel and fashion, The Sydney Morning Herald continues to transform the way Australians get their news.~
#`Life Hacker`https://lifehacker.com/rss`Lifehacker’s an award-winning daily blog that features tips, shortcuts, and downloads that help you work and live smarter and more efficiently.~
#`Politico`http://www.politico.com/rss/politicopicks.xml`POLITICO strives to be the dominant source for news on politics and policy in power centers across every continent where access to reliable information, nonpartisan journ.lism and real-time tools create, inform and engage a global citizenry.~
>>

__CNF_IS_COOL__
}

__END__

=begin copyright
Programed by  : Will Budic
EContactHash  : 990MWWLWM8C2MI8K (https://github.com/wbudic/EContactHash.md)
Source        : https://github.com/wbudic/LifeLog
    This source file is copied and usually placed in a local directory, outside of its repository project.
    So it could not be the actual or current version, can vary or has been modiefied for what ever purpose in another project.
    Please leave source of origin in this file for future references.
Open Source Code License -> https://github.com/wbudic/PerlCNF/blob/master/ISC_License.md
=cut copyright