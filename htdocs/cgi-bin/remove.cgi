#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#

use strict;
use warnings;
use Try::Tiny;
use Switch;

 
use CGI;
use CGI::Session '-ip_match';
use DBI;

use DateTime qw();
use DateTime::Format::SQLite;
use DateTime::Format::Human::Duration;
use Regexp::Common qw /URI/;

use lib "system/modules";
require Settings;

my $cgi = CGI->new;
my $session = new CGI::Session("driver:File",$cgi, {Directory => Settings::logPath()});
my $sid=$session->id();
my $dbname  =$session->param('database');
my $userid  =$session->param('alias');
my $password=$session->param('passw');

if(!$userid||!$dbname){
    print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
    exit;
}


my $database = Settings::logPath().$dbname;
my $dsn= "DBI:SQLite:dbname=$database";
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 }) or die "<p>Error->"& $DBI::errstri &"</p>";

#Fetch settings
my $imgw = 210;
my $imgh = 120;
Settings::getConfiguration($db);
Settings::getTheme();



### Page specific settings Here
my $PRC_WIDTH = &Settings::pagePrcWidth;
my $TH_CSS = &Settings::css;
my $BGCOL  = &Settings::bgcol;
#Set to 1 to get debug help. Switch off with 0.
my $DEBUG        = &Settings::debug;
#END OF SETTINGS

my $today = DateTime->now;
$today->set_time_zone(&Settings::timezone);

my %hshCats ={};
my $tbl_rc =0;
my $stm;
my $stmtCat = "SELECT ID, NAME FROM CAT;";
my $st = $db->prepare( $stmtCat );
my $rv = $st->execute();


while(my @row = $st->fetchrow_array()) {
    $hshCats{$row[0]} = $row[1];
}


my $tbl = '<form name="frm_log_del" action="remove.cgi" onSubmit="return formDelValidation();">
           <table class="tbl_rem" width="'.$PRC_WIDTH.'%">
           <tr class="hdr" style="text-align:left;"><th>Date</th> <th>Time</th><th>Log</th><th>Category</th></tr>';


my $datediff = $cgi->param("datediff");
my $confirmed = $cgi->param('confirmed');
if ($datediff){
         print $cgi->header(-expires=>"+6os");    
         print $cgi->start_html(-title => "Date Difference Report", -BGCOLOR => $BGCOL,
                 -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
                 -style =>{-type => 'text/css', -src => "wsrc/$TH_CSS"}

        );	  
        &DisplayDateDiffs;
}elsif (!$confirmed){
         print $cgi->header(-expires=>"+6os");    
         print $cgi->start_html(-title => "Personal Log Record Removal", -BGCOLOR => $BGCOL,
                 -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
                 -style =>{-type => 'text/css', -src => "wsrc/$TH_CSS"}

        );	  


        &NotConfirmed;
}else{
        &ConfirmedDelition;
}


print $cgi->end_html;
$db->disconnect();
exit;

sub DisplayDateDiffs{
    $tbl = '<table class="tbl" width="'.$PRC_WIDTH.'%">
        <tr class="r0"><td colspan="2"><b>* DATE DIFFERENCES *</b></td></tr>';

    $stm = 'SELECT DATE, LOG FROM LOG WHERE '; 
    my  @ids = $cgi->param('chk');

    foreach (@ids){
        $stm .= "rowid = '" . $_ ."'";
        if(  \$_ != \$ids[-1]  ) {
            $stm = $stm." OR ";
        }
    }
    $stm .= ';';
    $st = $db->prepare( $stm );
    $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";

    my $dt_prev = $today;
    while(my @row = $st->fetchrow_array()) {

         my $dt = DateTime::Format::SQLite->parse_datetime( $row[0] );
         my $dif = dateDiff($dt_prev, $dt);
         $tbl .= '<tr class="r1"><td>'. $dt->ymd . '</td> 
                    </td><td style="text-align:left;">'.$row[1]."</td></tr>".
                 '<tr class="r0"><td colspan="2">'.$dif. '</td> </tr>';	
        $dt_prev = $dt;
    }
    $tbl .= '</table>';

print '<center><div>'.$tbl.'</div><br><div><a href="main.cgi">Back to Main Log</a></div></center>';
}


sub dateDiff{
    my($d1,$d2)=@_;
    my $span = DateTime::Format::Human::Duration->new();
    my $dur = $span->format_duration($d2 - $d1);
return sprintf( "%s <br>between %s and %s", $dur, boldDate($d1), boldDate($d2));

}

sub boldDate{
    my($d)=@_;
return "<b>".$d->ymd."</b> ".$d->hms;
}


sub ConfirmedDelition{


    foreach my $id ($cgi->param('chk')){
        
        $st = $db->prepare("DELETE FROM LOG WHERE rowid = '$id';");
        $rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
        $st = $st = $db->prepare("DELETE FROM NOTES WHERE LID = '$id';");
        $rv = $st->execute();

        if($rv < 0) {
             print "<p>Error->"& $DBI::errstri &"</p>";
             exit;
        }
        
    }
    
    
    $st->finish;

    print $cgi->redirect('main.cgi');

}

sub NotConfirmed{

    my $stmS = "SELECT rowid, ID_CAT, DATE, LOG from LOG WHERE";
    my $stmE = " ORDER BY DATE DESC, rowid DESC;";

    #Get ids and build confirm table and check
    my $stm = $stmS ." ";
        foreach my $id ($cgi->param('chk')){
            $stm = $stm . "rowid = '" . $id . "' OR ";
        }
    #OR end to rid=0 hack! ;)
        $stm = $stm . "rowid = '0' " . $stmE;
    #
    $st = $db->prepare( $stm );
    $rv = $st->execute() or die "<p>Error->"& $DBI::errstri &"</p>";
    if($rv < 0) {
            print "<p>Error->"& $DBI::errstri &"</p>";
    }

    my $r_cnt = 0;
    my $rs = "r1";
    while(my @row = $st->fetchrow_array()) {

        my $ct = $hshCats{$row[1]};
        my $dt = DateTime::Format::SQLite->parse_datetime( $row[2] );
        my $log = log2html($row[3]);
        
        $tbl = $tbl . '<tr class="r1"><td class="'.$rs.'">'. $dt->ymd . "</td>" . 
            '<td class="'.$rs.'">' . $dt->hms . "</td>" .
            '<td class="'.$rs.'" style="font-weight:bold; color:maroon;">'."$log</td>\n".
            '<td class="'.$rs.'">' . $ct. '<input type="hidden" name="chk" value="'.$row[0].'"></td></tr>';
        if($rs eq "r1"){
        $rs = "r0";
        }
        else{
            $rs = "r1";
        }
        $r_cnt++;
    }
    my $plural = "";
    if($r_cnt>1){
        $plural = "s";
    }

 $tbl = $tbl .  '<tr class="r0"><td colspan="4">
 <center>
 <h2>Please Confirm You Want <br/>The Above Record'.$plural.' Deleted?</h2>
 (Or hit you Browsers Back Button!)</center>
 </td></tr>
 <tr class="r0"><td colspan="4"><center>
 <input type="submit" value="I AM CONFIRMING!">
 </center>
 <input type="hidden" name="confirmed" value="1">
</td></tr>
</table></form>';

print '<center><div>' . $tbl .'</div></center>';

 $st->finish;
}

sub log2html{
    my $log = shift;
    my ($re_a_tag, $sub)  = qr/<a\s+.*?>.*<\/a>/si;
    $log =~ s/''/'/g;    
    $log =~ s/\r\n/<br>/gs;
    $log =~ s/\\n/<br>/gs;

    if ( $log =~ /<<LNK</ ) {
        my $idx = $-[0] + 5;
        my $len = index( $log, '>', $idx );
        $sub = substr( $log, $idx + 1, $len - $idx - 1 );
        my $url = qq(<a href="$sub" target=_blank>$sub</a>);
        $log =~ s/<<LNK<(.*?)>/$url/osi;
    }

    if ( $log =~ /<<IMG</ ) {
            my $idx = $-[0] + 5;
            my $len = index( $log, '>', $idx );
            $sub = substr( $log, $idx + 1, $len - $idx - 1 );
            my $url = qq(<img src="$sub"/>);
            $log =~ s/<<IMG<(.*?)>/$url/osi;
    }
    elsif ( $log =~ /<<FRM</ ) {
            my $idx = $-[0] + 5;
            my $len = index( $log, '>', $idx );
            $sub = substr( $log, $idx + 1, $len - $idx - 1 );
            my $lnk = $sub;
            if ( $lnk =~ /_frm.png/ ) {
                my $ext = substr( $lnk, index( $lnk, '.' ) );
                $lnk =~ s/_frm.png/$ext/;
                if ( not -e "./images/$lnk" ) {
                    $lnk =~ s/$ext/.jpg/;
                    if ( not -e "./images/$lnk" ) {
                        $lnk =~ s/.jpg/.gif/;
                    }
                }
                $lnk =
                  qq(\n<a href="./images/$lnk" style="border=0;" target="_IMG">
			      <img src="./images/$sub" width="$imgw" height="$imgh" class="tag_FRM"/></a>);
            }
            else {
                #TODO fetch from web locally the original image.
                $lnk =  qq(\n<img src="$lnk" width="$imgw" height="$imgh" class="tag_FRM"/>);
            }
            $log =~ s/<<FRM<(.*?)>/$lnk/o;
        }

    #Replace with a full link an HTTP URI
    if ( $log =~ /<iframe / ) {
        my $a = q(<iframe width="560" height="315");
        my $b;
        switch (&Settings::frameSize) {
            case "0" { $b = q(width="390" height="215") }
            case "1" { $b = q(width="280" height="180") }
            case "2" { $b = q(width="160" height="120") }
            else {
                $b = &Settings::frameSize;
            }
        }
        $b = qq(<div><iframe align="center" $b);
        $log =~ s/$a/$b/o;
        $a = q(</iframe>);
        $b = q(</iframe></div>);
        $log =~ s/$a/$b/o;        
    }
    else {
        my @chnks = split( /($re_a_tag)/si, $log );
        foreach my $ch_i (@chnks) {
            next if $ch_i =~ /$re_a_tag/;
            next if index( $ch_i, "<img" ) > -1;
            $ch_i =~ s/https/http/gsi;
            $ch_i =~ s/($RE{URI}{HTTP})/<a href="$1" target=_blank>$1<\/a>/gsi;
        }
        $log = join( '', @chnks );
    }

    #$log =~ s/\<\</&#60;&#60/gs;
    #$log =~ s/\>\>/&#62&#62;/gs;

return $log;
}
