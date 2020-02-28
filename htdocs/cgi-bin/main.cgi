#!/usr/bin/perl
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
use warnings;
use strict;
use Exception::Class ('LifeLogException');
use Syntax::Keyword::Try;
use Switch;

use CGI;
use CGI::Session '-ip_match';
use CGI::Carp qw ( fatalsToBrowser );
use DBI;

use DateTime;
use DateTime::Format::SQLite;
use DateTime::Duration;
use Date::Language;
use Date::Parse;
use Time::localtime;

use Regexp::Common qw /URI/;

#DEFAULT SETTINGS HERE!
use lib "system/modules";
require Settings;

my $cgi = CGI->new;
my $sss = new CGI::Session( "driver:File", $cgi, { Directory => &Settings::logPath } );
my $sid      = $sss->id();
my $dbname   = $sss->param('database');
my $userid   = $sss->param('alias');
my $password = $sss->param('passw');
my $sssCDB   = $sss->param('cdb');
my $vmode;

if ( !$userid || !$dbname ) {
    print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
    exit;
}

my $database = &Settings::logPath . $dbname;
my $dsn      = "DBI:SQLite:dbname=$database";
my $db       = DBI->connect( $dsn, $userid, $password, { PrintError => 0, RaiseError => 1 } )
                      or LifeLogException->throw("Connection failed [$DBI::errstri]");
my ( $imgw, $imgh );
#Fetch settings
 Settings::getConfiguration($db);
 Settings::getTheme();
### Authenticate sss to alias password
    &authenticate;
#
my $log_rc      = 0;
my $log_rc_prev = 0;
my $log_cur_id  = 0;
my $log_top     = 0;
my $rs_keys     = $cgi->param('keywords');
my $rs_cat_idx  = $cgi->param('category');
my $prm_vc      = $cgi->param("vc");
my $prm_xc      = $cgi->param("xc");
my $prm_xc_lst  = $cgi->param("idx_cat_x");
my $rs_dat_from = $cgi->param('v_from');
my $rs_dat_to   = $cgi->param('v_to');
my $rs_prev     = $cgi->param('rs_prev');
my $rs_cur      = $cgi->param('rs_cur');
my $rs_page     = $cgi->param('rs_page');
my $stmS        = 'SELECT PID, ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY from VW_LOG WHERE';
my $stmE        = "";
my $stmD        = "";
my $sm_reset_all;
my $rec_limit   = &Settings::recordLimit;
### Page specific settings Here
my $TH_CSS      = &Settings::css;
my $BGCOL       = &Settings::bgcol;
#Set to 1 to get debug help. Switch off with 0.
my $DEBUG       = &Settings::debug;
#END OF SETTINGS



my $lang  = Date::Language->new(Settings::language());
my $today = DateTime->now;
   $today -> set_time_zone(Settings::timezone());

#Excludes can be now be set as permanent to page view excluded, visible if view searched.
#http://localhost:8080/cgi-bin/main.cgi?vc=0&category=0&xc=0&idx_cat_x=0&v_from=&v_to=&keywords=&srch_reset=0

if(!$prm_vc && &Settings::keepExcludes){
    if($prm_xc_lst){
        &Settings::configProperty($db, 201, '^EXCLUDES', $prm_xc_lst);
    }
    else{
       $prm_xc_lst = &Settings::obtainProperty($db, '^EXCLUDES');
       $prm_xc = $prm_xc_lst if (!$prm_xc && !$cgi->param('srch_reset'));
    }
}
elsif(!$prm_xc && $prm_xc_lst){
#view call only
    $prm_xc = $prm_xc_lst;
}

if ( !$rs_dat_to && $rs_dat_from ) {
    my $dur = $today;
    $dur->add( months => 1 );
    $rs_dat_to = DateTime::Format::SQLite->parse_datetime($dur);
}

if ( $rs_dat_from && $rs_dat_to ) {
    $stmD = qq( DATE BETWEEN date('$rs_dat_from') AND date('$rs_dat_to') );
}

#Toggle if search deployed.
my $toggle = "";
if ( $rs_keys || $rs_cat_idx || $stmD || $prm_vc > 0 || $prm_xc > 0) { $toggle = 1; }


##Handle Session Keeps
$sss->expire(&Settings::sessionExprs);
$sss->param('theme', $TH_CSS);
$sss->param('bgcolor', $BGCOL);
$sss->param('sss_main', $today);
#

#Reset Clicked
if($cgi->param('srch_reset') == 1){
   $sss->clear('sss_vc');
   $sss->clear('sss_xc');
}

if($prm_vc){
   if ($cgi->param('sss_xc') eq 'on'){
       $sss->param('sss_vc', $prm_vc)
   }
   else{
        $sss->clear('sss_vc');
   }
}else{
       $prm_vc = $sss->param('sss_vc');
}
if($prm_xc){
   if ($cgi->param('sss_xc') eq 'on'){
       $sss->param('sss_xc', $prm_xc)
   }
   else{
        $sss->clear('sss_xc');
   }
}else{
       $prm_xc = $sss->param('sss_xc');
}



#TODO (2020-02-23) It gets too complicated. should not have both $prm_xc and $prm_xc_lst;
       if(!$prm_xc_lst && index($prm_xc, ',') > 0){
           $prm_xc_lst =  $prm_xc;
       }
##
my @xc_lst = split /\,/, $prm_xc_lst;


$sss->flush();

#tag related framed sizing.
my @arrwh = split /x/, &Settings::imgWidthHeight;
if ( @arrwh == 2 ) {
    $imgw = $arrwh[0];
    $imgh = $arrwh[1];
}
else {    #defaults
    $imgw = 210;
    $imgh = 120;
}

print $cgi->header(-expires => "0s", -charset => "UTF-8");
print $cgi->start_html(
    -title   => "Personal Log",
    -BGCOLOR => $BGCOL,
    -onload  => "onBodyLoad('$toggle','".Settings::timezone()."','$today','".&Settings::sessionExprs."',$rs_cur);",
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

        { -type => 'text/css', -src => 'wsrc/quill/katex.min.css' },
        { -type => 'text/css', -src => 'wsrc/quill/monokai-sublime.min.css' },
        { -type => 'text/css', -src => 'wsrc/quill/quill.snow.css' },
        { -type => 'text/css', -src => 'wsrc/jquery.sweet-dropdown.css' },

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
        { -type => 'text/javascript', -src => 'wsrc/jquery.poshytip.js' },

        { -type => 'text/javascript', -src => 'wsrc/quill/katex.min.js' },
        { -type => 'text/javascript', -src => 'wsrc/quill/highlight.min.js' },
        { -type => 'text/javascript', -src => 'wsrc/quill/quill.min.js' },
        { -type => 'text/javascript', -src => 'wsrc/jscolor.js' },
        { -type => 'text/javascript', -src => 'wsrc/moment.js' },
        { -type => 'text/javascript', -src => 'wsrc/moment-timezone-with-data.js' },
        { -type => 'text/javascript', -src => 'wsrc/jquery.sweet-dropdown.js'}

    ],
);


my $st;
my $sqlCAT = "SELECT ID, NAME, DESCRIPTION FROM CAT ORDER BY ID;";
my $sqlVWL = "SELECT ID, ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY FROM VW_LOG WHERE STICKY = 1 LIMIT ".&Settings::viewAllLimit.";";

print qq(## Using db -> $dsn\n) if $DEBUG;

$st = $db->prepare($sqlCAT);
$st->execute() or LifeLogException->throw($DBI::errstri);

my %hshCats;
my %hshDesc = {};
my $c_sel   = 1;
my $data_cats = "";
my $td_cat = "<tr><td><ul>";
my $td_itm_cnt =0;
while ( my @row = $st->fetchrow_array() ) {
    my $n = $row[1];
    $n =~ s/\s*$//g;
    $hshCats{$row[0]} = $n;
    $hshDesc{$row[0]} = $row[2];
    if($td_itm_cnt>4){
        $td_cat .= "</ul></td><td><ul>";
        $td_itm_cnt = 0;
    }
    $td_cat .= "<li id='$row[0]'><a href='#'>$row[1]</a></li>";
    $td_itm_cnt++;

}
if($td_itm_cnt<5){#fill spacing.
    for (my $i=0;$i<5-$td_itm_cnt;$i++){
        $td_cat .= "<li><a href='#'></a>&nbsp;</li>";
    }
}
$td_cat .= "</ul></td></tr>";


for my $key ( keys %hshDesc ) {
    my $kv = $hshDesc{$key};
    if ( $kv ne ".." && index($key,'HASH(0x')!=0) {
        my $n = $hshCats{$key};
        $data_cats .= qq(<meta id="cats[$key]" name="$n" content="$kv">\n);
    }
}
my $log_output =
qq(<form id="frm_log" action="data.cgi" onSubmit="return formDelValidation();">
<TABLE class="tbl" border="0" width=").&Settings::pagePrcWidth.qq(%">
<tr class="r0">
	<th>Date</th>
	<th>Time</th>
	<th>Log</th><th>#</th>
	<th>Category</th>
    <th>Edit</th>
</tr>);

    if ( defined $prm_vc ) {    #view category form selection
        $rs_cat_idx = $prm_vc;
    }

    if ( $rs_keys && $rs_keys ne '*' ) {

        my @keywords = split / /, $rs_keys;
        if ($rs_cat_idx && $rs_cat_idx != $prm_xc) {
            $stmS .= " ID_CAT='" . $rs_cat_idx . "' AND";
        }
        else {
            if($prm_xc>0){
                if(@xc_lst){
                    foreach (@xc_lst){
                            $stmS .= " ID_CAT!=$_ AND";
                    }
                }
                else{       $stmS .= " ID_CAT!=$prm_xc AND"; }
            }
        }
        if ($stmD) {
            $stmS = $stmS . $stmD . " AND";
        }

        if (@keywords) {
            foreach (@keywords) {
                $stmS = $stmS . " LOWER(LOG) REGEXP '\\b" . lc $_ . "\\b'";
                if ( \$_ != \$keywords[-1] ) {
                    $stmS = $stmS . " OR ";
                }
            }
            $sqlVWL = $stmS . $stmE;
        }
    }
    elsif ($rs_cat_idx && $rs_cat_idx != $prm_xc) {

        if ($stmD) {
            $sqlVWL = $stmS . $stmD . " AND ID_CAT='" . $rs_cat_idx . "'" . $stmE;
        }
        else {
            $sqlVWL = $stmS . " ID_CAT=" . $rs_cat_idx . ";" . $stmE;
        }
    }
    else {
        if($prm_xc>0){

                if(@xc_lst){
                    my $ands = "";
                    foreach (@xc_lst){
                            $ands .= " ID_CAT!=$_ AND";
                    }
                    $ands =~ s/AND$//g;
                    $sqlVWL = $stmS . $ands . $stmE;
                }
                else{
                    $sqlVWL = $stmS . " ID_CAT!=$prm_xc;" . $stmE;
                }



        }
        if ($stmD) {
            $sqlVWL = $stmS . $stmD . $stmE;
        }
    }

    ###################
      &processSubmit;
    ###################

    my $tfId      = 0;
    my $id        = 0;
    my $log_start = index $sqlVWL, "<=";
    my $re_a_tag  = qr/<a\s+.*?>.*<\/a>/si;
    my $isView = rindex ($sqlVWL, 'PID<=') > 0 || rindex ($sqlVWL, 'ID_CAT=') > 0;

    print $cgi->pre("###[Session PARAMS->isV:$isView|vc=$prm_vc|xc=$prm_xc|xc_lst=$prm_xc_lst|xc_lst=@xc_lst|keepExcludes=".&Settings::keepExcludes."] -> ".$sqlVWL) if $DEBUG;

    if ( $log_start > 0 ) {

        #check if we are at the beggining of the LOG table?
        my $stc = traceDBExe('SELECT PID from VW_LOG LIMIT 1;');
        my @row = $stc->fetchrow_array();
            $log_top = $row[0];
        if ($log_top == $rs_prev && $rs_cur == $rs_prev ) {
            $log_start = -1;
        }
        $stc->finish();
    }
    #
    #Fetch entries!
    #
    my $CID_EVENT = 9;
    my $tags      = "";
    my $sum       = 0;
    my $exp       = 0;
    my $ass       = 0;


    #place sticky or view param.ed entries first!
    buildLog(traceDBExe($sqlVWL));
    #Following is saying is in page selection, not view selection, or accounting on type of sticky entries.
    if( !$isView && !$prm_vc  && !$prm_xc && !$rs_keys && !$rs_dat_from ){
        $sqlVWL = "SELECT ID, ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY FROM VW_LOG WHERE STICKY != 1  ORDER BY DATE DESC LIMIT ".&Settings::viewAllLimit.";";
        print $cgi->pre("###2 -> ".$sqlVWL)  if $DEBUG;
        ;
        &buildLog(traceDBExe($sqlVWL));
    }


sub traceDBExe {
    my $sql = shift;
    try{
        my $st = $db->prepare($sql);
           $st -> execute() or LifeLogException->throw("Execute failed [$DBI::errstri]", show_trace=>1);
        return $st;
    }catch{
                LifeLogException->throw(error=>"database error encountered.", show_trace=>1);
    }
}

sub buildLog {
    my $pst = shift;
    #print "## sqlVWL: $sqlVWL\n";
    while ( my @row = $pst->fetchrow_array() ) {
        my $i = 0;
        $id = $row[$i++]; #ID must be rowid in LOG.
        my $cid = $row[$i++]; #CID ID_CAT not used.
        my $ct  = $hshCats{$cid}; #ID_CAT
        my $rtf = $row[$i++];           #ID_RTF since v.1.8
        my $dt  = DateTime::Format::SQLite->parse_datetime( $row[$i++] ); #LOG.DATE
        my $log = $row[$i++]; #LOG.LOG
        my $am  = $row[$i++]; #LOG.AMOUNT
        my $af  = $row[$i++]; #AFLAG -> Asset as 0, Income as 1, Expense as 2
        my $sticky = $row[$i++]; #Sticky to top

        if ( $af == 1 ) { #AFLAG Income
            $sum += $am;
        }
        elsif ( $af == 2 ) {
            $exp -= $am;
        }
        else{
            $ass += $am;
        }
        $am =  &cam($am);
        #Apostrophe in the log value is doubled to avoid SQL errors.
        $log =~ s/''/'/g;
        #
        if ( !$ct ) {
            $ct = $hshCats{1};
        }
        if ( !$dt ) {
            $dt = $today;
        }
        if ( !$am ) {
            $am = "0.00";
        }
        if ( $log_rc_prev == 0 ) {
            $log_rc_prev = $id;
        }
        if ( $tfId > 0) {
            $tfId = 0;
        }
        else {
            $tfId = 1;
        }

        my $sub      = "";
        my $tagged   = 0;
        my $log_orig = $log;

#Check for LNK takes precedence here as we also parse plain placed URL's for http protocol later.
        if ( $log =~ /<<LNK</ ) {
            my $idx = $-[0] + 5;
            my $len = index( $log, '>', $idx );
            $sub = substr( $log, $idx + 1, $len - $idx - 1 );
            my $url = qq(<a href="$sub" target=_blank>$sub</a>);
            $tagged = 1;
            $log =~ s/<<LNK<(.*?)>+/$url/osi;
        }

        if ( $log =~ /<<IMG</ ) {
            my $idx = $-[0] + 5;
            my $len = index( $log, '>', $idx );
            $sub = substr( $log, $idx + 1, $len - $idx - 1 );
            my $url = qq(<img src="$sub"/>);
            $tagged = 1;
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
                $lnk =qq(\n<img src="$lnk" width="$imgw" height="$imgh" class="tag_FRM"/>);
            }
            $log =~ s/<<FRM<(.*?)>+/$lnk/o;
            $tagged = 1;
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
            $tagged = 1;
        }
        else {
            my @chnks = split( /($re_a_tag)/si, $log );
            foreach my $ch_i (@chnks) {
                next if $ch_i =~ /$re_a_tag/;
                next if index( $ch_i, "<img" ) > -1;
                $ch_i =~ s/https/http/gsi;
                $ch_i =~
                  s/($RE{URI}{HTTP})/<a href="$1" target=_blank>$1<\/a>/gsi;
            }
            $log = join( '', @chnks );
        }

        while ( $log =~ /<<B</ ) {
            my $idx = $-[0];
            my $len = index( $log, '>', $idx ) - 4;
            my $sub = "<b>" . substr( $log, $idx + 4, $len - $idx ) . "</b>";
            $log =~ s/<<B<(.*?)>+/$sub/o;
            $tagged = 1;
        }
        while ( $log =~ /<<I</ ) {
            my $idx = $-[0];
            my $len = index( $log, '>', $idx ) - 4;
            last if $len<6;
            my $sub = "<i>" . substr( $log, $idx + 4, $len - $idx ) . "</i>";
            $log =~ s/<<I<(.*?)>+/$sub/o;
            $tagged = 1;
        }
        while ( $log =~ /<<TITLE</ ) {
            my $idx = $-[0];
            my $len = index( $log, '>', $idx ) - 8;
            last if $len<9;
            my $sub = "<h3>" . substr( $log, $idx + 8, $len - $idx ) . "</h3>";
            $log =~ s/<<TITLE<(.*?)>+/$sub/o;
            $tagged = 1;
        }

        while ( $log =~ /<<LIST</ ) {
            my $idx = $-[0];
            my $len = index( $log, '>', $idx ) - 7;
            last if $len<9;
            my $lst = substr( $log, $idx + 7, $len - $idx );
            my $sub = "";
            my @arr = split( /\n|\\n/, $lst );
            my $ml  = "";
            foreach my $ln (@arr) {
                $ln =~ s/^\s*//g;
                if ( $ln =~ /~$/ ) {
                    $ln =~ s/~$/<br>/g;
                    $ml .= $ln . ' ';
                }
                else {
                    if ($ml) {
                        $ml  .= $ln if length($ln) > 0;
                        $sub .= "<li>$ml</li>\n";
                        $ml = "";
                    }
                    else {
                        $sub .= "<li>$ln</li>" if length($ln) > 0;
                    }
                }
            }

            $sub = "<div id='rz'><ul>$sub</ul></div>";
            $log =~ s/<<LIST<(\w*|\s*)*.*(>+?)/$sub/o;
            $tagged = 1;
        }

        #Decode escaped \\n
        $log =~ s/\r\n/<br>/gs;
        $log =~ s/\\n/<br>/gs;

        if ( $CID_EVENT == $row[1] ) {
            $log = "<font color='#eb4848' style='font-weight:bold'>$log</font>";
            $tagged = 1;
        }
        elsif ( 1 == $row[1] ) {
            $log =
"<font class='midnight' style='font-weight:bold;font-style:italic'>$log</font>";
            $tagged = 1;
        }

        #Tagged preserve originally stored entry in hidden numbered field.
        if ($tagged) {
            $log_orig =~ s/</&#60;/g;
            $log_orig =~ s/>/&#62;/g;
            $log_orig =~ s/\n/&#10;/g;
            $log_orig =~ s/\\n/&#10;/g;
            $log_orig =~ s/\t/&#9;/g;
            $log_orig =~ s/\"/&#34;/g;
            $log_orig =~ s/\'/&#39;/g;
            $tags .= qq(<input type="hidden" id="g$id" value="$log_orig"/>\n);
        }

        my ( $dty, $dtf ) = $dt->ymd;
        my $dth = $dt->hms;
        $dth .= " id=($id)" if $DEBUG;
        if ( &Settings::universalDate == 1 ) {
            $dtf = $dty;
        }
        else {
            $dtf = $lang->time2str( "%d %b %Y", $dt->epoch, &Settings::timezone);
        }

        if ( $rtf > 0 ) {
            $log .= qq(<hr><button id="btnRTF" onClick="return loadRTF(true, $id);">RTF</button>);
        }

        if($af==2){
           $am = qq(<font color="maroon">$am</font>);
        }

        my $ssymb = "Edit";
        my $ssid  = $tfId;
        if ($sticky){
            $ssymb = "Edit &#10037;";
            $ssid = $tfId + 2;
        }

        $log_output .= qq(<tr class="r$ssid">
		<td width="15%">$dtf<input id="y$id" type="hidden" value="$dty"/></td>
		<td id="t$id" width="10%" class="tbl">$dth</td>
		<td id="v$id" class="log" width="40%">$log</td>
		<td id="a$id" width="10%" class="tbl">$am</td>
		<td id="c$id" width="10%" class="tbl">$ct</td>
		<td width="20%">
        <input id="r$id" type="hidden" value="$rtf"/>
        <input id="s$id" type="hidden" value="$sticky"/>
        <input id="f$id" type="hidden" value="$af"/>
			<button class="edit" value="Edit" onclick="return edit($id);">$ssymb</button>
			<input name="chk" type="checkbox" value="$id"/>
		</td></tr>);

        if ( $rtf > 0 ) {
             $log_output .= qq(<tr id="q-rtf$id" class="r$tfId" style="display:none;">
                         <td colspan="6">
                          <div id="q-scroll$id" style="height:auto; max-height:480px; padding: 10px; background:#fffafa; overflow-y: auto;">
                            <div id="q-container$id"></div>
                          </div>
                        </td></tr>);
        }

        $log_rc += 1;

        if ( $rec_limit > 0 && $log_rc == $rec_limit ) {
            last;
        }

    }    #while end
}#buildLog

    if   ( $tfId == 1 ) { $tfId = 0; }
    else                { $tfId = 1; }
    my ($tot,$tas);
    $tot = $sum - $exp;
    $sum = &cam($sum);
    $exp = &cam($exp);
    $tas = &cam($ass);
    $tot = &cam($tot);

    $log_output .= qq(
    <tr class="r$tfId">
		<td></td>
		<td></td>
		<td id="summary" colspan="4" style="text-align:right"># <i>Totals</i>: Assets[$tas] Gross[<b><i>$tot</i></b> &lt;-- $sum (<font color="red">$exp</font>)]</td>
	</tr>);

    ###
    &buildNavigationButtons;
    ###

    ##
    #Fetch Keywords autocomplete we go by words larger then three.
    #
    my $aw_cnt    = 0;
    my $autowords = qq("gas","money","today");

    &fetchAutocomplete;

    if ( $log_rc == 0 ) {

        if ($stmD) {
            $log_output .= qq(<tr><td colspan="5">
			<b>Search Failed to Retrive any records on select: [<i>$stmD</i>] !</b></td></tr>');
        }
        elsif ($rs_keys) {
            my $criter = "";
            if ( $rs_cat_idx > 0 ) {
                $criter = "->Criteria[" . $hshCats{$rs_cat_idx} . "]";
            }
            $log_output .= qq(<tr><td colspan="5">
			<b>Search Failed to Retrive any records on keywords: [<i>$rs_keys</i>]$criter!</b></td></tr>);
        }
        else {
            if (&isInViewMode) { $log_output .= '<tr><td colspan="5"><b>You have reached the end of the data view!</b></td></tr>' }
            else{ $log_output .= '<tr><td colspan="5"><b>Database is New or  Empty!</b></td></tr>'}
        }
    }

    $log_output .= <<_TXT;
<tr class="r0"><td colspan="2">Show All hidden with &#10132;
<a id="menu_close" href="#" onclick="return showAll();"><span  class="ui-icon ui-icon-heart" style="float:none;></span></a>

<a href="#top">&#x219F;</a></td>
<td colspan="4" align="right">
    <input type="hidden" name="datediff" id="datediff" value="0"/>
    <input type="submit" value="Sum Selected" onclick="return sumSelected()"/>&nbsp;
    <input type="submit" value="Date Diff Selected" onclick="return dateDiffSelected()"/>&nbsp;
    <button onclick="return selectAllLogs()">Select All</button>
    <input type="reset" value="Unselect All"/>
    <input id="del_sel" type="submit" value="Delete Selected"/>
</td></tr>
</form>
<form id="frm_srch" action="main.cgi">
    <tr class="r0"><td><b>Keywords:</b></td><td colspan="4" align="left">
    <input id="rs_keys2" name="keywords" type="text" size="60"/></td>
    <td><input type="submit" value="Search"/></td></tr>
</form>
</TABLE>
_TXT

    my ( $sp1, $sp2, $sp3 );
    $sp1 = '<span  class="ui-icon ui-icon-heart"></span>';
    $sp2 = '<span  class="ui-icon ui-icon-circle-triangle-s"></span>';
    $sp3 = '<span  class="ui-icon ui-icon-arrow-4-diag"></span>';

    my $frm = qq(<a name="top"></a>
<form id="frm_entry" action="main.cgi" onSubmit="return formValidation();">
	<table class="tbl" border="0" width=").&Settings::pagePrcWidth.qq(%">
	<tr class="r0"><td colspan="3"><b>* LOG ENTRY FORM *</b>
    <a id="log_close" href="#" onclick="return hide('#div_log');">$sp1</a>
    <a id="log_close" href="#" onclick="return toggle('#div_log .collpsd');">$sp2</a>
    </td></tr>
	<tr class="collpsd">
	<td style="text-align:right; vertical-align:top; width:10%;">Date:</td>
	<td id="al" colspan="1" style="text-align:top; vertical-align:top"><input id="ed" type="text" name="date" size="18" value=")
      . $today->ymd . " " . $today->hms . qq(">

	&nbsp;<button type="button" onclick="return setNow();">Now</button>
			&nbsp;<button type="reset"  onclick="setNow();resetDoc(); return true;">Reset</button>


                <span id="cat_desc" name="cat_desc">Enter log...</span>

            </td>
			<td style="text-align:top; vertical-align:top">Category:&nbsp;
            <span id="lcat" class="span_cat"><i><font size=1>--Select --</font></i></span>
                <button class="bordered" data-dropdown="#dropdown-standard">&#171;</button>

            <div class="dropdown-menu dropdown-anchor-top-right dropdown-has-anchor" id="dropdown-standard">
                        <table class="tbl">$td_cat</table>
            </div>
<!-- OLD -> \$cats was here -->
			</td>
	</tr>
	<tr class="collpsd"><td style="text-align:right; vertical-align:top">Log:</td>
		<td id="al" colspan="2" style="text-align:top;">
			<textarea id="el" name="log" rows="3" style="float:left; width:99%;" onChange="toggleVisibility('cat_desc',true)"></textarea>
		</td>
	</tr>
	<tr class="collpsd"><td style="text-align:right"><a id="to_bottom" href="#bottom" title="Go to bottom of page.">&#x21A1;</a>&nbsp;Amount:</td>
		<td id="al">
			<input id="am" name="am" type="text">&nbsp;
            Marks as:
            <select id="amf" name="amf">
                <option value="0" selected>Asset</option>
                <option value="1">Income</option>
                <option value="2">Expense</option>
            </select>&nbsp;
            <input id="RTF" name="rtf" type="checkbox" onclick="return toggleDoc(true);"/> RTF Document
            <input id="STICKY" name="sticky" type="checkbox"/> Sticky
		</td>
		<td align="right">
                <span id="sss_status"></span>&nbsp;
				<input id="log_submit" type="submit" onclick="return saveRTF(-1, 'store');" value="Submit"/></div>
		</td>
	</tr>
	<tr class="collpsd"><td colspan="3"></td></tr>
	</table>
    <input type="hidden" name="ec" id="ec" value="0"/>
	<input type="hidden" name="submit_is_edit" id="submit_is_edit" value="0"/>
	<input type="hidden" name="submit_is_view" id="submit_is_view" value="0"/>
	<input type="hidden" name="rs_all" value="0"/>
	<input type="hidden" name="rs_cur" value="0"/>
	<input type="hidden" name="rs_prev" value="$log_rc_prev"/>
	<input type="hidden" name="rs_page" value="$rs_page"/>
	<input type="hidden" name="CGISESSID" value="$sid"/>
	$tags
    </form>
	);

    my $srh = qq(
	<form id="frm_srch" action="main.cgi">
	<table class="tbl" border="0" width=").&Settings::pagePrcWidth.qq(%">
	  <tr class="r0">
        <td colspan="2"><b>Search/View By</b>
            <a id="srch_close" href="#" onclick="return hide('#div_srh');">$sp1</a>
            <a id="srch_close" href="#" onclick="return toggle('#div_srh .collpsd');">$sp2</a>
        </td>
      </tr>
    );
    my $sss_checked = 'checked' if &isInViewMode;
    my $divxc = '<td id="divxc_lbl" align="right" style="display:none"><b>Excludes:</b></td><td align="left" id="divxc"></td>';
    my ($catselected, $idx_cat) =  '<i><font size=1>-- Select --</font></i>', 0;
    if($rs_cat_idx){
        $catselected = $hshCats{$rs_cat_idx};
        $idx_cat = $rs_cat_idx;

    }
    if(@xc_lst){#Do list of excludes, past from browser in form of category id's.
        my $xcls ="";
        foreach(@xc_lst){ $xcls .= $hshCats{$_}.','}
        $xcls =~ s/\,$//g;
        $divxc = '<td id="divxc_lbl" align="right"><b>Excludes:</b></td><td align="left" id="divxc">'.$xcls.'</td>';
    }
    $srh .=
    qq(
    <tr class="collpsd">
     <td align="right"><b>View by Category:</b></td>
     <td align="left">

                 <span id="lcat_v" class="span_cat">$catselected</span>
                 <button class="bordered" data-dropdown="#dropdown-standard-v">&#171;</button>

            <div id="dropdown-standard-v" class="dropdown-menu        dropdown-anchor-left-center      dropdown-has-anchor">
                        <table class="tbl">$td_cat</table>
            </div>
     <!--
    \$cats_v&nbsp;&nbsp;   -->
        <button id="btn_cat" onclick="viewByCategory(this);">View</button>
        <input id="idx_cat" name="category" type="hidden" value="$idx_cat"/>
     </td>
   </tr>
   <tr class="collpsd">
     <td align="right"><b>Exclude Category:</b></td>
     <td align="left">


                 <span id="lcat_x" class="span_cat"><i><font size=1>--Select --</font></i></span>
                 <button class="bordered" data-dropdown="#dropdown-standard-x">&#171;</button>

            <div id="dropdown-standard-x" class="dropdown-menu        dropdown-anchor-left-center      dropdown-has-anchor">
                        <table class="tbl">$td_cat</table>
            </div>

     <!-- \$cats_x&nbsp;&nbsp;   -->
        <input id="idx_cat_x" name="idx_cat_x" type="hidden" value="0"/>

        <button id="btnxca" onClick="return addExclude()"/>Add</button>&nbsp;&nbsp;
        <button id="btnxrc" type="button" onClick="return removeExclude()">Remove</button>&nbsp;
        <button id="btnxrc" type="button" onClick="return resetExclude()">Reset</button>&nbsp;&nbsp;&nbsp;
        <button id="btn_cat" onclick="return viewExcludeCategory(this);">View</button>&nbsp;&nbsp;
        <input id="sss_xc" name="sss_xc" type="checkbox" $sss_checked/> Keep In Seession
     </td>
   </tr>
   <tr class="collpsd">$divxc</tr>
   <tr class="collpsd">
    <td align="right"><b>View by Date:</b></td>
	<td align="left">
        From:&nbsp;<input id="srh_date_from" name="v_from" type="text" size="16" value="$rs_dat_from"/>&nbsp;&nbsp;
        To:&nbsp;<input id="srh_date_to" name="v_to" type="text" size="16" value="$rs_dat_to"/>
        &nbsp;&nbsp;<button id="btn_dat" onclick="viewByDate(this);">View</button>
    </td>
	</tr>
   <tr class="collpsd">
    <td align="right"><b>Keywords:</b></td>
	<td align="left">
		<input id="rs_keys" name="keywords" type="text" size="60" value="$rs_keys"/>
		&nbsp;&nbsp;<input type="submit" value="Search" align="left">
    </td>
    );

    if ( ( $rs_keys && $rs_keys ne '*' ) || $rs_cat_idx || $stmD || $prm_xc ) {
        $sm_reset_all = '<a class="a_" onclick="resetView();">Reset View</a><hr>';
        $srh .= '<tr class="collpsd"><td align="right" colspan="2">
        <input id="srch_reset" name="srch_reset" type="hidden" value="0"/>
        <button onClick="resetView()">Reset Whole View</button><br></td></tr>';
    }
    else {$srh .= '</tr>'};

    $srh .= '</table></form>';
    my $quill = &quill( $cgi->param('submit_is_edit') );
    my $help = &help;

  ################################
 #   Page printout from here!   #
################################

print qq(
<div id="menu" title="To close this menu click on its heart, and wait.">
<div class="hdr" style="marging=0;padding:0px;">
<a id="to_top" href="#top" title="Go to top of page."><span class="ui-icon ui-icon-arrowthick-1-n" style="float:none;"></span></a>&nbsp;
<a id="to_bottom" href="#bottom" title="Go to bottom of page."><span class="ui-icon ui-icon-arrowthick-1-s" style="float:none;"></span></a>
<a id="menu_close" href="#" onclick="return hideLog();"><span class="ui-icon ui-icon-heart" style="float:none;"></span></a>
</div>
<hr>
<a class="a_" onclick="return toggle('#div_log',true);">Log</a><br>
<a href="#" title="TOP" onclick="return submitTop();" ><span class="ui-icon ui-icon-triangle-1-w" style="float:none;"></span></a>
<a href="#" title="PREVIOUS" onclick="return submitPrev($log_rc_prev, $rec_limit);"><span class="ui-icon ui-icon-arrowthick-1-w" style="float:none;"></span></a>
<a href="#" title="NEXT" onclick="return submitNext($log_cur_id, $rec_limit);"><span class="ui-icon ui-icon-arrowthick-1-e" style="float:none;"></span></a>
<a href="#" title="END" onclick="return submitEnd($rec_limit);"><span class="ui-icon ui-icon-triangle-1-e" style="float:none;"></span></a>
<hr>
<a class="a_" onclick="return toggle('#div_srh',true);">Search</a><hr>
<a class="a_" onclick="return deleteSelected();">Delete</a><hr>
<a class="a_" onclick="return toggle('#tbl_hlp',true);">Help</a><hr>
<a class="a_" href="stats.cgi">Stats</a><hr>
<a class="a_" href="config.cgi">Config</a><hr>
<a class="a_" id="lnk_show_all" onclick="return showAll();">Show All <span  class="ui-icon ui-icon-heart"></a><hr>
$sm_reset_all
<a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a><br>
<span style="font-size: x-small;">$vmode</span><br>
</div>
	  <div id="div_log">$frm</div>
	  <div id="div_srh">$srh</div>
      $quill
      <div id="div_hlp">$help</div>
	  <div>\n$log_output\n</div><br>
	  <div><a class="a_" href="stats.cgi">View Statistics</a></div><br>
	  <div><a class="a_" href="config.cgi">Configure Log</a></div><hr>
	  <div><a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a><hr><a name="bottom"/></div>
<!-- Cat Data Start-->
<span id="meta_cats">
	$data_cats
</span>
<!--Cat Data End->
<!-- Page Settings Specifics date:20200222 -->
<script type="text/javascript">
    \$( function() {
        var tags = [$autowords];
        \$( "#rs_keys, #rs_keys2" ).autocomplete({
            source: tags
            });
        });
</script>
);


print $cgi->end_html;
$st->finish;
$db->disconnect();
undef($sss);
exit;


# http://localhost:8080/cgi-bin/main.cgi?
# date=2020-02-27+11%3A05%3A28&
# log=new
# &am=
# &amf=0
# &ec=92


# &submit_is_edit=0&submit_is_view=0&rs_all=0&rs_cur=0&rs_prev=332


sub processSubmit {

        my $date = $cgi->param('date');
        my $log  = $cgi->param('log');
        my $cat  = $cgi->param('ec');
        my $cnt ="";
        my $am = $cgi->param('am');
        my $af = $cgi->param('amf');

        my $edit_mode = $cgi->param('submit_is_edit');
        my $view_mode = $cgi->param('submit_is_view');
        my $view_all  = $cgi->param('rs_all');
        my $rtf    = $cgi->param('rtf');
        my $sticky = $cgi->param('sticky');
        my $stm;

        ##TODO
        if($rtf eq 'on'){$rtf = 1}  else {$rtf = 0}
        if($sticky eq 'on'){$sticky = 1} else {$sticky = 0}
        if(!$am){$am=0}

try {
#Apostroph's need to be replaced with doubles  and white space to be fixed for the SQL.
            $log =~ s/'/''/g;

            if ( $edit_mode && $edit_mode != "0" ) {

                #Update
                $date = DateTime::Format::SQLite->parse_datetime($date);
                $stm = qq( UPDATE LOG SET ID_CAT='$cat', ID_RTF='$rtf',
                                             DATE='$date',
                                             LOG='$log',
                                             AMOUNT='$am',
                                             AFLAG = '$af',
                                             STICKY='$sticky' WHERE rowid="$edit_mode";
                    <br>);
                #
                print $stm if $DEBUG;
                #

                my $dbUpd = DBI->connect( $dsn, $userid, $password, { RaiseError => 1 } )  or LifeLogException->throw("Execute failed [$DBI::errstri]");
                traceDBExe($stm);
                return;
            }

            if ( $view_all && $view_all == "1" ) {
                $rec_limit = &Settings::viewAllLimit;
            }

            if ( $view_mode == "1" ) {

                if ($rs_cur) {
                    my $sand = "";
                    if ( $rs_cur == $rs_prev )
                    {    #Mid page back button if id ordinal.
                        $rs_cur += $rec_limit;
                        $rs_prev = $rs_cur;
                        $rs_page--;
                    }
                    else {
                        $rs_page++;
                    }

                    if($prm_vc){
                        $sand = "and ID_CAT == $prm_vc";
                    }
                    elsif($prm_xc){

                        if(@xc_lst){
                                foreach (@xc_lst){
                                        $sand .= "and ID_CAT!=$_ ";
                                }
                        }
                        else{ $sand = "and ID_CAT != $prm_xc"; }

                    }

                    $sqlVWL = qq(SELECT PID, ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY from VW_LOG where PID<=$rs_cur and STICKY!=1 $sand)." LIMIT ".&Settings::viewAllLimit.";";
                    return;
                }
            }

            if ( $log && $date && $cat ) {

                #check for double entry
                #
                $date = DateTime::Format::SQLite->parse_datetime($date);
                $stm = qq(SELECT DATE,LOG FROM LOG where DATE='$date' AND LOG='$log';);
                my $st = traceDBExe($stm);
                if ($st->fetchrow_array() ) {
                    return;
                }

                $stm = qq(INSERT INTO LOG (ID_CAT, ID_RTF, DATE, LOG, AMOUNT, AFLAG, STICKY) VALUES($cat, $rtf, '$date', '$log', $am, $af, $sticky););
                $st = traceDBExe($stm);
                if($sssCDB){
                    #Allow further new database creation, it is not an login infinite db creation attack.
                    $sss->param("cdb", 0);
                }
                if($rtf){ #Update 0 ground NOTES entry to the just inserted log.

                   $st = traceDBExe('SELECT ID FROM VW_LOG LIMIT 1;');
                   my @lid = $st->fetchrow_array();
                   $st = traceDBExe('SELECT DOC FROM NOTES WHERE LID = 0;');
                   my @gzero = $st->fetchrow_array();
                   if(scalar @lid > 0){
            #By Notes.LID constraint, there should NOT be an already existing log rowid entry just submitted in the Notes table!
            #What happened? We must check and delete, regardles. As data is renumerated and shuffled from perl in database. :(
                      $st = traceDBExe("SELECT LID FROM NOTES WHERE LID=".$lid[0].";");
                      if($st->fetchrow_array()){
                          $st = $db->do("DELETE FROM NOTES WHERE LID=".$lid[0].";");
                          print qq(<p>Warning deleted (possible old) NOTES.LID[$lid[0]] -> lid:@lid</p>);
                      }
                      $st = $db->prepare("INSERT INTO NOTES(LID, DOC) VALUES (?, ?);");
                      $st->execute($lid[0], $gzero[0]);
                       #Flatten ground zero
                      $st = $db->prepare("UPDATE NOTES SET DOC='' WHERE LID=0;");
                      $st->execute();
                   }
                }
                #
                # After Insert renumeration check
                #
                my $dt    = DateTime::Format::SQLite->parse_datetime($date);
                my $dtCur = DateTime->now();
                $dtCur->set_time_zone(&Settings::timezone);
                $dtCur = $dtCur - DateTime::Duration->new( days => 1 );

                if ( $dtCur > $dt ) {
                    print $cgi->p('<b>Insert is in the past!</b>');
                   Settings::renumerate($db);
                }
            }
}
 catch {

my $err = $@;
my $pwd = `pwd`;
$pwd =~ s/\s*$//;

my $dbg = qq(--DEBUG OUTPUT--\n
    DSN:$dsn
    stm:$stm
    \@DB::args:@DB::args
    \$DBI::err:$DBI::errstr
    cnt:$cnt, cat:$cat, date:$date, log:$log, am:$am, af:$af, rtf:$rtf, sticky:$sticky);
print $cgi->header,
        "<hr><font color=red><b>SERVER ERROR</b></font> on ".DateTime->now.
        "<hr><pre>$pwd/$0 -> &".caller." -> [<font color=red><b>$DBI::errstr</b></font>] $err\n$dbg</pre>",
        $cgi->end_html;

    exit;
}
}

    sub buildNavigationButtons {

        if ( !$log_cur_id ) {

        #Following is a quick hack as previous id as current minus one might not
        #coincide in the database table!
            $log_cur_id = $id - 1;
        }
        if ( $tfId == 1 ) {
            $tfId = 0;
        }
        else {
            $tfId = 1;
        }

        $vmode = "[In Page Mode]&nbsp;";
        $vmode = "<font color='red'>[In View Mode]</font>&nbsp;" if &isInViewMode;

        if($rec_limit == 0){
            $log_output .= qq!<tr class="r$tfId"><td>$vmode</td><td colspan="3">
                               <input class="ui-button" type="button" onclick="submitTop($log_top);return false;" value="Back To Page View"/>!;

        }
        else{
                if ($rs_cur < $log_top && $rs_prev && $rs_prev > 0 && $log_start > 0 && $rs_page > 0) {

                    $log_output .= qq!<tr class="r$tfId"><td>$vmode</td><td colspan="3"><input class="ui-button" type="button" onclick="submitTop($log_top);return false;" value="TOP"/>&nbsp;&nbsp;
                    <input type="hidden" value="$rs_prev"/>
                    <input class="ui-button" type="button" onclick="submitPrev($log_rc_prev, $rec_limit);return false;" value="&lsaquo;&lsaquo;&nbsp; Previous"/>&nbsp;&nbsp;!;

                }
                else {
                    $log_output .= qq(<tr class="r$tfId"><td>$vmode</td><td colspan="3"><i>Top</i>&nbsp;&nbsp;&nbsp;&nbsp;);
                }


                    $log_output .= '<input class="ui-button" type="button" onclick="viewAll();return false;" value="View All"/>&nbsp;&nbsp;';


                if ( $log_cur_id == 0 ) {
                    $log_output = $log_output . '<i>End</i></td>';
                }
                else {

                    $log_output .= qq!<input class="ui-button" type="button" onclick="submitNext($log_cur_id, $rec_limit);return false;"
                                        value="Next &nbsp;&rsaquo;&rsaquo;"/>&nbsp;&nbsp;
                                        <input class="ui-button" type="button" onclick="submitEnd($rec_limit);return false;" value="END"/></td>!;

                }
        }

        $log_output .= '<td colspan="2"></td></tr>';
    }

sub authenticate {
    try {

        my $st = traceDBExe("SELECT alias FROM AUTH WHERE alias='$userid' and passw='$password';");
        my @c = $st->fetchrow_array();
        if (@c && $c[0] eq $userid ) { return; }

        #Check if passw has been wiped for reset?
        $st = traceDBExe("SELECT * FROM AUTH WHERE alias='$userid';");
        @c = $st->fetchrow_array();
        if ( @c && $c[1] == "" ) {
            #Wiped with -> UPDATE AUTH SET passw='' WHERE alias='$userid';
            $st = traceDBExe("UPDATE AUTH SET passw='$password' WHERE alias='$userid';");
            return;
        }

        print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
        print $cgi->start_html(
            -title => "Personal Log Login",
            -BGCOLOR => $BGCOL,
            -script =>
                { -type => 'text/javascript', -src => 'wsrc/main.js' },
            -style => { -type => 'text/css', -src => 'wsrc/main.css' },
        );
        if($DEBUG){
                print $cgi->center(
                    $cgi->div("<b>Access Denied!</b> alias:$userid pass:$password SQL->SELECT * FROM AUTH WHERE alias='$userid' and passw='$password'; ")
                );
        }
        else{
                print $cgi->center(
                    $cgi->div('<h2>Sorry Access Denied!</h2><font color=red><b>You supplied wrong credentials.</b></font>'),
                    $cgi->div('<h3>[<a href="login_ctr.cgi">Login</a>]</h3>')
                );
        }
        print $cgi->end_html;

        $db->disconnect();
        $sss->flush();
        exit;

    }
    catch {
        print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
        print $cgi->p( "PAGE ERROR:" . $_ );
        print $cgi->end_html;
        exit;
    }
}

sub fetchAutocomplete {
    my $st = traceDBExe('SELECT LOG from LOG' . $stmE );
    while ( my @row = $st->fetchrow_array() ) {
        my $log = $row[0];

        #Decode escaped \\n
        $log =~ s/\\n/\n/gs;
        $log =~ s/''/'/g;

        #Replace link to empty string
        my @words = split( /($re_a_tag)/si, $log );
        foreach my $ch_i (@words) {
            next if $ch_i =~ /$re_a_tag/;
            next if index( $ch_i, "<img" ) > -1;
            $ch_i =~ s/https//gsi;
            $ch_i =~ s/($RE{URI}{HTTP})//gsi;
        }
        $log   = join( ' ', @words );
        @words = split( ' ', $log );
        foreach my $word (@words) {

            #remove all non alphanumerics
            $word =~ s/[^a-zA-Z]//gs;
            if ( length($word) > 2 ) {
                $word = lc $word;
                #parse for already placed words, instead of using an hash.
                my $idx = index( $autowords, $word, 0 );
                if ( $idx > 0 ) {
                    my $end = index( $autowords, '"', $idx );
                    my $existing =
                        substr( $autowords, $idx, $end - $idx );
                    next if $word eq $existing;
                }

                $autowords .= qq(,"$word");
                if ( $aw_cnt++ > &Settings::autoWordLimit ) {
                    last;
                }
            }
        }

        if ( $aw_cnt > &Settings::autoWordLimit ) {
            last;
        }
    }
}

sub cam {
    my $am = sprintf( "%.2f", shift @_ );
    # Add one comma each time through the do-nothing loop
    1 while $am =~ s/^(-?\d+)(\d\d\d)/$1,$2/;
    return $am;
}


sub isInViewMode {
    return $sss->param('sss_vc') || $sss->param('sss_xc');
}


sub quill{

    my ( $log_id, $height ) = shift;

switch ( &Settings::windowRTFSize ) {
        case "0" { $height = q(height:420px;) }
        case "1" { $height = q(height:260px;) }
        case "2" { $height = q(height:140px;) }
        else {
            $height = &Settings::windowRTFSize;
        }
}
return qq(
<table id="tbl_doc" class="tbl" width=").&Settings::pagePrcWidth.qq(%" style="border:1; margin-top: 5px;" hidden>
	<tr class="r0" style="text-align:center"><td><b>* Document *</b>
    <a id="log_close" href="#" onclick="return hide('#tbl_doc');">$sp1</a>
    <a id="log_close" href="#" onclick="return toggleDoc(false);">$sp2</a>
    <a id="log_close" href="#" onclick="return resizeDoc();">$sp3</a>
    </td>
</tr>
<tr id="rtf_doc"><td>
  <div id="toolbar-container" hidden>
    <span class="ql-formats">
      <select class="ql-font"></select>
      <select class="ql-size"></select>
    </span>
    <span class="ql-formats">
      <button class="ql-bold"></button>
      <button class="ql-italic"></button>
      <button class="ql-underline"></button>
      <button class="ql-strike"></button>
    </span>
    <span class="ql-formats">
      <select class="ql-color"></select>
      <select class="ql-background"></select>
    </span>
    <span class="ql-formats">
      <button class="ql-script" value="sub"></button>
      <button class="ql-script" value="super"></button>
    </span>
    <span class="ql-formats">
      <button class="ql-header" value="1"></button>
      <button class="ql-header" value="2"></button>
      <button class="ql-blockquote"></button>
      <button class="ql-code-block"></button>
    </span>
    <span class="ql-formats">
      <button class="ql-list" value="ordered"></button>
      <button class="ql-list" value="bullet"></button>
      <button class="ql-indent" value="-1"></button>
      <button class="ql-indent" value="+1"></button>
    </span>
    <span class="ql-formats">
      <button class="ql-direction" value="rtl"></button>
      <select class="ql-align"></select>
    </span>
    <span class="ql-formats">
      <button class="ql-link"></button>
      <button class="ql-image"></button>
      <button class="ql-video"></button>
      <button class="ql-formula"></button>
    </span>
    <span class="ql-formats" style="float:right; border:1px;">
        Background <input id="fldBG" type="field" class="jscolor {onFineChange:'editorBackground(false)',closable:true,closeText:'Close',hash:true}" size="10" value="000000"/>
        <button onClick="editorBackground(true);" style="float:right; border:1px;">&nbsp;&nbsp;Reset</button>
    </span>
  </div>
  <div id="editor-container" style="$height"></div>
  <div class="save_button">
  <input type="button" id="btn_save_doc" onclick="saveRTF(0, 'store'); return false;" value="Save"/>
  </div>
  </td></tr></table>
)}

sub help{
return qq(
<table id="tbl_hlp" class="tbl" border="0" width=").&Settings::pagePrcWidth.qq(%" hidden>
	<tr class="r0"><td colspan="3"><b>* HELP *</b>
    <a id="a_close" href="#" onclick="return hide('#tbl_hlp');">$sp1</a>
    <a id="a_toggle" href="#" onclick="return toggle('#tbl_hlp .collpsd');">$sp2</a>
    </td></tr>
<tr class="collpsd"><td>
<div id="rz" class="rz">
    <h2>L-Tags Specs</h2>
    <p class="rz">
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
    <b>&#60;&#60;LIST&#60;<i>{List of items delimited by new line to terminate item or with '~' otherwise.}</i><b>&#62;</b>
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
					<p>
					<b>&#60;&#60;LNK&#60;<i>{url to image}</i><b>&#62;&#62;</b><br><br>
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
</td></tr></table>
)
}
