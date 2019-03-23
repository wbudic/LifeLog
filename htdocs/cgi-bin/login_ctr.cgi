#!/usr/bin/perl

use strict;
use warnings;
use Try::Tiny;
use Switch;
 
use CGI;
use CGI::Session;
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Text::CSV;

my $driver   = "SQLite"; 
my $database = "../../dbLifeLog/data_config_test_log.db";
my $dsn = "DBI:$driver:dbname=$database";
my $userid = $ENV{'DB_USER'};
my $password = $ENV{'DB_PASS'};



my $rv;
my $dbs;


my $q = CGI->new;
	
print $q->header(-expires=>"+6os", -charset=>"UTF-8");    
print $q->start_html(-title => "Personal Log", 
       		     -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
		     -style =>{-type => 'text/css', -src => 'wsrc/main.css'},
		        );	  
my  $frm = qq(
	 <form id="frm_login" action="login_ctr.cgi"><table>
	        <tr class="r0">
		 <td colspan="3"><center>LOGIN</center></td>
		</tr>
	        <tr class="r1">
		 <td>Alias:</td><td><input type="text" name="alias"/></td><td></td>
		</tr>
	        <tr class="r1">
		 <td>Password:</td><td><input type="text" name="password"/></td><td></td>
		</tr>
		<tr class="r1">
		<td colspan="3"><font color="red">NOTICE!</font> &nbsp;If here the first time? Write down your alias and password, before proceeding. So you can comeback in the future to continue. Only you can know it.
<input type="hidden" name="login" value="1"/></td></tr></table></form>);
	 

print "<center>";
	print "\n<div>\n" . $frm ."\n</div>\n<br/>";
print "</center>";


print $q->end_html;
exit;

### CGI END


