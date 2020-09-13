#!/usr/bin/perl
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;

use Syntax::Keyword::Try;
use DateTime;
use CGI;
use Text::Markdown 'markdown';

my $cgi = CGI->new;
my $file = $cgi->param('file');
   $file = qq(../../Current Development Check List.md) if(!$file);

try{

open my $fh, '<', $file or die "Can't open file $!";
read $fh, my $file_content, -s $fh;
my $html = markdown($file_content);
    print $cgi->header, "<DIV style='padding:10px'>\n$html\n</DIV>", $cgi->end_html;
exit;
}
catch{
    my $err = $@;
    print $cgi->header,
            "<font color=red><b>SERVER ERROR</b></font> on ".DateTime->now."<pre> $err\n$file</pre>";
    print $cgi->end_html;
}