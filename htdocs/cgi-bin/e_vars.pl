#!/usr/bin/perl

#################################################################### 
#
#	Environmantal Variables (E-Vars)
#	©2002, PerlScriptsJavaScripts.com
#
#	Requires: Perl5+
#	Created:  January, 2002
#	Author:   John Krinelos
#	Contact:  john@perlscriptsjavascripts.com
#	
#	This script / program is copyright material!
#	
#	Agent for copyright : 
#	Gene Volovich
#	Law Partners, 
#	140 Queen St. 
#	Melbourne
#	Ph. +61 3 9602 2266 
#	gvolovich@lawpartners.com.au
#	http://www.lawpartners.com.au/
#
#################################################################### 
 
#################################################################### 
#
# Place this in any cgi-bin CHMOD it to 755 (if UNIX) then call 
# it from your browser. Eg. http://www.you.com/cgi-bin/vars.cgi

$of = qq~<font size="2" face="arial,verdana,helvetica">~;
$cf = qq~</font>~;
 
my @slocs = qw~
	/usr/sbin/sendmail
	/usr/bin/sendmail
	/sbin/sendmail
	/usr/slib/sendmail
	/usr/lib/sendmail
	/bin/sendmail
	/lib/sendmail
	/slib/sendmail
	/usr/sendmail
	/sendmail
	sendmail
~;

print qq~Content-type: text/html


<html>
<head><title>Enviromental Variables Report. PerlScriptsJavaScripts.com</title></head>
<body bgcolor="#ffffff" alink="#ff0000" link="#ff0000" vlink="#ff0000">

<center>
$of<b>Enviromental Variables returned by this server. <a href="http://www.perlscriptsjavascripts.com/?evs">A PerlScriptsJavaScripts Product</a></b>$cf
</center>
<br>
<table align="center" border="1" cellpadding="5" cellspacing="0" width="600">
<tr>
<td>$of<b>Variable</b>$cf</td>
<td>$of<b>Value</b>$cf</td>
</tr>
~;

my @vars = sort(keys(%ENV));
foreach(@vars) {
	$ENV{$_} ||= qq~&nbsp;~;
	print qq~
	<tr>
	<td>$of\$ENV{$_}$cf</td>
	<td>$of$ENV{$_}$cf</td>
	</tr>
	~;
}

print qq~
<tr>
<td>$of\$ENV{DOCUMENT_NAME}$cf</td>
<td>$of$ENV{DOCUMENT_NAME} &nbsp;$cf</td>
</tr>
<tr>
<td>$of\$ENV{DOCUMENT_URI}$cf</td>
<td>$of$ENV{DOCUMENT_URI} &nbsp;$cf</td>
</tr>
<tr>
<td>$of\$ENV{LAST_MODIFIED}$cf</td>
<td>$of$ENV{LAST_MODIFIED} &nbsp;$cf</td>
</tr>
<tr>
<td>$of\$ENV{DATE_GMT}$cf</td>
<td>$of$ENV{DATE_GMT} &nbsp;$cf</td>
</tr>
<tr>
<td>$of\$ENV{DATE_LOCAL}$cf</td>
<td>$of$ENV{DATE_LOCAL} &nbsp;$cf</td>
</tr>
<tr>
<td>$of\$ENV{REMOTE_USER}$cf</td>
<td>$of$ENV{REMOTE_USER} This var returns the value of a .ht username$cf</td>
</tr>
</table>
<br>

<center>
$of<b>Path(s) to Sendmail</b>$cf
</center>
<br>

<table align="center" border="1" cellpadding="5" cellspacing="0" width="600">
~;

foreach(@slocs) { 
	if(-e $_){
		print qq~
		<tr>
		<td>$of$_$cf</td>
		</tr>
		~;
	}
} 

print qq~
</table>
<br>

<center>
$of<b>Additional Information</b>$cf
</center>
<br>
<table align="center" border="1" cellpadding="5" cellspacing="0" width="600">
<tr>
<td>$of<b>Variable</b>$cf</td>
<td>$of<b>Value</b>$cf</td>
<td>$of<b>Description</b>$cf</td>
</tr>
<tr>
<td>$of\$] $cf</td>
<td>$of$]$cf&nbsp;</td>
<td>$of Version of Perl$cf</td>
</tr>
<tr>
<td>$of\$0 $cf</td>
<td>$of$0$cf&nbsp;</td>
<td>$of Script name$cf</td>
</tr>
<tr>
<td>$of\$\$ $cf</td>
<td>$of$$ $cf&nbsp;</td>
<td>$of Process ID$cf</td>
</tr>
<tr>
<td>$of\$^O $cf</td>
<td>$of$^O $cf&nbsp;</td>
<td>$of Operating System$cf</td>
</tr>
<tr>
<td>$of\$! $cf</td>
<td>$of$!$cf&nbsp;</td>
<td>$of<a href="javascript:alert('If the error says No such file or directory, it is because this script tries to guess the location of sendmail.')">Error returned by server</a>$cf</td>
</tr>
</table>
<br>

<center>
$of<a href="javascript:alert('This is the complete list of standard modules contained in \@INC. \\n\\nClick on the module name to search for it\\'s documentation in the Cpan.org website')"><b>List of Modules Installed on this server</b></a>$cf
</center>
<br>
<table align="center" border="1" cellpadding="5" cellspacing="0" width="600">
<tr>
<td>$of<b>Name</b>$cf</td>
<td>$of<b>Name</b>$cf</td>
</tr>
<tr>
<td>
~;

find(\&wanted, @INC);

@found = sort { uc($a) cmp uc($b) } @found;

for($c = 0; $c < int(@found / 2); $c++){
	$search = $found[$c];
	$search =~ s/\.pm$//i;
	print qq~$of <a href="http://search.cpan.org/search?mode=module&query=$search">$found[$c]</a> <br>\n~;
}

print qq~$cf</td><td>~;

for($d = $c; $d < @found; $d++){
	$search = $found[$d];
	$search =~ s/\.pm$//i;
	print qq~$of <a href="http://search.cpan.org/search?mode=module&query=$search">$found[$d]</a><br>\n~;
}

($sec, $min, $hour, $day, $mon, $year, $weekday, $dayofyear, $dst) = localtime(time);

$year += 1900;

print qq~$cf</td></tr>
</table>
<br>
<center>
$of <a href="http://www.perlscriptsjavascripts.com/?evs"><b>Copyright $year PerlScriptsJavaScripts.com</b></a>$cf 
</center>
<br>
</body>
</html>
~;

sub wanted {
	use File::Find;
	$num = 0;	
	if ($File::Find::name =~ /\.pm$/){
		if(open(M,$File::Find::name)){
			while(<M>){
				if (/^ *package +(\S+);/){
					push (@found, $1);
					last;
				}
			}
			chomp(@found);
		}
	}
}
