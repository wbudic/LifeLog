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
my $dir = $cgi->param('dir');
   #$dir = './htdocs/cgi-bin/docs' if(!$dir);
   $dir = './docs' if(!$dir);
my $file = $cgi->param('file');
   #$file = qq(../../Current Development Check List.md) if(!$file);

try{
if($file && -f "$dir/$file"){
    open my $fh, '<', "$dir/$file" or die "Can't open file $!";
    read $fh, my $file_content, -s $fh;
    my $html = markdown($file_content);
    print $cgi->header, "<DIV style='padding:10px'>\n$html\n</DIV>", $cgi->end_html;
}
elsif(-d "$dir"){ #List and return markup files found in dir, comma separated.
    opendir(DIR, $dir) or die $!;
    my @lst = (); 
    while ($file = readdir(DIR)) {
        next if ($file =~ m/^\./) || ($file =~ m/!\.md$/);
        next if (-d "$dir/$file");
        push @lst, $file;
    }
    closedir(DIR);   
    print $cgi->header, join (',', map { chomp; qq("$_") } sort @lst);
}else{
    die "Directory [$dir] not valid!"
}


exit;
}
catch{
    my $err = $@;
    print $cgi->header,
            "<font color=red><b>SERVER ERROR</b></font> on ".DateTime->now."<pre> $err\n$file</pre>";
    print $cgi->end_html;
}