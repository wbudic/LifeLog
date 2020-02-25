#!/usr/bin/perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#

use strict;
use warnings;
use Switch;


use CGI;
use CGI::Session '-ip_match';
use DBI;
use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;

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
my $db = DBI->connect($dsn, $userid, $password, { RaiseError => 1 })  or LifeLogException->throw($DBI::errstri);

#Fetch settings
my $imgw = 210;
my $imgh = 120;
Settings::getConfiguration($db);
Settings::getTheme();
my $human = DateTime::Format::Human::Duration->new();


### Page specific settings Here
my $PRC_WIDTH = &Settings::pagePrcWidth;
my $TH_CSS = &Settings::css;
my $BGCOL  = &Settings::bgcol;
#Set to 1 to get debug help. Switch off with 0.
my $DEBUG  = &Settings::debug;
#END OF SETTINGS

my $today = DateTime->now;
$today->set_time_zone(&Settings::timezone);

my $tbl_rc =0;
my ($stm,$st, $rv);

my $tbl = '<a name="top"></a><form name="frm_log_del" action="data.cgi" onSubmit="return formDelValidation();">
           <table class="tbl_rem" width="'.$PRC_WIDTH.'%">
           <tr class="hdr" style="text-align:left;"><th>Date <a href="#bottom">&#x21A1;</a></th> <th>Time</th> <th>Log</th> <th>Category</th></tr>';


my $datediff = $cgi->param("datediff");
my $confirmed = $cgi->param('confirmed');
if ($datediff){
         print $cgi->header(-expires=>"+6os");
         print $cgi->start_html(-title => "Date Difference Report", -BGCOLOR => $BGCOL,
                 -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
                 -style =>{-type => 'text/css', -src => "wsrc/$TH_CSS"}

        );
        &DisplayDateDiffs;
}elsif ($confirmed){
    &ConfirmedDelition;
}else{
    print $cgi->redirect('main.cgi') if not $cgi->param('chk');
    &NotConfirmed;
}


print $cgi->end_html;
$db->disconnect();
exit;

sub DisplayDateDiffs{

    $tbl = '<table class="tbl" width="'.$PRC_WIDTH.'%">
        <tr class="r0"><td colspan="2"><b>* DATE DIFFERENCES *</b></td></tr>';

    $stm = 'SELECT DATE, LOG FROM VW_LOG WHERE ';
    my  @ids = $cgi->param('chk');

     @ids = reverse @ids;

    foreach (@ids){
        $stm .= "PID = " . $_ ."";
        if(  \$_ != \$ids[-1]  ) {
            $stm = $stm." OR ";
        }
    }
    $stm .= ' ORDER BY PID;';
    print $cgi->pre("###[stm:$stm]") if($DEBUG);
    $st = $db->prepare( $stm );
    $st->execute();

    my ($dt,$dif,$first,$last,$tnext, $dt_prev) = (0,0,0,0,0,$today);
    while(my @row = $st->fetchrow_array()) {
         my $rdat = $row[0];
         my $rlog = $row[1];
         $rlog =~ m/\n/;
         $dt  = DateTime::Format::SQLite->parse_julianday( $rdat );
         $dt->set_time_zone(&Settings::timezone);
         $dif = dateDiff($dt_prev, $dt);
         $tbl .= '<tr class="r1"><td>'. $dt->ymd . '</td>
                    </td><td style="text-align:left;">'.$rlog."</td></tr>".
                 '<tr class="r0"><td colspan="2">'.$dif.'</td> </tr>';
         $last = $dt_prev;
         $dt_prev = $dt;
         if($tnext){
             $dif = dateDiff($today, $dt,'');
             $tbl .= '<tr class="r0"><td colspan="2">'.$dif. '</td> </tr>';
         }
         else{$tnext=1; $first = $dt;}
    }
    if($first != $last){
        $dif = dateDiff($first, $dt_prev,'(first above)');
        $tbl .= '<tr class="r0"><td colspan="2">'.$dif. '</td> </tr>';
    }
    $tbl .= '</table>';

print '<a name="top"></a><center><div>'.$tbl.'</div><br><div><a href="main.cgi">Back to Main Log</a></div></center>';
}


sub dateDiff {
    my($d1,$d2,$ff,$sw)=@_;
    if($d1->epoch()>$d2->epoch()){
        $sw = $d1;
        $d1 = $d2;
        $d2 = $sw;
    }else{$sw="";}
    my $dur = $human->format_duration_between($d1, $d2);
    my ($t1,$t2) = ("","");
    $t1 = "<font color='red'> today </font>" if ($d1->ymd() eq $today->ymd());# Notice in perl == can't be used here!
    $t2 = "<font color='red'> today </font>" if ($d2->ymd() eq $today->ymd());
return sprintf( "%s <br>between $ff $t1 %s and $t2 %s[%s]", $dur, boldDate($d1), boldDate($d2), $d1->ymd());

}

sub boldDate {
    my($d)=@_;
return "<b>".$d->ymd()."</b> ".$d->hms;
}


sub ConfirmedDelition {

try{

    foreach my $id ($cgi->param('chk')){
        print $cgi->p("###[deleting:$id]")  if(Settings::debug());
        $st = $db->prepare("DELETE FROM LOG WHERE rowid = '$id';");
        $rv = $st->execute() or die or die "<p>Error->"& $DBI::errstri &"</p>";
        $st = $st = $db->prepare("DELETE FROM NOTES WHERE LID = '$id';");
        $rv = $st->execute();

       # if($rv == 0) {
          #   die "<p>Error->"& $DBI::errstri &"</p>";
       # }

    }
    $st->finish;

    print $cgi->redirect('main.cgi');

}catch{
    print $cgi->p("<font color=red><b>ERROR</b></font>  " . $_);
}

}

sub NotConfirmed {

    my $stmS = "SELECT ID, PID, (select NAME from CAT WHERE ID_CAT == CAT.ID) as CAT, DATE, LOG from VW_LOG WHERE";
    my $stmE = " ORDER BY DATE DESC, ID DESC;";

    #Get ids and build confirm table and check
    my $stm = $stmS ." ";
        foreach my $id ($cgi->param('chk')){
            $stm = $stm . "ID = " . $id . " OR ";
        }
        $stm =~ s/ OR $//; $stm .= $stmE;

    $st = $db->prepare( $stm );
    $rv = $st->execute();
    print $cgi->header(-expires=>"+6os");
    print $cgi->start_html(-title => "Personal Log Record Removal", -BGCOLOR => $BGCOL,
            -script=>{-type => 'text/javascript', -src => 'wsrc/main.js'},
            -style =>{-type => 'text/css', -src => "wsrc/$TH_CSS"}

    );

    print $cgi->pre("###NotConfirmed($rv,$st)->[stm:$stm]")  if($DEBUG);

    my $r_cnt = 0;
    my $rs = "r1";


    while(my @row = $st->fetchrow_array()) {

        my $ct = $row[2];
        my $dt = DateTime::Format::SQLite->parse_datetime( $row[3] );
        my $log = log2html($row[4]);

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

 $tbl = $tbl .  '<tr class="r0"><td colspan="4"><a name="bottom"></a><a href="#top">&#x219F;</a>
 <center>
 <h2>Please Confirm You Want<br>The Above Record'.$plural.' Deleted?</h2>
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
        $log =~ s/<<LNK<(.*?)>+/$url/osi;
    }

    if ( $log =~ /<<IMG</ ) {
            my $idx = $-[0] + 5;
            my $len = index( $log, '>', $idx );
            $sub = substr( $log, $idx + 1, $len - $idx - 1 );
            my $url = qq(<img src="$sub"/>);
            $log =~ s/<<IMG<(.*?)>+/$url/osi;
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
            $log =~ s/<<FRM<(.*?)>+/$lnk/o;
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
