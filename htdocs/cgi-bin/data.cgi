#!/usr/bin/env perl
#
# Programed in vim by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use v5.30; #use diagnostics;
use warnings;
use strict;
no warnings "experimental::smartmatch";

use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;
use DateTime::Format::Human::Duration;
use Regexp::Common qw /URI/;
use Text::CSV;
 

use lib "system/modules";
require Settings;

my $human     = DateTime::Format::Human::Duration->new();
my $db        = Settings::fetchDBSettings();
my $PRC_WIDTH = Settings::pagePrcWidth();
my $DEBUG     = Settings::debug();
my $today     = Settings::today();
my $tbl_rc    = 0;
my $imgw      = 210;
my $imgh      = 120;
my $cgi       = Settings::cgi(); 
my $opr       = $cgi->param("opr"); $opr=0 if !$opr;
my $confirmed = $cgi->param('confirmed');

if ($opr == 1){
    DisplayDateDiffs();
    exit;
}
if ($opr == 3){
    PrintView();
}
elsif ($confirmed){
    DeletionConfirmed();
}else{
    print $cgi->redirect('main.cgi') if not $cgi->param('chk');    
    ConfirmForDeletionPage();    
}
$db->disconnect();

sub DisplayDateDiffs {
       
    my $tbl = '<table class="tbl" width="'.$PRC_WIDTH.'%">
        <tr class="r0"><td colspan="2"><b>* DATE DIFFERENCES *</b></td></tr>';

    my $stm = 'SELECT DATE, LOG FROM VW_LOG WHERE ';
    my @ids = $cgi->param('chk');
       @ids = reverse @ids;
    foreach (@ids){
        $stm .= "PID = " . $_ ."";
        if(  \$_ != \$ids[-1]  ) {
            $stm = $stm." OR ";
        }
    }
    $stm .= ' ORDER BY PID;';
    print $cgi->pre("###[stm:$stm]") if($DEBUG);
    my $st = Settings::selectRecords($db, $stm);
    my ($dt,$dif,$first,$last,$tnext, $dt_prev) = (0,0,0,0,0,$today);
    while(my @row = $st->fetchrow_array()) {
         my $rdat = $row[0];
         my $rlog = $row[1];
         $rlog =~ m/\n/;
         $dt  = DateTime::Format::SQLite->parse_julianday( $rdat );
         $dt -> set_time_zone(&Settings::timezone);
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
    printHeader("Date Difference Report");
    print '<a name="top"></a><center><div>'.$tbl.'</div><br><div><a href="main.cgi">Back to Main Log</a></div></center>';
    print $cgi->end_html();

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

sub printHeader {

my $title = shift;
print $cgi->header(-expires=>"+6os");
&Settings::setupTheme;
print $cgi->start_html(-title => $title, -BGCOLOR => Settings::theme('colBG'),
            -script=> [ {-type => 'text/javascript', -src => 'wsrc/jquery.js'},
                        {-type => 'text/javascript', -src => 'wsrc/jquery-ui.js'},
                        {-type => 'text/javascript', -src => 'wsrc/main.js'}
                        ],                
            -style => [ {-type => 'text/css', -src => Settings::theme('css')},                        
                        {-type => 'text/css', -src => 'wsrc/jquery-ui.css'},
                        {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'},
                        {-type => 'text/css', -src => 'wsrc/jquery-ui.theme.css'}                        
                        ],                        
            -onload => "onBodyLoadGeneric()"
            )
}

sub ConfirmForDeletionPage {

try{    
    my $SQLID = 'rowid'; $SQLID = 'ID' if( Settings::isProgressDB() );
    my $stmS = "SELECT ID, PID, (select NAME from CAT WHERE ID_CAT = CAT.ID) as CAT, DATE, LOG from VW_LOG WHERE";       
    my $stmE = " ORDER BY DATE DESC, ID DESC;";  
    if($opr == 2){
       $stmS = "SELECT $SQLID as ID, ID_CAT as IDCAT, DATE, LOG, AMOUNT from LOG WHERE";
       $stmE = " ORDER BY date(DATE);";
    }

    #Get ids and build confirm table and check
    my $stm = $stmS ." ";
    my @chks= $cgi->param('chk');
    foreach my $id (@chks){
        if($opr == 2){
            $stm = $stm . "$SQLID = " . $id . " OR ";
        }
        else{
            $stm = $stm . "PID = " . $id . " OR ";
        }
    }
    $stm =~ s/ OR $//; $stm .= $stmE;
    my $st = Settings::selectRecords($db, $stm);

                 
    if($opr == 0){        
        printHeader('Confirm Deletion'); 
        print $cgi->pre("###ConfirmForDeletionPage()->[stm:$stm]\n]opr:$opr]") if($DEBUG);

        my $r_cnt = 0;
        my $rs = "r1";

         my $tbl = '<a name="top"></a><form name="frm_log_del" action="data.cgi" onSubmit="return formDelValidation();">
           <table class="tbl_rem" width="'.$PRC_WIDTH.'%">
           <tr class="hdr" style="text-align:left;">
               <th>Date <a href="#bottom">&#x21A1;</a></th> <th>Time</th> <th>Log</th> <th>Category <a href="#bottom">&#x21A1;</a></th></tr>';


        while(my @row = $st->fetchrow_array()) {

            my $ct = $row[2];
            my $dt = DateTime::Format::SQLite->parse_datetime( $row[3] );
            my $log = log2html($row[4]);

            $tbl .= '<tr class="r1"><td class="'.$rs.'">'. $dt->ymd . "</td>" .
                '<td class="'.$rs.'">' . $dt->hms . "</td>" .
                '<td class="'.$rs.'" style="font-weight:bold; color:maroon;">
                    <div class="log" style="overflow-x:none; max-width:600">'."$log</div></td>\n".
                '<td class="'.$rs.'">' . $ct. '<input type="hidden" name="chk" value="'.$row[0].'"></td></tr>';
            if($rs eq "r1"){
               $rs = "r0";
            }
            else{
                $rs = "r1";
            }
            $r_cnt++;
        }
  
        $tbl .= '<tr class="r0"><td colspan="4"><a name="bottom"></a><a href="#top">&#x219F;</a>
        <center>
            <h3>Please Confirm You Want<br>The Above Record'.($r_cnt>1?'s':'').' Deleted?</h3><br>
           <button onclick="return backToMain()">No Go Back</button>
        </center>
        </td></tr>
        <tr class="r0"><td colspan="4"><center>
        <input type="submit" value="I AM CONFIRMING!">
        </center>        
        </td></tr>
        </table><input type="hidden" name="confirmed" value="1"></form>';

        print qq(<div style="marging:5px;padding:10px;">$tbl</div>);

        print $cgi->end_html();
    } 
    elsif($opr == 2){        
        my $csv = Text::CSV-> new ( { binary => 1, escape_char => "\\", strict => 1, eol => $/ } );           
        my @columns = ("ID", "CAT", "DATE", "LOG", "AMOUNT");        
        print $cgi->header(-charset=>"UTF-8", -type=>"application/octet-stream", -attachment=>Settings::dbName()."_sel.csv");        
        print $csv->print(*STDOUT, \@columns);
        while (my $row=$st->fetchrow_arrayref()){
            #    $row[3] =~ s/\\\\n/\n/gs;
            my $out = $csv->print(*STDOUT, $row);                  
                print $out if(length $out>1);
        }
        exit;
    }else{        
        LifeLogException->throw(error => "Invalid Operation \$opr => $opr", show_trace=>1)
    }
    $st->finish();   
}catch($e){
    errorPage($e,'ConfirmForDeletionPage')
}
}


sub DeletionConfirmed {
    try{    
        my $SQLID = 'rowid'; $SQLID = 'ID' if Settings::isProgressDB();
        my $st1 = $db->prepare("DELETE FROM LOG WHERE $SQLID = ?;");
        my $st2 = $db->prepare("DELETE FROM NOTES WHERE LID = ?;");
        #print $cgi->header(-expires=>"+6os");
        foreach my $id ($cgi->param('chk')){
            my $st = Settings::selectRecords($db, 'select RTF from LOG where '.$SQLID.'='.$id);
            my @ra = $st->fetchrow_array();
            $st1->execute($id) or die "<p>Error->$_</p>";        
            $st2->execute($id) if $ra[0];
        }
    #2021-08-11 Added just in case next an renumeration. 
    # Above also checks now, if a log has flagged having an RTF before deleting the note entry.
    Settings::renumerate($db);
    print $cgi->redirect('main.cgi');  

    }catch($e){
        errorPage ($e, 'DeletionConfirmed');
    }
}

sub errorPage{
my  ($err, $sub) = @_;
printHeader("ERROR");
print "<font color=red><h2>".ref($err)." Encountered!</h2><br></font><p>Building  $sub Failed! </p><pre><b>Error:</b> ".$err."</pre>";
print $cgi->end_html()
}


use Text::Wrap; $Text::Wrap::columns=80; $Text::Wrap::separator="\n"; 

sub log2html {
    my $log = shift;
    my ($re_a_tag, $sub)  = qr/<a\s+.*?>.*<\/a>/si;
    $log = wrap('','',$log);
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
        given (&Settings::frameSize) {
            when("0") { $b = q(width="390" height="215") }
            when("1") { $b = q(width="280" height="180") }
            when("2") { $b = q(width="160" height="120") }
            default {
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

return $log;
}


sub PrintView {

try{    
    my $SQLID = 'rowid'; $SQLID = 'ID' if( Settings::isProgressDB() );
    my $stmS = "SELECT ID, PID, (select NAME from CAT WHERE ID_CAT = CAT.ID) as CAT, DATE, LOG, AMOUNT from VW_LOG WHERE";       
    my $stmE = " ORDER BY DATE DESC, ID DESC;";  

    #Get ids and build confirm table and check
    my $stm = " "; my @chks= $cgi->param('chk');
    foreach my $id (@chks){
        if($opr == 2){
            $stm = $stm . "$SQLID = " . $id . " OR ";
        }
        else{
            $stm = $stm . "PID = " . $id . " OR ";
        }
    }
    $stm =~ s/ OR $//; 
    my $sql = $stmS.$stm.$stmE;
    print $cgi->header(-expires=>"+6os");
    print $cgi->start_html(-title => "LifeLog Excerpt ".Settings::dbFile()." - ".$today->strftime('%d/%m/%Y %H:%M'),
            -style =>  {-type => 'text/css', -src => "wsrc/print.css"}
    );
    print $cgi->pre("###PrintView()->[sql:$sql]") if($DEBUG);

    my $st = Settings::selectRecords($db, "SELECT sum(AMOUNT) FROM VW_LOG WHERE $stm;");
    my $hasAmmounts = 0; while(my @r = $st->fetchrow_array()) {if($r[0]>0){$hasAmmounts = 1}}             
    

    my ($tot,$assets,$th_amt) = (0,0,''); $th_amt = '<th style="text-align:center;">'.Settings::currenySymbol().'</th>' if $hasAmmounts;
    my $tbl = qq(<table class="tbl_print" border="0" width="'.$PRC_WIDTH.'%">
        <tr class="hdr"><th>Date</th><th>Time</th><th>Log</th>
       </th>$th_amt<th>Category</th></tr>);
                    $st = Settings::selectRecords($db, $sql);
    while(my @row = $st->fetchrow_array()) {
        my $ct = $row[2];
        my $dt = DateTime::Format::SQLite->parse_datetime( $row[3] );
        my $log = log2html($row[4]);
        my $amt = $row[5];
        if($hasAmmounts){
            if($ct eq 'Expense'){
                $tot = $tot - $amt; $amt = "-$amt";
            }elsif($ct eq 'Income'){
                $tot += $amt;
            }else{
                $assets += $amt;
            }
            $amt="<td style='text-align:right;'>".cam($amt).'</td>';
        }else{$amt=""}

        $tbl .= '<tr><td class="ctr">'. $dt->ymd . "</td>" .
            '<td class="ctr">' . $dt->hms . "</td>" . qq(<td>$log</td>$amt<td class="cat">$ct</td></tr>);
    }
    $tot =  Settings::currenySymbol().cam($tot);
    if ($assets){$assets =  'Assets: '.Settings::currenySymbol().cam($assets)}else{$assets=""}
    if($hasAmmounts || $assets){
       $tbl .= qq(<tr><td colspan="6"></td></tr><tr>
                      <td></td><td></td><td style='text-align:right;'>$assets&nbsp;<b>Total:</b></td><td>$tot</td>
                      <td></td></tr>);
       $tbl .= '</table>';
    }
    
    print "<center><div>\n$tbl\n</div></center>";
    
}catch($e){
    errorPage($e,'ConfirmForDeletionPage')    
}
print $cgi->end_html();
}
sub cam {
    my $am = sprintf( "%.2f", shift);
    # Add one comma each time through the do-nothing loop
    1 while $am =~ s/^(-?\d+)(\d\d\d)/$1,$2/;
    return $am;
}

1;