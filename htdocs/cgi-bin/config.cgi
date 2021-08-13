#!/usr/bin/perl
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use v5.10;
use strict;
use warnings;

use DBI;
use DBD::Pg;
use DBD::Pg qw(:pg_types);
use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;
use CGI;

use DateTime::Format::SQLite;
use Date::Language;
use Capture::Tiny ':all';
use Text::CSV;
use Scalar::Util qw(looks_like_number);
use Sys::Syslog qw(:DEFAULT :standard :macros); #openLog, closelog macros

#DEFAULT SETTINGS HERE!
use lib "system/modules";
require Settings;
#15mg data post limit
$CGI::POST_MAX = 1024 * 15000;
##

my ($RDS,$TR_STATUS,$LOGOUT,$ERROR) = ("","",0,"");
my $sys     = `uname -n`;
my $db      = Settings::fetchDBSettings();
my $cgi     = Settings->cgi();
my $sid     = Settings::sid(); 
my $dbname  = Settings::dbName();
my $alias   = Settings::alias();
my $rv;
my $dbs;
my $lang    = Date::Language->new(Settings::language());
my $today   = Settings::today();   
my $tz      = $cgi->param('tz');
my $csvp    = $cgi->param('csv');

exportToCSV() if ($csvp);

if($cgi->param('bck'))        {&backup}
elsif($cgi->param('bck_del')) {&backupDelete}
elsif($cgi->param('data_bck')){&restore;}
elsif($cgi->param('bck_file')){restore($cgi->param('bck_file'))}
elsif($cgi->param('data_cat')){&importCatCSV}
elsif($cgi->param('data_log')){&importLogCSV}



my $stmtCat = 'SELECT * FROM CAT ORDER BY ID;';
my $status  = $RDS = "Ready for change!";
my $cats; 
my %hshCats = {};
cats();
###############
processSubmit();
###############
Settings::getTheme();
Settings::session()->param("theme", Settings::css());
Settings::session()->param("bgcolor", Settings::bgcol());
getHeader();

 if ($ERROR){&error;}else{
print qq(<div id="menu" title="To close this menu click on its heart, and wait.">
<div class="hdr" style="marging=0;padding:0px;">
<a id="to_top" href="#top" title="Go to top of page."><span class="ui-icon ui-icon-arrowthick-1-n" style="float:none;"></span></a>&nbsp;
<a id="to_bottom" href="#bottom" title="Go to bottom of page."><span class="ui-icon ui-icon-arrowthick-1-s" style="float:none;"></span></a>
<a id="menu_close" href="#" onclick="return hide('menu_close');"><span  class="ui-icon ui-icon-heart" style="float:none;"></span></a>
</div>
<hr>
<a class="a_" href="main.cgi">Log</a><hr>
<a class="a_" href="stats.cgi">Stats</a><hr>
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
            <tr class="r1"><th>ID</th><th>Category</th><th  align="left">Description</th></tr>';
my $foot = "";
$dbs = Settings::selectRecords($db, $stmtCat);
while(my @row = $dbs->fetchrow_array()) {
    if( $row[0]>0 ){
       $tbl .= '<tr class="r0"><td>'.$row[0].'</td>
            <td><input name="nm'.$row[0].'" type="text" value="'.$row[1].'" size="12"></td>
            <td align="left"><input name="ds'.$row[0].'" type="text" value="'.$row[2].'" size="64"></td>
        </tr>';
    }
 }

my $frmCats = qq(
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

$tbl = qq(<table id="cnf_sys" class="tbl" border="1" width=").&Settings::pagePrcWidth.qq(%">$TR_STATUS
              <tr class="r0"><td colspan="3"><b>* SYSTEM CONFIGURATION *</b></td></tr>
            <tr class="r1" align="left">
                            <th width="20%">Variable</th>
                            <th width="20%">Value</th>
                            <th width="60%">Description <input type="submit" value="Change" style="float:right"/></th>
                        </tr>
       );
my $stm = 'SELECT ID, NAME, VALUE, DESCRIPTION FROM CONFIG ORDER BY NAME;';
   $dbs = Settings::selectRecords($db, $stm);
my $REL = "";
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
        elsif($n eq "COMPRESS_ENC"){
            my($l,$u)=("","");
            if($v == 0){
                    $l = "SELECTED"
            }
            else{
                $u = "SELECTED"
            }
            $v = qq(<select id="cmp_enc" name="var$i">
                    <option value="0" $l>False</option>
                    <option value="1" $u>True</option>
                    </select>);
        }
        elsif($n eq "DISP_ALL"){
            my($l,$u)=("","");
            if($v == 0){
                    $l = "SELECTED"
            }
            else{
                $u = "SELECTED"
            }
            $v = qq(<select id="log_disp" name="var$i">
                    <option value="0" $l>False</option>
                    <option value="1" $u>True</option>
                    </select>);
        }
        elsif(!defined(Settings::anon($n))){ #change into settable field to us found here unknown and not anon.
            $v = '<input name="var'.$i.'" type="text" value="'.$v.'" size="12">';
        }

       my $tr = qq(<tr class="r0" align="left">
            <td>$n</td>
            <td>$v</td>
            <td>$d</td>
        </tr>);

        if($i<300){$tbl.=$tr}else{$foot.=$tr}
}

$tbl = qq($tbl$foot<tr class="r1" align="left">$REL</tr>); #RELEASE VERSION we make to outstand last, can't be changed. :)

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
        <tr class="r1" align="left"><td style="width:100px">Existing:</td><td><input type="password" name="existing" value="" size="12"/></td></tr>
        <tr class="r1" align="left"><td>New:</td><td><input type="password" name="new" value="" size="12"/></td></tr>
        <tr class="r1" align="left"><td>Confirmation:</td><td><input type="password" name="confirm" value="" size="12"/></td></tr>
        <tr class="r1">
         <td colspan="2" align="right"><b>Pass change for -> $alias</b>&nbsp;<input type="submit" value="Change"/></td>
        </tr>
        </table><input type="hidden" name="pass_change" value="1"/></form><br>
        );
$frmPASS = qq(<tr><td>Password changing has been dissabled!</td></tr>) if Settings::isProgressDB(); 

my @backups = ();
my ($file, $bck_list) ="";
opendir my $dir, &Settings::logPath;
while($file = readdir $dir){
next if $file eq '.' or $file eq '..' or index ($file , 'bck_') == -1;
  push @backups, $file;
}
close $dir;
foreach $file (sort @backups){
    #my $n = substr $file, length(&Settings::logPath);
    $bck_list .=  "<input name='bck_file' type='radio' value='$file' onclick='setBackupFile(this);'>$file</input><br>";
}
if(length $bck_list == 0){
$bck_list = '<p>Restore will bring back and merge log entries from the time of backup.</p>
                        </td>
                </tr>';
}
else{
    $bck_list = qq(<p>Tick Select Backup to Restore or Delete</p><p>$bck_list</p>
    <input type="submit" onclick="deleteBackup();return false;" value="Delete"/>&nbsp;&nbsp;<input type="Submit" value="Restore"/></form>);
}

my $inpRestore = qq(<b>Local File:</b>&nbsp;&nbsp;
<input type="file" name="data_bck" />&nbsp;&nbsp;<input type="Submit" value="Restore"/>);
my $inpCVS = qq(<input type="button" onclick="return exportToCSV('log',0);" value="Export"/>&nbsp;
<input type="button" onclick="return exportToCSV('log',1);" value="View"/>);
if((Settings::anon("backup_enabled") == 0)){
    $inpRestore = $inpCVS = '&nbsp;<i><b>Sorry this feature has been dissabled!</b></i>';
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
            <form id="bck" action="config.cgi" method="post">
            <table border="0" width="100%">
                <tr><td><a name="backup"></a><H3>Backup File Format</H3></td></tr>
                <tr><td><input id="btnFetch" type="button" onclick="alert('Backing up next, this can take up some time. Please give it few minutes and return or refresh the config page!');return fetchBackup();" value="Fetch"/><hr></td></tr>

                <tr><td><div id="div_backups">$bck_list</div><hr></td></tr>

                <form id="bck_file" action="config.cgi" method="post" enctype="multipart/form-data">
                <tr><td>
                $inpRestore
                <hr></td></tr>
                </form>
                <form action="config.cgi" method="post" enctype="multipart/form-data">
                <tr>
                <td><H3>CSV File Format</H3>Notice: (<font color=red>This is an obsolete feature, use is not recommended!</font>)</td></tr>
                <tr><td style="text-align:left"><p>This Servers DSN is -><br> ).Settings::dsn().qq(</p></td></tr>
                <tr><td>
                        <b>Import Categories</b>: <input type="file" name="data_cat" />
                </td></tr>
                <tr><td style="text-align:right;">
                        <input type="submit" name="Submit" value="Submit"/></td>
                </tr>                
                <tr><td><b>Export Categories:</b>
                       <input type="button" onclick="return exportToCSV('cat',0);" value="Export"/>&nbsp;
                       <input type="button" onclick="return exportToCSV('cat',1);" value="View"/>
                </td></tr>
                <tr><td>
                        <br>
                        <b>Import Log</b>: <input type="file" name="data_log" /></td></tr>
                <tr style="border-right: 0px solid black;"><td style="text-align:right;">
                        <input type="submit" name="Submit" value="Submit"/></td></tr>
                </form>
                <tr><td><b>Export Log:</b>$inpCVS
                </td></tr>                
            </table><br><a href="#top">&#x219F;&nbsp;Go to Top of page</a>
    </div>
   <hr>
   <div id="rz" style="text-align:left; position:relative;width:640px; padding:10px;">
       <h2>Backup Specs</h2>
    <p><ol>
        <li><h3>Backup Rules</h3>
            <ol>
                <li>Backup provides an compressed archive of only the current logged in database.</li>
                <li>Backup should and can be uploaded to local client to later restore.</li>
                <li>Issuing backup always creates on the server an copy.</li>
                <li>Backups are issued manually and are interactive.</li>
                <li>Backups are server side encrypted.</li>
                <li>Backups can be particularly server specific, therefore not suitable for restoration on new or different hardware.</li>
                <li>Backup uses OpenSSL, wich under different versions can be uncompatible in the implemented type of encryption.</li>
            </ol>
        </li>
        <li><h3>Restore Rules</h3>
            <ol>
                <li>The restoring is only possible if logged into current database the backup belongs.</li>
                <li>Restoration is of only logs found missing in current log.</li>
                <li>Restoration is not removing entries in existing current log data.</li>
                <li>Restoration might not be possible after an server application upgrade.</li>
                <li>Restoration of old backups is not made possible or is safe, on new stable application releases.
                 <ul><li><i>Upgrade your application after restoring it first, as an upgrade will/might migrate structure and data.</i></li></ul></li>
                <li>                
                Restoration will import on an previous date backuped data, in case when recreating a newly created same alias database. 
                    <ul><li>For example: If the database file has been deleted or is blank on login, you than can run a restore, if you have an backup, for given server.</li></ul>
                </li>
                
                
            </ol>            
        </li>
        <li><h3>Purpose</h3>
            <ol>
                    <li>Provides a direct safeguard, besides any external backup procedures.</li>
                    <li>Provides a before snapshot, if venturing into major log modifications.</li>
                    <li>Encourages experimentation, with data deletion and modification.</li>
                    <li>Required if downgrading from an failed application upgrade, or found a missuesed or corrupted state of current data.</li>
            </ol>
        </li>
    </ol></p>
    </div>        
</div>
<hr>
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
        if(confirmExistingPass($ex)){
             &changePass($ne);
             $status = "Pass Has Been Changed";
        }
        else{
            $status = "Wrong existing pass was entered, are you user by alias: $alias ?";
            print "<center><div><p><font color=red>Client Error</font>: $status</p></div></center>";
        }
    }
    Settings::toLog($db,$status);
    openlog(Settings::dsn(), 'cons,pid', "user");
        syslog('info', 'Status:%s', $status);
        syslog('info', 'Password change request for %s', $alias);
    closelog();
    $TR_STATUS = qq(<tr><td colspan="3"><b><font color=red>$status</font></b></td></tr>) if $status !~ m/$RDS/;
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
    $status = "Updated Categories!";$TR_STATUS = qq(<tr><td colspan="3"><b>$status</b></td></tr>);
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

        my $output = qq(<a name="top"></a><form id="frm_log" action="data.cgi" onSubmit="return formDelValidation();">
                    <TABLE class="tbl" border="0" width=").&Settings::pagePrcWidth.qq(%">
                    <tr class="hdr"><td colspan="5" class="r1"><h3>Select Categories To Delete</h3></td></tr>
                    <tr class="r2">
                        <th><a id="to_bottom" href="#bottom" title="Go to bottom of page."><span class="ui-icon ui-icon-arrowthick-1-s" style="float:none;"></span></a> Date</th>
                        <th>Time</th>
                        <th>Log</th><th>#</th>
                        <th>Category</th>
                    </tr>);
        my $sel ="";
        if($isByCat){$sel = "ID_CAT ='$category'"}
        if($isByDate){
            $sel .= " AND " if ($isByCat);
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
            if ( Settings::universalDate() == 1 ) {
                $dtf = $dty;
            }
            else {
                $dtf = $lang->time2str( "%d %b %Y", $dt->epoch, Settings::timezone() );
            }

                $log =~ s/''/'/g;
                $log =~ s/\\n/<br>/gs;

            $output .= qq(<tr class="r2">
                    <td width="15%">$dtf<input id="y$id" type="hidden" value="$dty"/></td>
                    <td id="t$id" width="10%" class="tbl">$dth</td>
                    <td id="v$id" class="log" width="40%">$log</td>
                    <td id="c$id" width="10%" class="tbl">$ct</td>
                    <td width="20%">
                        <input name="chk" type="checkbox" value="$id"/>
                    </td></tr>);
       }#while
       $output .= qq(<tr class="r3"><td style="text-align:left;">
       <a id="to_top" href="#top" title="Go to top of page.">To Top<span class="ui-icon ui-icon-arrowthick-1-n" style="float:none;"></span></a>
       <a href="config.cgi?CGISESSID=$sid#dbsets">Go Back</a></td>
       <td colspan="4" align="right">
        <a name="bottom"></a><button onclick="return selectAllLogs()">Select All</button>
        <input type="reset" value="Unselect All"/>
        <input type="hidden" name="confirmed" value="1">
        <input id="del_sel" type="submit" value="Delete Selected"/>
        </td></tr>
        </form></TABLE>);

        &Settings::getTheme;
        &getHeader;

        print "<div>$output</div>";

        print $cgi->end_html;
        $db->disconnect();
        exit;

    }
    else{processDBFix()}
    $status = "Performed Database Fixes!";
}
$TR_STATUS = qq(<tr><td colspan="3"><b>Status -> </b>$status</td></tr>)if $status !~ m/$RDS/;

}
catch{

        my $err = $@;
        my $pwd = `pwd`;
           $pwd =~ s/\s*$//;

        $ERROR =
        "<hr><font color=red><b>SERVER ERROR</b></font> on ".DateTime->now.
        "<hr><pre>".$pwd."/$0 -> &".caller." -> [$err]","</pre>",



}

    openlog(Settings::dsn(), 'cons,pid', "user");
        syslog('info', 'Status:%s', $status);
        syslog('err', '%s', $ERROR) if ($ERROR);
    closelog();
}

sub confirmExistingPass {        
        my $crypt = encryptPassw($_[0]);
        my $sql = "SELECT ALIAS from AUTH WHERE ALIAS='$alias' AND PASSW='$crypt';";
    
        $dbs = Settings::selectRecords($db, $sql ); my @a = $dbs->fetchrow_array();
        if(@a==1 && $a[0] eq $alias){
            return 1;
        }
        return 0;
}
sub changePass {
      my $pass = encryptPassw($_[0]);
        $dbs = Settings::selectRecords($db, "UPDATE AUTH SET PASSW='$pass' WHERE ALIAS='$alias';");
        my @a = $dbs->fetchrow_array();
        if(@a==1 && $a[0] eq $alias){
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
    #Hash is unreliable for returning sequential order of keys so array must do.
    my @dlts = ();    
    my $cntr_del =0;
    my $existing;
    my @row;

        getHeader() if(&Settings::debug);
        print "<h3>Database Records Fix Result</h3>\n<hr>" if(&Settings::debug);
        print "<body><pre>Started transaction!\n" if(&Settings::debug);

        $db->do('BEGIN TRANSACTION;');
        # Check for duplicates, which are possible during imports or migration as internal rowid is not primary in log.
        # @TODO This should be selecting an cross SQL compatibe view.
        if(Settings::isProgressDB()){
            $dbs = Settings::selectRecords($db, 'SELECT ID, DATE FROM LOG ORDER BY DATE;');
        }else{
            $dbs = Settings::selectRecords($db, 'SELECT rowid, DATE FROM LOG ORDER BY DATE;');
        }
        while(@row = $dbs->fetchrow_array()) {
            my $existing = $dates{$row[0]};
            if($existing && $existing eq $row[1]){
                $dlts[$cntr_del++] = $row[0];
            }
            else{
                $dates{$row[0]} = $row[1];
            }
        }

        foreach my $del (@dlts){
             if(Settings::isProgressDB()){
                 $sql = "DELETE FROM LOG WHERE rowid=$del;";
             }else{
                 $sql = "DELETE FROM LOG WHERE ID=$del;";
             }
            print "$sql\n<br>";
            my $st_del = $db->prepare($sql);
            $st_del->execute();
        }
        print "Doing renumerate next...\n" if(&Settings::debug);
        &renumerate;
        print "done!\n";
        print "Doing removeOldSessions next..." if(&Settings::debug);
        &Settings::removeOldSessions;
        print "done!\n " if(&Settings::debug);
        &resetCategories if $rs_cats;
        &resetSystemConfiguration($db) if $rs_syst;
        &wipeSystemConfiguration if $wipe_ss;

        $db->do('COMMIT;')if(&Settings::debug);
        print "Commited ALL!<br>"if(&Settings::debug);
       # $db->disconnect();
        $db  = Settings::connectDB();
        $dbs = $db->do("VACUUM;")if(&Settings::debug);
        print "Issued  VACUUM!<br>"if(&Settings::debug);
        
        if($LOGOUT){
                &logout;
        }

        exit if(&Settings::debug);

}
catch{
    $db->do('ROLLBACK;');
    LifeLogException->throw(error=>qq(@&processDBFix error -> $_ with statement->[$sql] for $date update counter:$cntr_upd \nERROR->$@),show_trace=>1);
}
}

sub renumerate {

    # NOTE: This is most likelly all performed under an transaction.
    my $sql; 
    # Fetch list by date identified rtf attached logs, with possibly now an old LID, to be updated to new one.    
    if(Settings::isProgressDB()){
        $sql = "SELECT ID, DATE FROM LOG WHERE RTF > 0;"
    }else{
        $sql = "SELECT rowid, DATE FROM LOG WHERE RTF > 0;"
    }
    my @row = Settings::selectRecords($db, $sql)->fetchrow_array();
    my %notes  = ();
    if (scalar @row > 0){
        $notes{$row[1]} = $row[0]; #<- This is current LID, will change.
        print "Expecting Note entry for  ".$row[1]."  LOG.ID[".$row[0]."]<- LID...\n";
    }

    ### RENUMERATE LOG
    $db->do("CREATE TABLE life_log_temp_table AS SELECT * FROM LOG;");
    if(Settings::isProgressDB()){
        $db->do('DROP TABLE LOG CASCADE;');
    }
    else{
        $db->do('DROP TABLE LOG;');
    }
    $db->do(&Settings::createLOGStmt);
    $db->do(q(INSERT INTO LOG (ID_CAT, DATE, LOG, RTF, AMOUNT,AFLAG)
                    SELECT ID_CAT, DATE, LOG, RTF, AMOUNT, AFLAG FROM life_log_temp_table ORDER by DATE;));
    $db->do('DROP TABLE life_log_temp_table;');
    ###

    # Update  notes with new log id, if it changed.

    foreach my $date (keys %notes){
        my $old = $notes{$date};
        #my $sql_date = DateTime::Format::SQLite->parse_datetime($date);
        
        if(Settings::isProgressDB()){
            $sql = "SELECT ID FROM LOG WHERE RTF > 0 AND DATE = '".$date."';";
        }else{
            $sql = "SELECT rowid FROM LOG WHERE RTF > 0 AND DATE = '".$date."';";
        }
        print "Selecting ->  $sql\n";
        $dbs = Settings::selectRecords($db, $sql);        
        @row = $dbs->fetchrow_array();
        if(scalar @row > 0){                            
            my $new = $row[0];
            if($new ne $old){
               $db->do("UPDATE NOTES SET LID =$new WHERE LID=$old;");
               print "Updated Note in LID[$old] to be LID[$new]\n";
            }
            else{
               print "All fine skipping LID[$new]\n";
            }
        }else{
            print "ERROR NOT FOUND: $date for LID:$old!\n";
        }

    }

    # Delete Orphaned Notes entries if any?
    if(Settings::isProgressDB()){
        $dbs = Settings::selectRecords($db, "SELECT LID, LOG.ID from NOTES LEFT JOIN LOG ON
                                        NOTES.LID = LOG.ID WHERE LOG.ID is NULL;");
    }else{
        $dbs = Settings::selectRecords($db, "SELECT LID, LOG.rowid from NOTES LEFT JOIN LOG ON
                                        NOTES.LID = LOG.rowid WHERE LOG.rowid is NULL;");
    }
    if ($dbs) {  foreach (@row = $dbs->fetchrow_array()) {
                $db->do("DELETE FROM NOTES WHERELID=$row[0];") if $row[0]; # 0 is the place keeper for the shared zero record. 
    }}

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
                                                            for my $id (keys %nash) {
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
    Settings::session()->delete();
    Settings::session()->flush();
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
         LifeLogException->throw("File -> <i>[$n]</i> is not a backup file or it doesn't belong to $alias (you)!") if(index ($file , /bck_\d+$alias\_log/) == -1 );
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
   my $pass = Settings::pass();   
   my @dr = split(':', Settings::dbSrc());
   my $ball = 'bck_'.$today->strftime('%Y%m%d%H%M%S_').$dr[1]."_$dbname.osz";   

   my $file = Settings::logPath().'data_'.$dr[1].'_'."$dbname"."_log.db";
   my $dsn= "DBI:SQLite:dbname=$file";
   my $weProgress = Settings::isProgressDB();
   if($weProgress){
           try{$pass = uc crypt $pass, hex Settings->CIPHER_KEY;
               unlink $file if -e $file; # we will recreate it next.
           }catch{};
        my $dbB = DBI->connect($dsn, $alias, $pass, { AutoCommit => 1, RaiseError => 1 }) or 
                        LifeLogException->throw(error=>"Invalid database! $dsn [$@]", show_trace=>&Settings::debug);
            &Settings::resetToDefaultDriver;
            $dbB->do(&Settings::createCATStmt);
            $dbB->do(&Settings::createLOGStmt);
            $dbB->do(&Settings::createNOTEStmt);

            my $in = $dbB->prepare('INSERT INTO CAT VALUES (?,?,?)');
            my $st = Settings::selectRecords($db,'SELECT * FROM CAT;');       
                while(my @c = $st->fetchrow_array()){          
                $in->execute($c[0],$c[1],$c[2]);
                }

                $in = $dbB->prepare('INSERT INTO LOG (ID_CAT, DATE, LOG, RTF, AMOUNT, AFLAG, STICKY) VALUES (?,?,?,?,?,?,?);');
                $st = Settings::selectRecords($db,'SELECT ID_CAT, DATE, LOG, RTF, AMOUNT, AFLAG, STICKY FROM LOG order by DATE;');       
                while(my @c = $st->fetchrow_array()){          
                    $in->execute($c[0],$c[1],$c[2],$c[3],$c[4],$c[5],$c[6]);
                }
                $in = $dbB->prepare('INSERT INTO NOTES VALUES (?,?)');
                $st = Settings::selectRecords($db,'SELECT LID, DOC FROM NOTES;');       
                while(my @c = $st->fetchrow_array()){          
                    $in->execute($c[0],$c[1]);
                }
                $dbB->disconnect();                
   }else{
       $file = Settings::dbFile();
   }

    print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>$ball);
    my $pipe = "tar czf - ".Settings::logPath().'main.cnf' ." ".$file." | openssl enc -e -des-ede3-cfb -salt -S ".
                            Settings->CIPHER_KEY." -pass pass:$pass-$alias -out ".Settings::logPath().$ball." 2>/dev/null";
    my $rez = `$pipe`;       
       open (my $TAR, "<", Settings::logPath().$ball) or die "Failed creating backup -> $ball";
            while(<$TAR>){print $_;}
       close $TAR;
    unlink $file if $weProgress;  
    exit;
}

sub restore {

    my $file = shift;
    my ($tar,$pipe,@br,$stdout, $b_db);
    my $pass = Settings::pass();
    my $hndl = $cgi->param('data_bck');
    my $dbck = &Settings::logPath."bck/"; `mkdir $dbck` if (!-d $dbck);
    my $stage = "Initial";

try{
        getHeader();
        print $cgi->start_html;

my $stdout = capture_stdout {

        print "<h3>Restore Result</h3>\n<hr>";
        print "Restore started: ".Settings::today(), "\n";
        if($file){ #Open handle on server to backup to be restored.
            my $f = &Settings::logPath.$file;
            open($hndl, '<', $f) or die "Can't open $f: $!";            
            print "<pre>Reading on server backup file -> $file</pre>";
            $tar = $dbck.$file;
        }        
        else{
            print "<pre>Reading-> $hndl</pre>";
            $tar = $dbck.$hndl;
        }
        $tar =~ s/osz$/tar/;


        my $srcIsPg = 0;
        my $pipe;
        my $passw   = $pass; $passw = uc crypt $pass, hex Settings->CIPHER_KEY if &Settings::isProgressDB;
        open ($pipe, "| openssl enc -d -des-ede3-cfb -salt -S ".
                Settings->CIPHER_KEY." -pass pass:$passw-$alias -in /dev/stdin 2>/dev/null > $tar");
            while(<$hndl>){print $pipe $_;};
        close $pipe; close $hndl;

        print "<pre>\n";
        

        my $m1 = "it is not permitted to restore from anothers backup file.";
        $m1= "has your log password changed?" if ($tar=~/_data_$alias/);
        $stage = "Extraction";

        my $cmd = `tar tvf $tar 2>/dev/null` 
         or die qq(, Error: A possible security issue, $m1\n<br> BACKUP FILE HAS BEEN INVALIDATED!
          $tar\nYour alias is: <b>$alias</b>\n<br>
          Your DSN  is: ).Settings::dsn().qq(<br>
          Your LifeLog version is:), Settings::release()."\n";
        
        print "Contents->\n".$cmd."\n\n";
        $cmd = `tar xzvf $tar -C $dbck --strip-components 1 2>/dev/null` or die "Failed extracting $tar";
        print "Extracted->\n".$cmd."\n" or die "Failed extracting $tar";;
        my @dr = split(':', Settings::dbSrc());
        my $b_base = $dbck.'data_'.$dbname.'_log.db';  
        
        # We check if db file has been extracted first?
        unless(-e $b_base){                  
                  if (&Settings::isProgressDB){
                      $b_base = $dbck.'data_'.$dr[1].'_'.$dbname.'_log.db'
                  }else{ # maybe the source is a Pg db backup?
                      $b_base = $dbck.'data_Pg_'.$dbname.'_log.db';
                      $srcIsPg = 1;
                  }
                  unless(-e $b_base){
                      die "Failed to locate database in archive -> $b_base";
                  }
        }
        my $dsn= "DBI:SQLite:dbname=$b_base";

        $b_db = DBI->connect($dsn, $alias, $pass, { RaiseError => 1 }) or 
                 LifeLogException->throw(error=>"Invalid database! $dsn->$hndl [$@]", show_trace=>&Settings::debug);

        print "Connected to -> ".Settings::dsn()."\n";
        $stage = "Merging categories table.";
        print "Merging from backup categories table...";
        my $stats =  DBMigStats -> new();
        my $insCAT   = $db->prepare('INSERT INTO CAT (ID, NAME, DESCRIPTION) VALUES(?,?,?);') or die "Failed CAT prepare.";
        my $b_pst = Settings::selectRecords($b_db,'SELECT ID, NAME, DESCRIPTION FROM CAT;');
        
        while ( @br = $b_pst->fetchrow_array() ) {
            next if not $br[0]; #@2021-08-12 For some reason this still could be null 
            $stage .= "<br>id:".$br[0]."->".$br[1];
            my $pst = Settings::selectRecords($db, "SELECT ID, NAME, DESCRIPTION FROM CAT WHERE ID=".$br[0].";");
            my @ext = $pst->fetchrow_array();
            if(scalar(@ext)==0){
                $insCAT->execute($br[0],$br[1],$br[2]);
                print "\nAdded CAT->".$br[0]."|".$br[1]; $stats->DBMigStats::cats_inserts_incr();
            }
            elsif($br[0] ne $ext[0] or $br[1] ne $ext[1]){
                $db->do("UPDATE CAT SET NAME='".$br[1]."', DESCRIPTION='".$br[2]."' WHERE ID=$br[0];") or die "Cat update failed!";
                print "\nUpdated->".$br[0]."|".$br[1]."|".$br[2]; $stats->DBMigStats::cats_updates_incr();
            }

        }
        
        print "\nFinished with merging CAT table.\n";
        print "There where -> ". $stats->cats_inserts(). " inserts, and ". $stats->cats_updates(). " updates.\n";

        $stage = "Merging backup LOG";
        print "\n\nMerging from backup LOG table...\n";

        my %backupLIDS =();
        my $CI = 'rowid'; $CI = 'ID' if Settings::isProgressDB();
        my $insLOG   = $db->prepare('INSERT INTO LOG (ID_CAT, DATE, LOG, RTF, AMOUNT, AFLAG, STICKY) VALUES(?,?,?,?,?,?,?);')or die "Failed LOG prepare.";

        $b_pst = Settings::selectRecords($b_db,"SELECT rowid, ID_CAT, DATE, LOG, RTF, AMOUNT, AFLAG, STICKY FROM LOG;");
        while ( @br = $b_pst->fetchrow_array() ) {
            my $dt  = $br[2];
            my $pst = Settings::selectRecords($db,"SELECT DATE FROM LOG WHERE DATE='".$dt."';");
            my @ext = $pst->fetchrow_array();
            if(scalar(@ext)==0){
                try{
                            $insLOG->execute($br[1],$br[2],$br[3],$br[4],$br[5],$br[6],$br[7]);
                            print "Added->".$br[0]."|".$br[2]."|".$br[3]."\n"; $stats->logs_inserts_incr();
                            if($br[4]){                    
                                $pst = Settings::selectRecords($db, "SELECT max($CI) FROM LOG");
                                my @r = $pst->fetchrow_array();
                                $backupLIDS{$br[0]} = $r[0];
                            }
                }
                catch{
                    print "<font color=red><b>Insert insert of</b> ->[".$br[0]."|".$br[2]."|\n".$br[3]."]<br><b>Error -> <i>$@</i><b></font>\n";
                }
            }
        }
        print "\nFinished with merging LOG table.\n";
        print "There where -> ". $stats->logs_inserts(). " inserts.\n";

        $stage = "Merging Notes";
        print "\nMerging from backup NOTES table...\n";
        my $insNOTES   = $db->prepare('INSERT INTO NOTES (LID, DOC) VALUES(?,?);') or die "Failed NOTES prepare.";
        $b_pst = Settings::selectRecords($b_db,'SELECT LID, DOC FROM NOTES;');
        while ( @br = $b_pst->fetchrow_array() ) {
            my $in_id = $backupLIDS{$br[0]};
            if($in_id && $br[1]){
                if(Settings::isProgressDB()){                    
                    $insNOTES->bind_param(1, $in_id);                    
                    try{                    
                        use IO::Compress::Gzip qw(gzip $GzipError);
                        use Compress::Zlib;
                        use Crypt::Blowfish;
                        use Crypt::CBC;
                        sub cryptKey {
                            my $p = shift;
                            my $r = $alias.$p.Settings->CIPHER_KEY;
                            $r    =~ s/(.)/sprintf '%04x', ord $1/seg;        
                        return  substr $r.Settings->CIPHER_PADDING, 0, 58;
                        }
                        if( not $srcIsPg ){ #IT is NOT PG BCK to PG DB
                            # With Pg the password we don't encrypt itself, so we need to redo the binary :(.
                            my $d = uncompress($br[1]);
                            my $cipher = Crypt::CBC->new(-key  => cryptKey($passw), -cipher => 'Blowfish');
                            my $doc = $cipher->decrypt($d);
                            #print $doc;
                            $cipher = Crypt::CBC->new(-key  => cryptKey($pass), -cipher => 'Blowfish');
                            $doc = compress($cipher->encrypt($doc));
                            $insNOTES->bind_param(2, $doc, { pg_type => DBD::Pg::PG_BYTEA });
                            $insNOTES->execute() or die "Failed NOTES INSERT[".$br[0]."]";
                        }else{
                            $insNOTES->bind_param(2, $br[1], { pg_type => DBD::Pg::PG_BYTEA });
                            $insNOTES->execute() or die "Failed NOTES INSERT[".$br[0]."]";
                        }
                        print "Added ".$dr[1]." NOTES -> LID:$in_id\n";


                    }
                    catch{
                        print "FAILED TO INSERT NOTES -> LID:$in_id Err:$@\n";
                    } 
                    
                }else{
                    try{
                        $insNOTES->execute($in_id, $br[1]);
                        print "Added NOTES -> LID:$in_id\n";
                    }
                    catch{
                        print "FAILED TO INSERT NOTES -> LID:$in_id Err:$@\n";
                    } 
                }                   
            }
        }
        print "\nFinished with merging NOTES table.\n";
        print "Note that the merge didn't recover documents for any existing log entries.\n";
        print "To do this, delete those log entries, then run restore again.\n";        
        print "Done!\n";
        print "Restore ended: ".Settings::today(), "\n";
};      print $stdout;

my $fh; open( $fh, ">>", Settings::logPath()."backup_restore.log");
        print $fh $stdout;
        close $fh;

$b_db->disconnect();
$db->disconnect();
`rm -rf $dbck/`;

}
catch{
    $ERROR = "<br><font color='red'><b>Full Restore Failed!</b></font><br>hndl->$hndl <br>$@ \n";
    $ERROR .= "br:[@br]" if(@br);
    $ERROR .= "<br><b>Failed at stage:</b> $stage";
};

    my $back = $cgi->url( -relative => 1 );
    print $ERROR if($ERROR);
    print "\n</pre><code>";
    print qq(<a href="config.cgi?CGISESSID=$sid"><hr>Go Back</a> or <a href="main.cgi"><br>Go to LOG</a></code>);
    print $cgi->end_html;
       exit;

}

package DBMigStats {

    
    sub new {
        my $class = shift;
        my $self = bless {cats_ins  => 0, cats_upd  => 0, logs_ins  => 0, logs_upd  => 0, notes => 0}, $class;
    }

    sub cats_inserts(){my $s = shift;return $s->{cats_ins}}
    sub cats_inserts_incr() {my $s = shift; $s->{cats_ins}++}
    sub cats_updates(){my $s = shift;return $s->{cats_upd}}
    sub cats_updates_incr() {my $s = shift; $s->{cats_upd}++}
    
    sub logs_inserts(){my $s = shift;return $s->{logs_ins}}
    sub logs_inserts_incr(){my $s = shift;  $s->{logs_ins}++}
    sub logs_updates(){my $s = shift;return $s->{logs_upd}}
    sub logs_updates_incr(){my $s = shift;  $s->{logs_upd}++}
    
    sub notes()      {my $s = shift;return  $s->{notes}}
    sub notes_incr() {my $s = shift; $s->{notes}++}

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
         my $type = 'categories';
         $type = 'log' if($csvp ==1);
         print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>"$dbname.$type.csv");
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
        my $date   = $fields[$i++];
        my $log    = $fields[$i++];
        my $rtf    = $fields[$i++];
        my $amv    = $fields[$i++];
        my $amf    = $fields[$i++];
        my $sticky = $fields[$i++];
        # Is it old pre. 1.8 format -> ID, DATE, LOG, AMOUNT, AFLAG, RTF, STICKY
        if(!looks_like_number($rtf)){
            $i = 0;
            $id_cat = $fields[$i++];
            $rtf    = $fields[$i++];
            $date   = $fields[$i++];            
            $log    = $fields[$i++];
            $amv    = $fields[$i++];
            $amf    = $fields[$i++];            
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
                    $dbs->execute($id_cat, $pdate, $log, $rtf, $amv, $amf, $sticky);
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


    my %dates  = ();
    #Hash is unreliable for returning sequential order of keys so array must do.
    my @dlts = ();    
    my $cntr_del =0;
    my $existing;
    my @row;

        getHeader();
        print "<body><pre>Started transaction!\n";

        $db->do('BEGIN TRANSACTION;');
        # Check for duplicates, which are possible during imports or migration as internal rowid is not primary in log.
        # @TODO This should be done through an view?
        if(Settings::isProgressDB()){
            $dbs = Settings::selectRecords($db, 'SELECT ID, DATE FROM LOG ORDER BY DATE;');
        }else{
            $dbs = Settings::selectRecords($db, 'SELECT rowid, DATE FROM LOG ORDER BY DATE;');
        }
        while(@row = $dbs->fetchrow_array()) {
            my $existing = $dates{$row[0]};
            if($existing && $existing eq $row[1]){
                $dlts[$cntr_del++] = $row[0];
            }
            else{
                $dates{$row[0]} = $row[1];
            }
        }



1;