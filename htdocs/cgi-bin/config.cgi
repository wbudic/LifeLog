#!/usr/bin/perl -w
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use strict;
use warnings;
use Try::Tiny;
use Switch;
 
use CGI;
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Text::CSV;

#DEFAULT SETTINGS HERE!
our $REC_LIMIT    = 25;
our $TIME_ZONE    = 'Australia/Sydney';
our $LANGUAGE     = 'English';
our $PRC_WIDTH    = '70';
our $LOG_PATH     = '../../dbLifeLog/';
our $SESSN_EXPR   = '+30m';
our $DATE_UNI     = '0';
our $RELEASE_VER  = '1.4';
our $AUTHORITY    = '';
our $IMG_W_H      = '210x120';
our $AUTO_WRD_LMT = 200;
our $AUTO_LOGIN   = 0;
our $FRAME_SIZE   = 0;
our $RTF_SIZE     = 0;
our $THEME        = 0;
our $TH_CSS       = 'main.css';
#END OF SETTINGS

#This is the OS developer release key, replace on istallation. As it is not secure.
my $cipher_key = '95d7a85ba891da';

#15mg data post limit
$CGI::POST_MAX = 1024 * 15000;
my ($LOGOUT,$ERROR) = (0,"");
my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory=>$LOG_PATH});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');
my  $sys = `uname -n`;
#my $acumululator="";

if(!$userid||!$dbname){
    print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
    exit;
}

my $database = $LOG_PATH.$dbname;
my $dsn= "DBI:SQLite:dbname=$database";
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) or die "<p>Error->"& $DBI::errstri &"</p>";

my $rv;
my $dbs;
my $today  = DateTime->now;
my $tz     = $cgi->param('tz');
my $csvp   = $cgi->param('csv');
   
     switch ($csvp){
                case "1" {&exportLogToCSV}
                case "2" {&exportLogToCSV}
                case "3" {&exportCategoriesToCSV}
                case "4" {&exportCategoriesToCSV}
     }

    if($cgi->param('data_cat')){
            &importCatCSV;
     }elsif($cgi->param('data_log')){
            &importLogCSV;
     }  
        
#####################
    &getConfiguration;
#####################
$today->set_time_zone( $TIME_ZONE );
    

my $stmtCat = 'SELECT * FROM CAT ORDER BY ID;';
my $status = "Ready for change!";


###############
&processSubmit;
###############

my $BGCOL = '#c8fff8';
    if ( $THEME eq 'Sun' ) {
        $BGCOL = '#D4AF37';
        $TH_CSS = "main_sun.css";
    }elsif ($THEME eq 'Moon'){
        $TH_CSS = "main_moon.css";
        $BGCOL = '#000000';

    }elsif ($THEME eq 'Earth'){
        $TH_CSS = "main_earth.css";
        $BGCOL = 'green';
    }

print $cgi->header(-expires=>"+6s", -charset=>"UTF-8");
print $cgi->start_html(-title => "Personal Log", -BGCOLOR=>"$BGCOL",
           -onload  => "loadedBody();",	           
            -style   => [
          { -type => 'text/css', -src => "wsrc/$TH_CSS" },
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


print qq(<div id="menu" title="To close this menu click on its heart, and wait.">
<div class="hdr" style="marging=0;padding:0px;">
<a id="to_top" href="#top" title="Go to top of page."><span class="ui-icon ui-icon-arrowthick-1-n" style="float:none;"></span></a>&nbsp;
<a id="to_bottom" href="#bottom" title="Go to bottom of page."><span class="ui-icon ui-icon-arrowthick-1-s" style="float:none;"></span></a>
<a id="floating_menu_close" href="#"><span  class="ui-icon ui-icon-heart" style="float:none;"></span></a>
</div>
<hr>
<a class="a_" href="stats.cgi">Stats</a><hr>
<a class="a_" href="main.cgi">Log</a><hr>
<br>
<a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a>
</div>);

&error if $ERROR;



my $tbl = '<table id="cnf_cats" class="tbl" border="1" width="'.$PRC_WIDTH.'%">
              <tr class="r0"><td colspan="4"><b>* CATEGORIES CONFIGURATION *</b></td></tr>
            <tr class="r1"><th>ID</th><th>Category</th><th  align="left">Description</th></tr>
          ';
$dbs = dbExecute($stmtCat);
while(my @row = $dbs->fetchrow_array()) {
    if($row[0]>0){ 
       $tbl = $tbl. 
       '<tr class="r0"><td>'.$row[0].'</td>
            <td><input name="nm'.$row[0].'" type="text" value="'.$row[1].'" size="12"></td>
            <td align="left"><input name="ds'.$row[0].'" type="text" value="'.$row[2].'" size="64"></td>
        </tr>';
    }
 }

my  $frm = qq(
     <form id="frm_config" action="config.cgi">).$tbl.qq(
      <tr class="r1">
         <td><input type="text" name="caid" value="" size="3"/></td>
         <td><input type="text" name="canm" value="" size="12"/></td>
         <td align="left"><input type="text" name="cade" value="" size="64"/></td>		 
        </tr>
      <tr class="r1">
         <td colspan="2"><a href="#bottom">&#x21A1;</a>&nbsp;&nbsp;&nbsp;<input type="submit" value="Add New Category" onclick="return submitNewCategory()"/></td>
         <td colspan="1" align="right"><b>Categories Configuration In -> $dbname</b>&nbsp;<input type="submit" value="Change"/></td>
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
     

$tbl = qq(<table id="cnf_sys" class="tbl" border="1" width="$PRC_WIDTH%">
              <tr class="r0"><td colspan="3"><b>* SYSTEM CONFIGURATION *</b></td></tr>
            <tr class="r1" align="left">
                            <th width="20%">Variable</th>
                            <th width="20%">Value</th>
                                <th width="60%">Description</th>
                        </tr>
       );
my $stm = 'SELECT ID, NAME, VALUE, DESCRIPTION FROM CONFIG;';
$dbs = $db->prepare( $stm );
$rv = $dbs->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

while(my @row = $dbs->fetchrow_array()) {
         my $i = $row[0];
         my $n = $row[1];
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
             if($v eq 'Sun'){
                $s1 = "SELECTED";
            }
            elsif($v == 'Moon'){
                $s2 = "SELECTED";
            }

            $v = qq(<select id="theme" name="var$i">
                   <option $s0>Standard</option>
                   <option $s1>Sun</option>
                   <option $s2>Moon</option>
                   <option $s3>Earth</option>
                </select>);	
        }
        elsif($n ne "RELEASE_VER"){		 
             $v = '<input name="var'.$i.'" type="text" value="'.$v.'" size="12">';
        }



       $tbl = qq($tbl 
       <tr class="r0" align="left">
            <td>$n</td>
            <td>$v</td>
                <td>$d</td>   
        </tr>);
}


my  $frmVars = qq(
     <form id="frm_vars" action="config.cgi">$tbl
      <tr class="r1">		
         <td colspan="3" align=right><b>System Settings In -> $dbname</b>&nbsp;<input type="submit" value="Change"/></td>
        </tr>	
        <input type="hidden" name="sys" value="1"/>
        </table></form><br>);



$tbl = qq(<table id="cnf_fix" class="tbl" border="0" width="$PRC_WIDTH%">
              <tr class="r0"><td colspan="2"><b>* DATA FIX *</b></td></tr>
             );
my $cats = &cats;			 
my  $frmDB = qq(
     <form id="frm_DB" action="config.cgi">$tbl
        <tr class="r1" align="left"><th>Extra Action</th><th>Description</th></tr>
        <tr class="r0" align="left"><td><input type="checkbox" name="reset_cats"/>Reset Categories</td><td>Resets Categories to factory values (will initiate logoff).</td></tr>
        <tr class="r1" align="left"><td><input type="checkbox" name="reset_syst"/>Reset Settings</td><td>Resets system settings to default values.</td></tr>
        <tr class="r0" align="left"><td><input type="checkbox" name="wipe_syst"/>Wipe Settings</td><td>Resets and wipes system settings for migration  (will initiate logoff).</td></tr>
        <tr class="r1" align="left"><td><input type="checkbox" name="del_by_cats"/>Delete by Category <font color=red>*UD</font><br>$cats</td><td>Selects and displays by category logs to delete.</td></tr>
        <tr class="r0" align="left"><td><input type="checkbox" name="del_from"/>Delete from Date <font color=red>*UD</font><br><input id="fldFrom" size/></td><td>Selects and displays from a date to into deep past logs to delete..</td></tr>
        <tr class="r1">		
         <td colspan="2" align="right"><b>Data maintenance for -> $dbname</b>&nbsp;<input type="submit" value="Fix"/></td>
        </tr>			
        <tr class="r1" align="left">
             <td colspan="2">Perform this change/check in the event of experiencing data problems. Or periodically for data check and maintenance. <br>
                                 <font color="red">WARNING!</font> Checking any of the above extra actions will cause loss
                                                  of your changes. Please, export/backup first.<br><font color=red>*UD</font> - Under Development, not working!</td>
        </tr>
        <input type="hidden" name="db_fix" value="1"/>
        </table></form><br>
        );
$tbl = qq(<table id="cnf_fix" class="tbl" border="1" width="$PRC_WIDTH%">
              <tr class="r0"><td colspan="2"><b>* CHANGE PASSWORD *</b></td></tr>
             );
my  $frmPASS = qq(
     <form id="frm_PASS" action="config.cgi">$tbl
        <tr class="r1" align="left"><td style="width:100px">Existing:</td><td><input type="password" name="existing" value="" size="12"/></td></tr>
        <tr class="r1" align="left"><td>New:</td><td><input type="password" name="new" value="" size="12"/></td></tr>
        <tr class="r1" align="left"><td>Confirmation:</td><td><input type="password" name="confirm" value="" size="12"/></td></tr>
        <tr class="r1">		
         <td colspan="2" align="right"><b>Password change for -> $userid</b>&nbsp;<input type="submit" value="Change"/></td>
        </tr>			
        <input type="hidden" name="pass_change" value="1"/>
        </table></form><br>
        );


#
#Page printout from here!
#
my $prc_hdr = $PRC_WIDTH-2;
  print qq(
<a name="top"/><center>
    <div>$frm</div>
  <div>$frmVars</div>
    <div>$frmDB</div>
    <div>$frmPASS</div>
    <div id="rz" style="text-align:center;width:$PRC_WIDTH%;">
                <a href="#top">&#x219F;</a>&nbsp;Configuration status -> <b>$status</b>&nbsp;<a href="#bottom">&#x21A1;</a></div>		
            <br><div id="rz" style="text-align:center;width:$PRC_WIDTH%;">
            <a href="main.cgi"><h3>Back to Main Log</h3></a><h3><a href="login_ctr.cgi?logout=bye">LOGOUT</a></h3></div>
            <br><hr> 
            
            <table border="0">
                <tr><td><H3>CSV File Format</H3></td></tr> 
                <form action="config.cgi" method="post" enctype="multipart/form-data"> 
                <tr style="border-left: 1px solid black;"><td> 
                        <b>Import Categories</b>: <input type="file" name="data_cat" /></td></tr> 
                <tr style="border-left: 1px solid black;"><td style="text-align:right;">
                        <input type="submit" name="Submit" value="Submit"/></p></td></tr> 
                </form> 
                <form action="config.cgi" method="post" enctype="multipart/form-data"> 
                <tr style="border-top: 1px solid black;border-right: 1px solid black;"><td> 
                        <b>Import Log</b>: <input type="file" name="data_log" /></td></tr> 
                <tr style="border-right: 1px solid black;"><td style="text-align:right;"> 
                        <input type="submit" name="Submit" value="Submit"/></p></td></tr> 
                </form> 
                    <tr><td style="text-align:right"><H3>To Server -> $sys -> $dbname</H3></td></tr>
            </table>
    </div>
                    
                    <br><div><a href="#top">&#x219F;</a>&nbsp;&nbsp;&nbsp;[<a href="config.cgi?csv=1">Export Log to CSV</a>] &nbsp;
                     [<a href="config.cgi?csv=2">View the Log in CSV Format</a>]</div> 					
                    <br><div>[<a href="config.cgi?csv=3">Export Categories to CSV</a>] &nbsp;
                    [<a href="config.cgi?csv=4">View the Categories in CSV Format</a>]</div> 
                    <hr>

                    <center>
                    <div id="rz" style="text-align:left; position:relative;width:640px; padding:10px;">
                    <h2>L-Tags Specs</h2>					
                    <p>
                    Life Log Tags are simple markup allowing fancy formatting and functionality 
                    for your logs HTML layout.
                    </p>
                    <p>
                    <b>&#60;&#60;B&#60;<i>{Text To Bold}</i><b>&#62;</b>
                    </p>
                    <p>
                    <b>&#60;&#60;I&#60;<i>{Text To Italic}</i><b>&#62;</b>
                    </p>					
                    <p>
                    <b>&#60;&#60;TITLE&#60;<i>{Title Text}</i><b>&#62;</b>
                    </p>
                    <p>
                    <b>&#60;&#60;LIST&#60;<i>{List of items delimited by new line to terminate item or with '~' otherwise.}</i><b>&#62;</b>
                    </p>
                    <p>
                    <b>&#60;&#60;IMG&#60;<i>{url to image}</i><b>&#62;</b>
                    </p>
                    <p>
                        <b>&#60;&#60;FRM&#60;<i>{file name}_frm.png}</i><b>&#62;</b><br><br>
                        *_frm.png images file pairs are located in the ./images folder of the cgi-bin directory.<br>
                        These are manually resized by the user. Next to the original.
                        Otherwise considered as stand alone icons. *_frm.png Image resized to ->  width="210" height="120"
                        <br><i>Example</i>:
                        <pre>
        ../cgi-bin/images/
            my_cat_simon_frm.png
            my_cat_simon.jpg	

          For log entry, place:

      &#60;&#60;FRM&#62;my_cat_simon_frm.png&#62; &#60;&#60;TITLE&#60;Simon The Cat&#62;
      This is my pet, can you hold him for a week while I am on holiday?
            </pre>
                    </p>
                    <p>
                    <b>&#60;&#60;LNK&#60;<i>{url to image}</i><b>&#62;</b><br><br>
                    Explicitly tag an URL in the log entry. 
                    Required if using in log IMG or FRM tags. 
                    Otherwise link appears as plain text.
                    </p>
                    <hr>
          </p>
                        <h3>Log Page Particulars</h3>
                        &#x219F; or &#x21A1; - Jump links to top or bottom of page respectivelly.
                    </p>
                    </div>
                    </center><a name="bottom"/><a href="#top">&#x219F;</a>
                    <hr>
    );

print '</center>';


print $cgi->end_html;
$db->disconnect();

exit;

sub processSubmit {

my $change = $cgi->param("cchg");
my $chgsys = $cgi->param("sys");
my $chdbfix  = $cgi->param("db_fix");
my $passch = $cgi->param("pass_change");
my $s;
my $d;

try{

$dbs = $db->prepare( $stmtCat );
$rv = $dbs->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
    
if($passch){
    my ($ex,$ne,$cf) = ($cgi->param("existing"),$cgi->param("new"),$cgi->param("confirm"));
    if($ne ne $cf){
         $status = "New password must match confirmation!";
         print "<center><div><p><font color=red>Client Error</font>: $status</p></div></center>";
    }
    else{
        if(&confirmExistingPassword($ex)){
             &changePassword($ne);
             $status = "Password Has Been Changed";
        }
        else{
            $status = "Wrong existing password was entered, are you user by alias: $userid ?";
            print "<center><div><p><font color=red>Client Error</font>: $status</p></div></center>";
        }
    }	
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
                     $s = "  LOG SET ID_CAT=1 WHERE rowid=".$r[0].";";
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
    $status = "Upadated Categories!";
}


if($change > 1){

        #UNDER DEVELOPMENT!
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
}elsif($chdbfix){		
    &processDBFix;
    $status = "Performed Database Fixes!";
}


}
catch{	  
    $ERROR = qq(<p><font color=red><b>SERVER ERROR</b></font> -> $_</p>);
}
}

sub confirmExistingPassword {
        my $pass = $_[0];
      my $crypt = encryptPassw($pass);
        my $sql = "SELECT ALIAS, PASSW from AUTH WHERE ALIAS='$userid' AND PASSW='$crypt';";
    #		print "<center><div><p><font color=red><b>DEBUG</b></font>:[$pass]<br>$sql</p></div></center>";
        $dbs = $db->prepare($sql);
        $dbs->execute();
        if($dbs->fetchrow_array()){
            return 1;
        }
        return 0;
}
sub changePassword {
      my $pass = encryptPassw($_[0]);
        $dbs = $db->prepare("UPDATE AUTH SET PASSW='$pass' WHERE ALIAS='$userid';");
        $dbs->execute();
        if($dbs->fetchrow_array()){
            return 1;
        }
        return 0;	
}
sub encryptPassw {
    return uc crypt $_[0], hex $cipher_key;
}



sub processDBFix {

     my $rs_syst = $cgi->param("reset_syst");
     my $rs_cats = $cgi->param("reset_cats");
     my $wipe_ss = $cgi->param("wipe_syst");
     my $issue;
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
        $dbs = dbExecute('select rowid, DATE from LOG ORDER BY DATE;');			
        while(my @row = $dbs->fetchrow_array()) {
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
            $issue = "DELETE FROM LOG WHERE rowid=$del;";
                    #print "$issue\n<br>";
                    my $st_del = $db->prepare($issue);
                    $st_del->execute();
        }

        #Renumerate!
        my $cnt = 1;
        my $st_upd;
        $dbs = dbExecute("select count(rowid) from LOG;");		
        @row = $dbs->fetchrow_array();
        $cntr_upd =$row[0];
        
        
        $dbs = dbExecute("select rowid, RTF from LOG order by DATE;");		
        while(@row = $dbs->fetchrow_array()) {
            $issue    = "UPDATE LOG SET rowid=$cnt WHERE rowid=$row[0];";
            $st_upd = $db->prepare($issue);
            $st_upd->execute();
            if($row[1]){#RTF				
                my @doc = dbExecute("SELECT LID FROM NOTES WHERE LID='$row[0]';");
                if(scalar @doc>0){
                          dbExecute("UPDATE NOTES SET LID = $cnt WHERE LID='$row[0]';");					
                }
            }				
            $cnt++;
        }			
        # Delete Orphaned Notes entries.			
        $dbs = dbExecute("SELECT LID, LOG.rowid from NOTES LEFT JOIN LOG ON 
                                        NOTES.LID = LOG.rowid WHERE LOG.rowid is NULL;");			
        while(my @row = $dbs->fetchrow_array()) {				
            $db->do("DELETE FROM NOTES WHERE LID=$row[0];");
        }

                    
        &resetCategories if $rs_cats;
        &resetSystemConfiguration($db) if $rs_syst;			
        &wipeSystemConfiguration if $wipe_ss;

        $db->do('COMMIT;');
        $db->disconnect();
        $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) or die "<p>Error->"& $DBI::errstri &"</p>";
        $dbs = $db->do("VACUUM;");

        if($LOGOUT){
                &logout; 
        }		
            
            
}
catch{	
    $db->do('ROLLBACK;');
    die qq(@&processDBFix error:$_ with statement->$issue for $date update counter:$cntr_upd);	
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

        open(my $fh, '<', $LOG_PATH.'main.cnf' ) or die "Can't open main.cnf: $!";
        my $db = shift;
        my ($did,$name, $value, $desc);
        my $inData = 0;
        my $err = "";
        my %vars = {};

try{
          
        my $insert = $db->prepare('INSERT INTO CONFIG VALUES (?,?,?,?)');
        my $update = $db->prepare("UPDATE CONFIG SET VALUE=? WHERE ID=?;");
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
                                                                my $name  = $nash{$id};
                                                                my $value = $hsh{$key};
                                                                if($vars{$id}){
                            $err .= "UID{$id} taken by $vars{$id}-> $line\n";
                                                                }
                                                                else{
                                                                    $dbs = dbExecute(
                                                                        "SELECT ID, NAME, VALUE, DESCRIPTION FROM CONFIG WHERE NAME LIKE '$name';");
                                                                    $inData = 1;
                                                                    my @row = $dbs->fetchrow_array();
                                                                    if(scalar @row == 0){
                                                                            $insert->execute($id,$name,$value,$tick[1]);
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
        &getConfiguration;
 } catch{	 	
      close $fh;	
      print $cgi->header;
        print "<font color=red><b>SERVER ERROR!</b></font><br> ".$_."<br><pre>$err</pre>";
    print $cgi->end_html;
        exit;
 }
}


sub logout{
    $session->delete();
    $session->flush();
    print $cgi->redirect("login_ctr.cgi");
    exit;
}


sub changeSystemSettings {
    try{
            $dbs = dbExecute("SELECT ID, NAME FROM CONFIG;");
            while (my @r=$dbs->fetchrow_array()){ 
                my $var = $cgi->param('var'.$r[0]);
                if(defined $var){					
                    switch ($r[1]) {
                        case "REC_LIMIT" {$REC_LIMIT=$var;  updCnf($r[0],$var)}
                        case "TIME_ZONE" {$TIME_ZONE=$var;  updCnf($r[0],$var)}
                        case "PRC_WIDTH" {$PRC_WIDTH=$var;  updCnf($r[0],$var)}
                        case "SESSN_EXPR"{$SESSN_EXPR=$var; updCnf($r[0],$var)}
                        case "DATE_UNI"  {$DATE_UNI=$var; updCnf($r[0],$var)}
                        case "LANGUAGE"  {$LANGUAGE=$var; updCnf($r[0],$var)}
                        case "AUTHORITY" {$AUTHORITY=$var; updCnf($r[0],$var)}
                        case "IMG_W_H"   {$IMG_W_H=$var; updCnf($r[0],$var)}
                        case "AUTO_WRD_LMT"{$AUTO_WRD_LMT=$var; updCnf($r[0],$var)}
                        case "AUTO_LOGIN" {$AUTO_LOGIN=$var; updCnf($r[0],$var)}
                        case "FRAME_SIZE" {$FRAME_SIZE=$var; updCnf($r[0],$var)}
                        case "RTF_SIZE"   {$RTF_SIZE=$var; updCnf($r[0],$var)}
                        case "THEME"      {$THEME=$var; updCnf($r[0],$var)}
                     }
                }
            }
    }
    catch{
        print "<font color=red><b>SERVER ERROR->changeSystemSettings</b></font>:".$_;
    }
}

sub updCnf {
    my ($id, $val, $s) = @_;    
    $s = "UPDATE CONFIG SET VALUE='".$val."' WHERE ID=".$id.";"; 
    try{
          dbExecute($s); 
    }
    catch{
        print "<font color=red><b>SERVER ERROR</b>->updCnf[$s]</font>:".$_;
    }
}

sub exportLogToCSV {
    try{
          
        my $csv = Text::CSV->new ( { binary => 1, strict => 1 , quote_space=>1, auto_diag => 1, eol => $/} ); 		  
        $dbs = dbExecute("SELECT * FROM LOG;");
        if($csvp==2){
                 print $cgi->header(-charset=>"UTF-8", -type=>"text/html");	
                 print "<pre>\n";
            }
            else{
                 print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>"$dbname.csv");
            }
            
         # print "ID_CAT,DATE,LOG,AMOUNT, AFLAG\n";
            while (my $r=$dbs->fetchrow_arrayref()){ 
                         print $csv->print(*STDOUT, $r)."\n";
            }
            if($csvp==1){			
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

sub exportCategoriesToCSV {
    try{
          
        my $csv = Text::CSV->new ( { binary => 1, strict => 1,eol => $/ } );
        $dbs = dbExecute("SELECT ID, NAME, DESCRIPTION FROM CAT ORDER BY ID;");
        if($csvp==4){
                 print $cgi->header(-charset=>"UTF-8", -type=>"text/html");	
                 print "<pre>\n";
        }
        else{
         print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>"$dbname.categories.csv");
        }
            
        #print "ID,NAME,DESCRIPTION\n";
        while (my $row=$dbs->fetchrow_arrayref()){ 
                print $csv->print(*STDOUT, $row),"\n";
        }
        if($csvp==4){			
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
    my $csv = Text::CSV->new ( { binary => 1, strict => 1, eol => $/ } ); 	
    while (my $line = <$hndl>) {
        chomp $line;
        if ($csv->parse($line)) { 
              my @flds   = $csv->fields();
            updateCATDB(@flds);
        }else{
              warn "Data could not be parsed: $line\n";
          }		 
    }
}

sub updateCATDB {
    my @flds = @_;
    if(@flds>2){
    try{	
            my $id   = $flds[0];
            my $name = $flds[1];
            my $desc = $flds[2];
            
            #is it existing entry?
            $dbs = dbExecute("SELECT ID, NAME, DESCRIPTION FROM CAT WHERE ID = '$id';");			
            if(not defined $dbs->fetchrow_array()){
                    $dbs = $db->prepare('INSERT INTO CAT VALUES (?,?,?)');
                    $dbs->execute($id, $name, $desc);
                    $dbs->finish;
            }
            else{
                #TODO Update
            }
        
    }
    catch{
        print "<font color=red><b>SERVER ERROR</b>->updateCATDB</font>:".$_;
    }
    }
}
sub importLogCSV {
    my $hndl = $cgi->upload("data_log");
    my $csv = Text::CSV->new ( { binary => 1, strict => 1, eol => $/ } ); 	
    while (my $line = <$hndl>) {
            chomp $line;
            if ($csv->parse($line)) { 
                  my @flds   = $csv->fields();
                updateLOGDB(@flds);
            }else{
                     warn "Data could not be parsed: $line\n";
            } 
    }	
    $db->disconnect();
    print $cgi->redirect('main.cgi');
    exit;
}

sub updateLOGDB {
    my @flds = @_;
    if(@flds>3){
    try{	
            my $id_cat = $flds[0];
            my $date   = $flds[1];
            my $log    = $flds[2];
            my $amv    = $flds[3];
            my $amf    = $flds[4];
            my $rtf    = $flds[5];
            my $pdate = DateTime::Format::SQLite->parse_datetime($date);
            #Check if valid date log entry?
            if($id_cat==0||$id_cat==""||!$pdate){
                return;
            }
            #is it existing entry?
            $dbs = $db->prepare("SELECT ID_CAT, DATE, LOG, AMOUNT, AFLAG, RTF  FROM LOG WHERE date = '$date';");
            $dbs->execute();
            if(!$dbs->fetchrow_array()){
                    $dbs = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?,?,?)');
                    $dbs->execute( $id_cat, $pdate, $log, $amv, $amf, $rtf);
            }
            #Renumerate
            $dbs = $db->prepare('select rowid from LOG ORDER BY DATE;');
            $dbs->execute();
            my @row = $dbs->fetchrow_array();
            my $cnt = 1;
             while(my @row = $dbs->fetchrow_array()) {
            my $st_upd = $db->prepare("UPDATE LOG SET rowid=".$cnt.
                                        " WHERE rowid='".$row[0]."';");
                $st_upd->execute();
                $cnt = $cnt + 1;
            }
            $dbs->finish;
    }
    catch{
        print "<font color=red><b>SERVER ERROR</b>->exportLogToCSV</font>:".$_;
    }
    }
}


sub getConfiguration {
    try{
        $dbs = dbExecute("SELECT * FROM CONFIG;");
        while (my @r=$dbs->fetchrow_array()){
            
            switch ($r[1]) {
                case "REC_LIMIT"    {$REC_LIMIT=$r[2]}
                case "TIME_ZONE"    {$TIME_ZONE=$r[2]}
                case "PRC_WIDTH"    {$PRC_WIDTH=$r[2]}		
                case "SESSN_EXPR"   {$SESSN_EXPR=$r[2]}
                case "DATE_UNI"     {$DATE_UNI=$r[2]}
                case "LANGUAGE"     {$LANGUAGE=$r[2]}
                case "IMG_W_H"      {$IMG_W_H=$r[2]}
                case "AUTO_WRD_LMT" {$AUTO_WRD_LMT=$r[2]}
                case "AUTO_LOGIN" 	{$AUTO_LOGIN=$r[2]}
                case "FRAME_SIZE"	{$FRAME_SIZE=$r[2]}
                case "RTF_SIZE"		{$RTF_SIZE=$r[2]}
                case "THEME"        {$THEME= $r[2]}
            }
        }
    }
    catch{
        print "<font color=red><b>SERVER ERROR</b></font>:".$_;
    }

}

sub cats{

        my $cats = qq(<select id="cats" name="cats"><option value="0">---</option>\n);
        $dbs = dbExecute("SELECT ID, NAME, DESCRIPTION FROM CAT ORDER BY ID;");
        while ( my @row = $dbs->fetchrow_array() ) {

                $cats .= qq(<option value="$row[0]">$row[1]</option>\n);
        }
        $cats .= '</select>';

    return $cats;
}

sub dbExecute{
    my $ret	= $db->prepare(shift);
       $ret->execute() or die "<p>Error->"& $DBI::errstri &"</p>";
    return $ret;
}

sub error{
    my $url = $cgi->url();
    print qq(<h2>Sorry Encountered Errors</h2><p>Page -> $url</p><p>$ERROR</p>);
    print qq(<h3>CGI Parameters</h3>);
    print "<ol>\n";
    foreach ($cgi->param){
        print '<li>'.$_.'=='. $cgi->param($_).'</li>';
    }
    print "</ol>\n";
    print "<a href=$cgi>Return to -> $url</a>";
    print $cgi->end_html;
    $db->disconnect();
    exit;
}