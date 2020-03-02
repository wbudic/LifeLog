#!/usr/bin/perl -w
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Switch;

use CGI;
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use DBI;
use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Date::Language;
use Text::CSV;
use Scalar::Util qw(looks_like_number);
use Sys::Syslog qw(:DEFAULT :standard :macros);

#DEFAULT SETTINGS HERE!
use lib "system/modules";
require Settings;
##

#15mg data post limit
$CGI::POST_MAX = 1024 * 15000;
my ($LOGOUT,$ERROR) = (0,"");
my $cgi = CGI->new;
my $session = new CGI::Session("driver:File", $cgi, {Directory=>&Settings::logPath});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $pass    =$session->param('passw');
my $sys     = `uname -n`;
#my $acumululator="";

if(!$userid||!$dbname){
    print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
    exit;
}

my $database = &Settings::logPath.$dbname;
my $dsn= "DBI:SQLite:dbname=$database";
my $db = DBI->connect($dsn, $userid, $pass, { RaiseError => 1 }) or die "<p>Error->"& $DBI::errstri &"</p>";

### Fetch settings
    Settings::getConfiguration($db);
    Settings::getTheme();
###

my $rv;
my $dbs;
my $lang   = Date::Language->new(&Settings::language);
my $today  = DateTime->now;
   $today->set_time_zone( &Settings::timezone );
my $tz     = $cgi->param('tz');
my $csvp   = $cgi->param('csv');

&exportToCSV if ($csvp);

if($cgi->param('bck')){
    &backup;
}
elsif($cgi->param('bck_del')){
    &backupDelete;
}
elsif($cgi->param('data_bck')){
    &restore;
}
elsif($cgi->param('data_cat')){
    &importCatCSV;
}elsif($cgi->param('data_log')){
    &importLogCSV;
}



my $stmtCat = 'SELECT * FROM CAT ORDER BY ID;';
my $status = "Ready for change!";
my $cats;
my %hshCats = {};
&cats;

###############
&processSubmit;
###############
Settings::getTheme();
$session->param("theme",&Settings::css);
$session->param("bgcolor",&Settings::bgcol);

&getHeader;

 if ($ERROR){&error;}else{
print qq(<div id="menu" title="To close this menu click on its heart, and wait.">
<div class="hdr" style="marging=0;padding:0px;">
<a id="to_top" href="#top" title="Go to top of page."><span class="ui-icon ui-icon-arrowthick-1-n" style="float:none;"></span></a>&nbsp;
<a id="to_bottom" href="#bottom" title="Go to bottom of page."><span class="ui-icon ui-icon-arrowthick-1-s" style="float:none;"></span></a>
<a id="menu_close" href="#" onclick="return hide('menu_close');"><span  class="ui-icon ui-icon-heart" style="float:none;"></span></a>
</div>
<hr>
<a class="a_" href="stats.cgi">Stats</a><hr>
<a class="a_" href="main.cgi">Log</a><hr>
<font size="2"><b>Jump to Sections</b><br>
<a href="#categories">Categories</a><br>
<a href="#vars">System</a><br>
<a href="#dbsets">DB Fix</a><br>
<a href="#passets">Pass</a><br>
<a href="#backup">Backup</a>
</font>
<hr>
<br>
<a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a>
</div>);
}

my $tbl = '<table id="cnf_cats" class="tbl" border="1" width="'.&Settings::pagePrcWidth.'%">
              <tr class="r0"><td colspan="4"><b>* CATEGORIES CONFIGURATION *</b></td></tr>
            <tr class="r1"><th>ID</th><th>Category</th><th  align="left">Description</th></tr>
          ';
$dbs = Settings::selectRecords($db, $stmtCat);
while(my @row = $dbs->fetchrow_array()) {
    if( $row[0]>0 ){
       $tbl .= '<tr class="r0"><td>'.$row[0].'</td>
            <td><input name="nm'.$row[0].'" type="text" value="'.$row[1].'" size="12"></td>
            <td align="left"><input name="ds'.$row[0].'" type="text" value="'.$row[2].'" size="64"></td>
        </tr>';
    }
 }

my  $frmCats = qq(
     <form id="frm_config" action="config.cgi">).$tbl.qq(
      <tr class="r1">
         <td><input type="text" name="caid" value="" size="3"/></td>
         <td><input type="text" name="canm" value="" size="12"/></td>
         <td align="left"><input type="text" name="cade" value="" size="64"/></td>
        </tr>
      <tr class="r1">
         <td colspan="2"><a href="#bottom">&#x21A1;</a>&nbsp;&nbsp;&nbsp;
         <input type="submit" value="Add New Category First" onclick="return submitNewCategory()"/> or <input type="submit" value="Change"/></td>
         <td colspan="1" align="right"><b>Categories Configuration In -> $dbname</b>&nbsp;
         <input type="submit" value="Change" onclick="return checkConfigCatsChange()"/></td>
        </tr>
        <tr class="r1">
          <td colspan="3"><div style="text-align:left; float"><font color="red">WARNING!</font>
           Removing or changing categories is permanent! Each category one must have an unique ID.
             Blank a category name to remove it. LOG records will change to the
             <b>Unspecified</b> (id 1) category! And the categories <b>Unspecified</b>, <b>Income</b> and <b>Expense</b>  can't be removed!
             </div>
            </td>
        </tr>
        </table><input type="hidden" name="cchg" value="1"/></form><br>);


$tbl = qq(<table id="cnf_sys" class="tbl" border="1" width=").&Settings::pagePrcWidth.qq(%">
              <tr class="r0"><td colspan="3"><b>* SYSTEM CONFIGURATION *</b></td></tr>
            <tr class="r1" align="left">
                            <th width="20%">Variable</th>
                            <th width="20%">Value</th>
                            <th width="60%">Description <input type="submit" value="Change" style="float:right"/></th>
                        </tr>
       );
my $stm = 'SELECT ID, NAME, VALUE, DESCRIPTION FROM CONFIG ORDER BY NAME;';
   $dbs = Settings::selectRecords($db, $stm);
my $REL ="";
while(my @row = $dbs->fetchrow_array()) {

         my $n = $row[1]; next if($n =~ m/^\^/); #skip private tagged settings
         my $i = $row[0];
         my $v = $row[2];
         my $d = $row[3];

         if($n eq "TIME_ZONE"){
              $n = '<a href="time_zones.cgi" target=_blank>'.$n.'</a>';
              if($tz){
                   $v = $tz;
              }
              $v = '<input name="var'.$i.'" type="text" value="'.$v.'" size="12">';
         }
         elsif($n eq "DATE_UNI"){
              my($l,$u)=("","");
                if($v == 0){
                     $l = "SELECTED"
                }
                else{
                 $u = "SELECTED"
                }
        $v = qq(<select id="dumi" name="var$i">
                         <option value="0" $l>Locale</option>
                                 <option value="1" $u>Universal</option>
                                </select>);
         }
         elsif($n eq "AUTO_LOGIN"){
              my($l,$u)=("","");
                if($v == 0){
                     $l = "SELECTED"
                }
                else{
                 $u = "SELECTED"
                }
        $v = qq(<select id="almi" name="var$i">
                   <option value="0" $l>Disabled</option>
                   <option value="1" $u>Enabled</option>
                </select>);
         }
         elsif($n eq "FRAME_SIZE"){
              my($l,$m,$s, $t)=("","");
                if($v == 0){
                     $l = "SELECTED"
                }
                elsif($v == 1){
                     $m = "SELECTED"
                }
                elsif($v == 2){
                     $s = "SELECTED"
                }
                else{
                      $t = $v;
                }
        $v = qq(<select id="frms" name="var$i">
                   <option value="0" $l>Large</option>
                   <option value="1" $m>Medium</option>
                   <option value="2" $s>Small</option>
                   <option value="3" $t>---</option>
                </select>);
        }
        elsif($n eq "RTF_SIZE"){
                my($l,$m,$s, $t)=("","");
                if($v == 0){
                     $l = "SELECTED"
                }
                elsif($v == 1){
                     $m = "SELECTED"
                }
                elsif($v == 2){
                     $s = "SELECTED"
                }
                else{
                      $t = $v;
                }
        $v = qq(<select id="rtfs" name="var$i">
                   <option value="0" $l>Large</option>
                   <option value="1" $m>Medium</option>
                   <option value="2" $s>Small</option>
                   <option value="3" $t>---</option>
                </select>);

        }
        elsif($n eq "THEME"){
            my($s0,$s1,$s2,$s3)=("","","","");
             if($v eq 'Standard'){
                $s0 = " SELECTED";
            }
            elsif($v eq 'Sun'){
                $s1 = " SELECTED";
            }
            elsif($v eq 'Moon'){
                $s2 = " SELECTED";
            }
            elsif($v eq 'Earth'){
                $s3 = " SELECTED";
            }

            $v = qq(<select id="theme" name="var$i">
                   <option$s0>Standard</option>
                   <option$s1>Sun</option>
                   <option$s2>Moon</option>
                   <option$s3>Earth</option>
                </select>);
        }
        elsif($n eq "KEEP_EXCS" or $n eq 'TRACK_LOGINS' or $n eq 'DEBUG'){
            my($l,$u)=("","");
            if($v == 0){
               $l = "SELECTED"
            }
            else{
               $u = "SELECTED"
            }
            $v = qq(<select id="onoff" name="var$i">
                   <option value="0" $l>Off</option>
                   <option value="1" $u>On</option>
                </select>);
        }

        elsif($n eq "RELEASE_VER"){
            $REL = qq(<td>$n</td>
                      <td>$v</td>
                      <td>$d</td>);
            next;
        }
        else{
            $v = '<input name="var'.$i.'" type="text" value="'.$v.'" size="12">';
        }



       $tbl = qq($tbl
       <tr class="r0" align="left">
            <td>$n</td>
            <td>$v</td>
            <td>$d</td>
        </tr>);
}

$tbl = qq($tbl<tr class="r1" align="left">$REL</tr>); #RELEASE VERSION we make outstand last, can't be changed. :)

my  $frmVars = qq(
     <form id="frm_vars" action="config.cgi">$tbl
      <tr class="r1">
         <td colspan="3" align=right><b>System Settings In -> $dbname</b>&nbsp;<input type="submit" value="Change"/></td>
        </tr>
        </table><input type="hidden" name="sys" value="1"/></form><br>);



$tbl = qq(<table id="cnf_fix" class="tbl" border="0" width=").&Settings::pagePrcWidth.qq(%">
              <tr class="r0"><td colspan="2"><b>* DATA FIX *</b></td></tr>
             );

my  $frmDB = qq(
     <form id="frm_DB" action="config.cgi">$tbl
        <tr class="r1" align="left"><th>Extra Action</th><th>Description</th></tr>
        <tr class="r0" align="left"><td><input type="checkbox" name="reset_cats"/>Reset Categories</td><td>Resets Categories to factory values (will initiate logoff).</td></tr>
        <tr class="r1" align="left"><td><input type="checkbox" name="reset_syst"/>Reset Settings</td><td>Resets system settings to default values.</td></tr>
        <tr class="r0" align="left"><td><input type="checkbox" name="wipe_syst"/>Wipe Settings</td><td>Resets and wipes system settings for migration  (will initiate logoff).</td></tr>
        <tr class="r1" align="left"><td><input type="checkbox" name="del_by_cats"/>Delete by Category <font color=red></font><br>
        $cats</td><td>Selects and displays by category logs to delete.</td></tr>
        <tr class="r0" align="left"><td><input type="checkbox" name="del_from"/>Delete from Date <br>
        <input id="fldFrom" name="date_from"/></td><td>Selects and displays from a date to into deep past logs to delete..</td></tr>
        <tr class="r1">
         <td colspan="2" align="right"><b>Data maintenance for -> $dbname</b>&nbsp;<input type="submit" value="Fix"/></td>
        </tr>
        <tr class="r1" align="left">
             <td colspan="2">Perform this change/check in the event of experiencing data problems. Or periodically for data check and maintenance. <br>
                                 <font color="red">WARNING!</font> Checking any of the above extra actions will cause loss
                                                  of your changes. Please, export/backup first.</td>
        </tr>
        </table><input type="hidden" name="db_fix" value="1"/></form><br>
        );
$tbl = qq(<table id="cnf_fix" class="tbl" border="1" width=").&Settings::pagePrcWidth.qq(%">
              <tr class="r0"><td colspan="2"><b>* CHANGE PASS *</b></td></tr>
             );
my  $frmPASS = qq(
     <form id="frm_PASS" action="config.cgi">$tbl
        <tr class="r1" align="left"><td style="width:100px">Existing:</td><td><input type="pass" name="existing" value="" size="12"/></td></tr>
        <tr class="r1" align="left"><td>New:</td><td><input type="pass" name="new" value="" size="12"/></td></tr>
        <tr class="r1" align="left"><td>Confirmation:</td><td><input type="pass" name="confirm" value="" size="12"/></td></tr>
        <tr class="r1">
         <td colspan="2" align="right"><b>Pass change for -> $userid</b>&nbsp;<input type="submit" value="Change"/></td>
        </tr>
        </table><input type="hidden" name="pass_change" value="1"/></form><br>
        );


my @backups = ();
my ($file,$bck_list) ="";
opendir my $dir, &Settings::logPath;
while($file = readdir $dir){
next if $file eq '.' or $file eq '..' or index ($file , 'bck_') == -1;
  push @backups, $file;
}
close $dir;
foreach $file (sort @backups){
    #my $n = substr $file, length(&Settings::logPath);
    $bck_list .=  "<input name='bck_file' type='radio' value='$file'>$file</input><br>";
}
if(length $bck_list == 0){
$bck_list = '<p>Restore will bring back and merge log entries from the time of backup.</p>';
}
else{
    $bck_list = qq(<p>Tick Select Backup to Restore or Delete</p><p>$bck_list</p>);
}

#
#  Page printout from here!
#

print qq(
<a name="top"></a><center>
    <div><a name="vars"></a>$frmVars</div>
    <div><a name="categories"></a>$frmCats</div>
    <div><a name="dbsets"></a>$frmDB</div>
    <div><a name="passets"></a>$frmPASS</div>
    <div id="rz" style="text-align:center;width:).&Settings::pagePrcWidth.qq(%;">
                <a href="#top">&#x219F;</a>&nbsp;Configuration status -> <b>$status</b>&nbsp;<a href="#bottom">&#x21A1;</a>
    </div>
    <br>
    <div id="rz" style="text-align:left; width:640px; padding:10px; background-color:).&Settings::bgcol.qq(">
            <form id="bck" action="config.cgi" method="post" enctype="multipart/form-data">
            <table border="0" width="100%">
                <tr><td><a name="backup"></a><H3>Backup File Format</H3></td></tr>
                <tr><td><input type="button" onclick="return fetchBackup();" value="Fetch"/><hr></td></tr>

                <tr><td><div id="div_backups">$bck_list</div><hr></td></tr>
                <tr><td><input type="button" onclick="return deleteBackup();" value="Delete"/> <input type="file" name="data_bck" />&nbsp;&nbsp;<input type="Submit" onclick="return true;restoreBackup();" value="Restore"/><hr></td></tr>


                <tr><td><H3>CSV File Format</H3></td></tr>

                <tr style="border-left: 1px solid black;"><td>
                        <b>Import Categories</b>: <input type="file" name="data_cat" /></td></tr>
                <tr style="border-left: 1px solid black;"><td style="text-align:right;">
                        <input type="submit" name="Submit" value="Submit"/></td>
                </tr>

                </form>
                <form action="config.cgi" method="post" enctype="multipart/form-data">
                <tr><td><b>Export Categories:</b>
                                           <input type="button" onclick="return exportToCSV('cat',0);" value="Export"/>&nbsp;
                                           <input type="button" onclick="return exportToCSV('cat',1);" value="View"/>
                </td></tr>
                <tr style="border-top: 1px solid black;border-right: 1px solid black;"><td>
                        <b>Import Log</b>: <input type="file" name="data_log" /></td></tr>
                <tr style="border-right: 1px solid black;"><td style="text-align:right;">
                        <input type="submit" name="Submit" value="Submit"/></td></tr>
                </form>
                <tr><td><b>Export Log:</b>
                                           <input type="button" onclick="return exportToCSV('log',0);" value="Export"/>&nbsp;
                                           <input type="button" onclick="return exportToCSV('log',1);" value="View"/>
                </td></tr>
                <tr><td style="text-align:right"><H3>For Server -> $sys -> $dbname</H3></td></tr>
            </table><br><a href="#top">&#x219F;&nbsp;Go to Top of page</a>
    </div>
   <hr>

    <div id="rz" style="text-align:left; position:relative;width:640px; padding:10px;">
                    <h2>L-Tags Specs</h2>
                    <p>
                    Life Log Tags are simple markup allowing fancy formatting and functionality
                    for your logs HTML layout.
                    </p>
                    <p>
                    <b>&#60;&#60;B&#60;<i>{Text To Bold}</i><b>&#62;&#62;</b>
                    </p>
                    <p>
                    <b>&#60;&#60;I&#60;<i>{Text To Italic}</i><b>&#62;&#62;</b>
                    </p>
                    <p>
                    <b>&#60;&#60;TITLE&#60;<i>{Title Text}</i><b>&#62;&#62;</b>
                    </p>
                    <p>
                    <b>&#60;&#60;LIST&#60;<i>{List of items delimited by new line to terminate item or with '~' otherwise.}</i><b>&#62;&#62;</b>
                    </p>
                    <p>
                    <b>&#60;&#60;IMG&#60;<i>{url to image}</i><b>&#62;&#62;</b>
                    </p>
                    <p>
                        <b>&#60;&#60;FRM&#60;<i>{file name}_frm.png}</i><b>&#62;&#62;</b><br><br>
                        *_frm.png images file pairs are located in the ./images folder of the cgi-bin directory.<br>
                        These are manually resized by the user. Next to the original.
                        Otherwise considered as stand alone icons. *_frm.png Image resized to ->  width="210" height="120"
                        <br><i>Example</i>:
                        <pre>
        ../cgi-bin/images/
            my_cat_simon_frm.png
            my_cat_simon.jpg

          For log entry, place:

      &#60;&#60;FRM&#62;my_cat_simon_frm.png&#62; &#60;&#60;TITLE&#60;Simon The Cat&#62;&#62;
      This is my pet, can you hold him for a week while I am on holiday?
                        </pre>
                    </p>

                    <p><b>&#60;&#60;LNK&#60;<i>{url to image}</i><b>&#62;&#62;</b><br><br></p>
                     <p>
                    Explicitly tag an URL in the log entry.
                    Required if using in log IMG or FRM tags.
                    Otherwise link appears as plain text.
                    </p>
                    <hr>
                        <h3>Log Page Particulars</h3>
                        &#x219F; or &#x21A1; - Jump links to top or bottom of page respectivelly.
                    </center><a name="bottom"></a><a href="#top">&#x219F;</a>
                    <hr>
</div>
<br>
<div>
            <a href="main.cgi"><h3>Back to Main Log</h3></a><h3><a href="login_ctr.cgi?logout=bye">LOGOUT</a></h3>
</div>
);


print $cgi->end_html;
$db->disconnect();

exit;

sub getHeader {
print $cgi->header(-expires=>"+6s", -charset=>"UTF-8");
print $cgi->start_html(-title => "Personal Log", -BGCOLOR=>&Settings::bgcol,
           -onload  => "onBodyLoadGeneric();",
            -style   => [
          { -type => 'text/css', -src => "wsrc/".&Settings::css },
          { -type => 'text/css', -src => 'wsrc/jquery-ui.css' },
          { -type => 'text/css', -src => 'wsrc/jquery-ui.theme.css' },
          {
              -type => 'text/css',
              -src  => 'wsrc/jquery-ui-timepicker-addon.css'
          },
          { -type => 'text/css', -src => 'wsrc/tip-skyblue/tip-skyblue.css' },
          {
              -type => 'text/css',
              -src  => 'wsrc/tip-yellowsimple/tip-yellowsimple.css'
          },
      ],
      -script => [
          { -type => 'text/javascript', -src => 'wsrc/main.js' },
          { -type => 'text/javascript', -src => 'wsrc/jquery.js' },
          { -type => 'text/javascript', -src => 'wsrc/jquery-ui.js' },
          {
              -type => 'text/javascript',
              -src  => 'wsrc/jquery-ui-timepicker-addon.js'
          },
          {
              -type => 'text/javascript',
              -src  => 'wsrc/jquery-ui-sliderAccess.js'
          },
          { -type => 'text/javascript', -src => 'wsrc/jquery.poshytip.js' }
      ],
            );
}

sub processSubmit{

my $change = $cgi->param("cchg");
my $chgsys = $cgi->param("sys");
my $chdbfix  = $cgi->param("db_fix");
my $passch = $cgi->param("pass_change");
my $del_by_cats = $cgi->param("del_by_cats");
my $category = $cgi->param("cats");
my $del_by_date = $cgi->param("del_from");
my $del_date_from = $cgi->param("date_from");
my ($s, $d);

try{
$dbs = Settings::selectRecords($db, $stmtCat );
if($passch){
    my ($ex,$ne,$cf) = ($cgi->param("existing"),$cgi->param("new"),$cgi->param("confirm"));
    if($ne ne $cf){
         $status = "New pass must match confirmation!";
         print "<center><div><p><font color=red>Client Error</font>: $status</p></div></center>";
    }
    else{
        if(&confirmExistingPass($ex)){
             &changePass($ne);
             $status = "Pass Has Been Changed";
        }
        else{
            $status = "Wrong existing pass was entered, are you user by alias: $userid ?";
            print "<center><div><p><font color=red>Client Error</font>: $status</p></div></center>";
        }
    }

    openlog($dsn, 'cons,pid', "user");
        syslog('info', 'Status:%s', $status);
        syslog('info', 'Password change request for %s', $$userid);
    closelog();


}
elsif ($change == 1){

    while(my @row = $dbs->fetchrow_array()) {

          my $cid = $row[0];
          my $cnm = $row[1];
          my $cds = $row[2];

          my $pnm  = $cgi->param('nm'.$cid);
          my $pds  = $cgi->param('ds'.$cid);

      if($pnm ne $cnm || $pds ne $cds){

         if( ($cid!=1 && $cid!=32 && $cid!=35) && $pnm eq  ""){

           $s = "SELECT rowid, ID_CAT FROM LOG WHERE ID_CAT =".$cid.";";
           $d = $db->prepare($s);
           $d->execute();

            while(my @r = $d->fetchrow_array()) {
                     $s = "UPDATE LOG SET ID_CAT=1 WHERE rowid=".$r[0].";";
                     $d = $db->prepare($s);
                     $d->execute();
             }

            #Delete
            $s = "DELETE FROM CAT WHERE ID=".$cid.";";
            $d = $db->prepare($s);
            $d->execute();

        }else{
            #Update
            $s = "UPDATE CAT SET NAME='".$pnm."', DESCRIPTION='".$pds."' WHERE ID=".$cid.";";
               $d = $db->prepare($s);
               $d->execute();
        }
      }
    }
    $status = "Updated Categories!";
}


if($change > 1){

    my $caid  = $cgi->param('caid');
    my $canm  = $cgi->param('canm');
    my $cade  = $cgi->param('cade');
    my $valid = 1;

    while(my @row = $dbs->fetchrow_array()) {

        my $cid = $row[0];
        my $cnm = $row[1];
        my $cds = $row[2];


        if($cid==$caid || $cnm eq $canm){
                        $valid = 0;
                        last;
        }
    }

    if($valid){
        $d = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
        $d->execute($caid,$canm, $cade);
        $status = "Added Category $canm!";
    }
    else{
        $status = "ID->".$caid." or -> Category->".$canm." is already assigned, these must be unique!";
        die "<div><p><font color=red>Client Error</font>: $status</p></div>";
    }
    $status = "Inserted new category[$canm]";


}elsif ($chgsys == 1){
    &changeSystemSettings;
    $status = "Changed System Settings!";
}
elsif($chdbfix){

    my $isByCat = ($del_by_cats eq 'on' && $category > 0);
    my $isByDate = ($del_by_date eq 'on');


    if( $isByCat || $isByDate){

        my $output = qq(<form id="frm_log" action="remove.cgi" onSubmit="return formDelValidation();">
                    <TABLE class="tbl" border="0" width=").&Settings::pagePrcWidth.qq(%">
                    <tr class="hdr"><td colspan="5"><h2>Select Categories To Delete</h2></td></tr>
                    <tr class="r0">
                        <th>Date</th>
                        <th>Time</th>
                        <th>Log</th><th>#</th>
                        <th>Category</th>
                    </tr>);
        my $sel ="";
        if ($isByCat){$sel = "ID_CAT ='$category'"}
        if($isByDate){
            if ($isByCat){ $sel .= " AND ";}
            $sel .= "DATE<='$del_date_from'";
        }


       $dbs = Settings::selectRecords($db, "SELECT rowid, ID_CAT, DATE, LOG FROM LOG WHERE $sel ORDER BY DATE;" );
       while(my @row = $dbs->fetchrow_array()) {
        my $id = $row[0];# rowid
            my $ct  = $hshCats{$row[1]}; #ID_CAT
            my $dt  = DateTime::Format::SQLite->parse_datetime( $row[2] );
            my $log = $row[3];

            my ( $dty, $dtf ) = $dt->ymd;
            my $dth = $dt->hms;
            if ( &Settings::universalDate == 1 ) {
                $dtf = $dty;
            }
            else {
                $dtf = $lang->time2str( "%d %b %Y", $dt->epoch, &Settings::timezone );
            }

            $output .= qq(<tr class="r0">
                    <td width="15%">$dtf<input id="y$id" type="hidden" value="$dty"/></td>
                    <td id="t$id" width="10%" class="tbl">$dth</td>
                    <td id="v$id" class="log" width="40%">$log</td>
                    <td id="c$id" width="10%" class="tbl">$ct</td>
                    <td width="20%">
                        <input name="chk" type="checkbox" value="$id"/>
                    </td></tr>);
       }#while
       $output .= qq(<td colspan="5" align="right">
        <button onclick="return selectAllLogs()">Select All</button>
        <input type="reset" value="Unselect All"/>
        <input id="del_sel" type="submit" value="Delete Selected"/>
        </td></tr>
        </form></TABLE>);

        &getTheme;
        &getHeader;

        print "<div>$output</div>";

        print $cgi->end_html;
        $db->disconnect();
        exit;

    }
    else{
        &processDBFix;
    }
    $status = "Performed Database Fixes!";
}


}
catch{

        my $err = $@;
        my $pwd = `pwd`;
           $pwd =~ s/\s*$//;

        $ERROR =
        "<hr><font color=red><b>SERVER ERROR</b></font> on ".DateTime->now.
        "<hr><pre>".$pwd."/$0 -> &".caller." -> [$err]","</pre>",



}

    openlog($dsn, 'cons,pid', "user");
        syslog('info', 'Status:%s', $status);
        syslog('err', '%s', $ERROR) if ($ERROR);
    closelog();
}

sub confirmExistingPass {
        my $pass = $_[0];
        my $crypt = encryptPassw($pass);
        my $sql = "SELECT ALIAS, PASSW from AUTH WHERE ALIAS='$userid' AND PASSW='$crypt';";
    #		print "<center><div><p><font color=red><b>DEBUG</b></font>:[$pass]<br>$sql</p></div></center>";
        $dbs = Settings::selectRecords($db, $stmtCat );
        if($dbs->fetchrow_array()){
            return 1;
        }
        return 0;
}
sub changePass {
      my $pass = encryptPassw($_[0]);
        $dbs = Settings::selectRecords($db, "UPDATE AUTH SET PASSW='$pass' WHERE ALIAS='$userid';");
        if($dbs->fetchrow_array()){
            return 1;
        }
        return 0;
}
sub encryptPassw {
    return uc crypt $_[0], hex Settings->CIPHER_KEY;
}



sub processDBFix {

     my $rs_syst = $cgi->param("reset_syst");
     my $rs_cats = $cgi->param("reset_cats");
     my $wipe_ss = $cgi->param("wipe_syst");


     my $sql;
     my $date;
     my $cntr_upd =0;
try{


        my %dates  = ();
        my @dlts = ();
        #Hash is unreliable for returning sequential order of keys so array must do.
        my @updts = ();
        my $cntr_del =0;
        my $existing;
        my @row;

        $db->do('BEGIN TRANSACTION;');
        #Check for duplicates, which are possible during imports or migration as internal rowid is not primary in log.
        $dbs = Settings::selectRecords($db, 'SELECT rowid, DATE FROM LOG ORDER BY DATE;');
        while(@row = $dbs->fetchrow_array()) {
            my $existing = $dates{$row[0]};
            if($existing && $existing eq $row[1]){
                $dlts[$cntr_del++] = $row[0];
            }
            else{
                $dates{$row[0]} = $row[1];
                $updts[$cntr_upd++] = $row[0];
            }
        }

        foreach my $del (@dlts){
            $sql = "DELETE FROM LOG WHERE rowid=$del;";
                    #print "$sql\n<br>";
                    my $st_del = $db->prepare($sql);
                    $st_del->execute();
        }

        &renumerate;
        &Settings::removeOldSessions;
        &resetCategories if $rs_cats;
        &resetSystemConfiguration($db) if $rs_syst;
        &wipeSystemConfiguration if $wipe_ss;



        $db->do('COMMIT;');
        $db->disconnect();
        $db = DBI->connect($dsn, $userid, $pass, { RaiseError => 1 }) or LifeLogException->throw($DBI::errstri);
        $dbs = $db->do("VACUUM;");


        if($LOGOUT){
                &logout;
        }


}
catch{
    $db->do('ROLLBACK;');
    LifeLogException->throw(error=>qq(@&processDBFix error -> $_ with statement->[$sql] for $date update counter:$cntr_upd \nERROR->$@),show_trace=>1);
}
}

sub resetCategories {
    $db->do("DELETE FROM CAT;");
    $db->do("DROP TABLE CAT;");
    $LOGOUT = 1;
}

sub wipeSystemConfiguration {
    $db->do("DELETE FROM CONFIG;");
    $db->do("DROP TABLE CONFIG;");
    $LOGOUT = 1;
}


sub resetSystemConfiguration {

        open(my $fh, '<', &Settings::logPath.'main.cnf' ) or die "Can't open main.cnf: $!";
        my $db = shift;
        my ($id,$name, $value, $desc);
        my $inData = 0;
        my $err = "";
        my %vars = {};

try{
        my $insert = $db->prepare('INSERT INTO CONFIG VALUES (?,?,?,?)');
        my $update = $db->prepare('UPDATE CONFIG SET VALUE=? WHERE ID=?;');
        my $updExs = $db->prepare('UPDATE CONFIG SET NAME=?, VALUE=? WHERE ID=?;');
        $dbs->finish();
    while (my $line = <$fh>) {
                    chomp $line;
                    my @tick = split("`",$line);
                    if(scalar(@tick)==2){
                                    my %hsh = $tick[0] =~ m[(\S+)\s*=\s*(\S+)]g;
                                    if(scalar(%hsh)==1){
                                            for my $key (keys %hsh) {

                                                    my %nash = $key =~ m[(\S+)\s*\|\$\s*(\S+)]g;
                                                    if(scalar(%nash)==1){
                                                            for $id (keys %nash) {
                                                                $name  = $nash{$id};
                                                                $value = $hsh{$key};
                                                                if($vars{$id}){
                            $err .= "UID{$id} taken by $vars{$id}-> $line\n";
                                                                }
                                                                else{
                                                                    $dbs = Settings::selectRecords($db,
                                                                        "SELECT ID, NAME, VALUE, DESCRIPTION FROM CONFIG WHERE NAME LIKE '$name';");
                                                                    $inData = 1;
                                                                    my @row = $dbs->fetchrow_array();
                                                                    if(scalar @row == 0){
                                                                       #The id in config file has precedence to the one in the db,
                                                                       #from a ppossible previous version.
                                                                       $dbs = Settings::selectRecords($db, "SELECT ID FROM CONFIG WHERE ID = $id;");
                                                                       @row = $dbs->fetchrow_array();
                                                                       if(scalar @row == 0){
                                                                            $insert->execute($id,$name,$value,$tick[1]);
                                                                       }else{
                                                                            #rename, revalue exsisting id
                                                                            $updExs->execute($name,$value,$id);
                                                                        }
                                                                    }
                                                                    else{
                                                                            $update->execute($value,$id);
                                                                    }
                                                                }
                                                            }
                                                    }else{
                            $err .= "Invalid, spec'ed {uid}|{setting}`{description}-> $line\n";
                                                    }

                                            }#rof
                                    }
                                    else{
                            $err .= "Invalid, speced entry -> $line\n";
                                    }

                    }elsif($inData && length($line)>0){
                    if(scalar(@tick)==1){
                             $err .= "Corrupt Entry, no description supplied -> $line\n";
                        }
                        else{
                           $err .= "Corrupt Entry -> $line\n";
                        }
                    }
        }
        #die "Configuration script './main.cnf' [$fh] contains errors." if $err;
        close $fh;
       Settings::getConfiguration($db);
 } catch{
      close $fh;
      print $cgi->header;
        print "<font color=red><b>SERVER ERROR! [id:$id,name:$name,value:$value]/b></font><br> ".$_."<br><pre>$err</pre>";
    print $cgi->end_html;
        exit;
 }
}

sub logout {
    $session->delete();
    $session->flush();
    print $cgi->redirect("login_ctr.cgi");
    exit;
}

sub changeSystemSettings {
    my $updated;
    $dbs = Settings::selectRecords($db, "SELECT ID, NAME FROM CONFIG;");
    while (my @r=$dbs->fetchrow_array()){
        my $var = $cgi->param('var'.$r[0]);
        if(defined $var){
            Settings::configProperty($db, $r[0], undef, $var);
            $updated = 1;
        }
    }
    Settings::getConfiguration($db) if($updated);
}


sub backupDelete {
    my $n = $cgi->param('bck_del');
    my $f = &Settings::logPath.$n;
try{
    if (-e $f) {
         LifeLogException->throw("File -> <i>[$n]</i> is not a backup file or it doesn't belong to $userid (you)!") if(index ($file , /bck_\d+$userid\_log/) == -1 );
         unlink($f) or LifeLogException->throw("Failed to delete $n! -> $!");
         print $cgi->redirect("config.cgi?CGISESSID=$sid");
    exit;
    } else {
        LifeLogException->throw( "File $n does not exist!");
    }
}catch{
        my $err = $@;
        &getHeader;
        print $cgi->start_html;
        print qq(<div class=r0><b>Delete Has Failed!<br>[$err]</div>
                 <div class=r2><a href="config.cgi?CGISESSID=$sid"><br>Go Back</a> or <a href="main.cgi"><br>Go to main LOG</a></div>
        );
        print $cgi->end_html;
        exit;
};
}
sub backup {

   my $ball = 'bck__'.$today->strftime('%Y%m%d%H%M%S_')."$dbname.osz";
   my $pipe = "tar czf - ".&Settings::logPath.'main.cnf' ." $database | openssl enc -k $pass:$userid -e -des-ede3-cfb -out ".Settings::logPath().$ball." 2>/dev/null";
   my $rez = `$pipe`;

    #print $cgi->header;
    #print $cgi->start_html;
    print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>$ball);
    open (TAR, "<".Settings::logPath().$ball) or die "Failed creating backup -> $ball";
    while(<TAR>){print $_;}
    close TAR;

    #print $cgi->end_html;
    exit;

}


sub restore {

    my $hndl = $cgi->upload("data_bck");
    my ($pipe,@br);
    try{


        &getHeader;
        print $cgi->start_html;
        print "<pre>Reading->$hndl</pre>";
        my $dbck = &Settings::logPath."bck/"; `mkdir $dbck` if (!-d $dbck);
        my $tar = $dbck.$hndl; $tar =~ s/osz$/tar/;
        my $pipe;
        open ($pipe,  "| openssl enc -k $pass:$userid -d -des-ede3-cfb -in /dev/stdin 2>/dev/null > $tar"); #| tar zt");#1>/dev/null");
            while(<$hndl>){print $pipe $_;};
        close $pipe;

        print "<pre>\n";
        my $m1 = "it is not permitted to restore another aliases log backup.";
        $m1= "has your log password changed?" if ($tar=~/_data_$userid/);

        my $cmd = `tar tvf $tar 2>/dev/null`  or die qq(, possible an security issue, $m1\nFAILED READING $tar. \nYour alias is: <b>$userid</b>.\n);

        print "Contents->".$cmd."\n\n";
        $cmd = `tar xzvf $tar -C $dbck --strip-components 1 2>/dev/null` or die "Failed extracting $tar";
        print "Extracted->\n".$cmd."\n" or die "Failed extracting $tar";;

        my $b_base = $dbck.$dbname;
        my $dsn= "DBI:SQLite:dbname=$b_base";
        my $b_db = DBI->connect($dsn, $userid, $pass, { RaiseError => 1 }) or LifeLogException->throw(error=>"Invalid database! $dsn->$hndl [$@]", show_trace=>&Settings::debug);
        print "Connected to -> $dsn\n";

        print "Merging from backup categories table...\n";
        my $insCAT   = $db->prepare('INSERT INTO CAT (ID, NAME, DESCRIPTION) VALUES(?,?,?);') or die "Failed CAT prepare.";

        my $b_pst = Settings::selectRecords($b_db,'SELECT ID, NAME, DESCRIPTION FROM CAT;');
        while ( @br = $b_pst->fetchrow_array() ) {
            my $pst = Settings::selectRecords($db, "SELECT ID,NAME,DESCRIPTION FROM CAT WHERE ID='".$br[0]."';");
            my @ext = $pst->fetchrow_array();
            if(scalar(@ext)==0){
                $insCAT->execute($br[0],$br[1],$br[2]);
                print "Added CAT->".$br[0]."|".$br[1]."\n";
            }
            elsif($br[0] ne $ext[0] or $br[1] ne $ext[1]){
                $db->do("UPDATE CAT SET NAME='".$br[1]."', DESCRIPTION='".$br[2]."' WHERE ID=?;") or die "Cat update failed!";
                print "Updated->".$br[0]."|".$br[1]."|".$br[2]."\n";
            }

        }
        print "\nFinished with merging CAT table.\n";

        print "\n\nMerging from backup LOG table...\n";
        my $insLOG   = $db->prepare('INSERT INTO LOG (ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY) VALUES(?,?,?,?,?,?,?);')or die "Failed LOG prepare.";

        $b_pst = Settings::selectRecords($b_db,'SELECT ID, ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY FROM VW_LOG;');
        while ( @br = $b_pst->fetchrow_array() ) {
            my $pst = Settings::selectRecords($db,"SELECT DATE FROM VW_LOG WHERE DATE='".$br[3]."';");
            my @ext = $pst->fetchrow_array();
            if(scalar(@ext)==0){
                $insLOG->execute($br[1],$br[2],$br[3],$br[4],$br[5],$br[6],$br[7]);
                print "Added->".$br[0]."|".$br[3]."|".$br[4]."\n";
            }

        }
        print "\nFinished with merging LOG table.\n";

        print "\n\nMerging from backup NOTES table...\n";
        my $insNOTES   = $db->prepare('INSERT INTO NOTES (LID, DOC) VALUES(?,?);')or die "Failed NOTESprepare.";
        $b_pst = Settings::selectRecords($b_db,'SELECT LID, DOC FROM NOTES;');
        while ( @br = $b_pst->fetchrow_array() ) {
            my $pst = Settings::selectRecords($db,"SELECT LID FROM NOTES WHERE LID=".$br[0].";");
            my @ext = $pst->fetchrow_array();
            if(@ext==0&&$br[0]&&$br[1]){
                $insNOTES->execute($br[0], $br[1]) or die "Failed NOTES INSERT[".$br[0]."]";
                print "Added NOTES->".$br[0]."\n";
            }

        }
        print "\nFinished with merging NOTES table.\n";

        $b_db->disconnect();
        $db->disconnect();
        print "Done!";
    }
    catch{
        $ERROR = "<font color='red'><b>Restore failed!</b></font> hndl->$hndl $@ \nbr:[@br]";#,show_trace=>&Settings::debug);
    };

    my $back = $cgi->url( -relative => 1 );
    print $ERROR if($ERROR);
    print "\n</pre><code>";
    print qq(<a href="config.cgi?CGISESSID=$sid"><hr>Go Back</a> or <a href="main.cgi"><brr>Go to LOG</a></code>);
    print $cgi->end_html;
       exit;

}

sub exportToCSV {
    try{
        my $csv = Text::CSV->new ( { binary => 1, strict => 1,eol => $/ } );
        if($csvp > 2){
           $dbs = Settings::selectRecords($db, "SELECT ID, NAME, DESCRIPTION FROM CAT ORDER BY ID;");
        }
        else{
           $dbs = Settings::selectRecords($db, "SELECT * FROM LOG;");
        }

        if($csvp==2 || $csvp==4){
                 print $cgi->header(-charset=>"UTF-8", -type=>"text/html");
                 print "<pre>\n";
        }
        else{
         print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>"$dbname.categories.csv");
        }

        #print "ID,NAME,DESCRIPTION\n";
        while (my $row=$dbs->fetchrow_arrayref()){
               my $out = $csv->print(*STDOUT, $row);
                  print $out if(length $out>1);
        }
        if($csvp==2 || $csvp==4){
             print "</pre>";
        }
        $dbs->finish();
        $db->disconnect();
        exit;
    }
    catch{
        print "<font color=red><b>SERVER ERROR</b>->exportLogToCSV</font>:".$_;
    }
}


sub importCatCSV {
    my $hndl = $cgi->upload("data_cat");
    my $csv; try{
       $csv = Text::CSV->new ( { binary => 1, strict => 1, eol => $/ } );
        while (my $line = <$hndl>) {
            chomp $line;
            if ($csv->parse($line)) {
                my @fields   = $csv->fields();
                updateCATDB(@fields);
            }else{
                warn "Data could not be parsed: $line\n";
            }
        }
    }
    catch{
        LifeLogException->throw(error=>"Category update failed! CSV_STATUS->".$csv->error_diag()."\nfile_hndl->$hndl",show_trace=>&Settings::debug);
    };
}

sub updateCATDB {
    my @fields = @_;
    if(@fields>2){
            my $id   = $fields[0];
            my $name = $fields[1];
            my $desc = $fields[2];

            #is it existing entry?
            $dbs = Settings::selectRecords($db, "SELECT ID FROM CAT WHERE ID = '$id';");
            if(!$dbs->fetchrow_array()){
                    $dbs = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
                    $dbs->execute($id, $name, $desc);
                    $dbs->finish;
            }
            else{
                #TODO Update
            }
    }
      else{
         LifeLogException->throw("Invalid CSV data format!");
    }
}

sub importLogCSV {
    my $hndl = $cgi->upload("data_log");
    my $csv;
    try{

    $csv = Text::CSV->new ( { binary => 1, strict => 1, eol => $/ } );

        while (my $line = <$hndl>) {
                chomp $line;
                if ($csv->parse($line)) {
                    my @fields   = $csv->fields();
                    updateLOGDB(@fields);
                }else{
                        warn "Data could not be parsed: $line\n";
                }
        }
        &renumerate;
        $db->disconnect();
        print $cgi->redirect('main.cgi');

    }
    catch{
        LifeLogException->throw(error=>"Log update failed! CSV_STATUS->".$csv->error_diag()."\nfile_hndl->$hndl",show_trace=>&Settings::debug);
    };
    exit;
}

sub updateLOGDB {
    my @fields = @_;
    if(scalar(@fields)>6){

        my $i = 0;
        my $id_cat = $fields[$i++];
        my $id_rtf = $fields[$i++];
        my $date   = $fields[$i++];
        my $log    = $fields[$i++];
        my $amv    = $fields[$i++];
        my $amf    = $fields[$i++];
        my $sticky = $fields[$i++];
        # Is it old pre. 1.8 format -> ID, DATE, LOG, AMOUNT, AFLAG, RTF, STICKY
        if(!looks_like_number($id_rtf)){
            $i = 0;
            $id_cat = $fields[$i++];
            $date   = $fields[$i++];
            $log    = $fields[$i++];
            $amv    = $fields[$i++];
            $amf    = $fields[$i++];
            $id_rtf = $fields[$i++];
            $sticky = $fields[$i++];
        }
        my $pdate = DateTime::Format::SQLite->parse_datetime($date);
        #Check if valid date log entry?
        if($id_cat==0||$id_cat==""||!$pdate){
            return;
        }
        #is it existing entry?
        $dbs = Settings::selectRecords($db,"SELECT DATE FROM LOG WHERE DATE is '$pdate';");
        my @rows = $dbs->fetchrow_array();
        if(scalar @rows == 0){
                    $dbs = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?,?,?,?)');
                    $dbs->execute($id_cat, $id_rtf, $pdate, $log, $amv, $amf, $sticky);
        }
        $dbs->finish();
    }
    else{
         LifeLogException->throw("Invalid CSV data format!");
    }
}

sub cats {
        $cats = qq(<select id="cats" name="cats"><option value="0">---</option>\n);
        $dbs = Settings::selectRecords($db, "SELECT ID, NAME FROM CAT ORDER BY ID;");
        while ( my @row = $dbs->fetchrow_array() ) {
                $cats .= qq(<option value="$row[0]">$row[1]</option>\n);
                $hshCats{ $row[0] } = $row[1];
        }
        $cats .= '</select>';
}


sub error {
    my $url = $cgi->url(-path_info => 1);
    print qq(<h2>Sorry Encountered Errors</h2><p>Page -> $url</p><p>$ERROR</p>);
    print qq(<h3>CGI Parameters</h3>);
    print "<ol>\n";
    foreach ($cgi->param){
        print '<li>'.$_.'=='. $cgi->param($_).'</li>';
    }
    print "</ol>\n";
    print "<a href=$url>Return to -> $url</a>";
    print $cgi->end_html;
    $db->disconnect();
    exit;
}


sub renumerate {
    #Renumerate Log! Copy into temp. table.
    my $sql;
    $db->do("CREATE TABLE life_log_temp_table AS SELECT * FROM LOG;");
    $dbs = Settings::selectRecords($db, 'SELECT rowid, DATE FROM LOG WHERE ID_RTF >0 ORDER BY DATE;');
    #update  notes with new log id
    while(my @row = $dbs->fetchrow_array()) {
        my $sql_date = $row[1];
        if($sql_date){#could be an improperly deleted record in there? Skip if there is!
                        #$sql_date =~ s/T/ /;
                        $sql_date = DateTime::Format::SQLite->parse_datetime($sql_date);
                        $sql = "SELECT rowid, DATE FROM life_log_temp_table WHERE ID_RTF > 0 AND DATE = '".$sql_date."';";
                        $dbs = Settings::selectRecords($db, $sql);
                        my @new  = $dbs->fetchrow_array();
                        if(scalar @new > 0){
                            $db->do("UPDATE NOTES SET LID =". $new[0]." WHERE LID==".$row[0].";");
                        }
        }
    }

    # Delete Orphaned Notes entries.
    $dbs = Settings::selectRecords($db, "SELECT LID, LOG.rowid from NOTES LEFT JOIN LOG ON
                                    NOTES.LID = LOG.rowid WHERE LOG.rowid is NULL;");
    while(my @row = $dbs->fetchrow_array()) {
        $db->do("DELETE FROM NOTES WHERE LID=$row[0];");
    }
    $db->do('DROP TABLE LOG;');
    $db->do(&Settings::createLOGStmt);
    $db->do(q(INSERT INTO LOG (ID_CAT, ID_RTF, DATE, LOG, AMOUNT,AFLAG)
                    SELECT ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG FROM life_log_temp_table ORDER by DATE;));
    $db->do('DROP TABLE life_log_temp_table;');
}

1;