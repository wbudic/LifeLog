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
our $REC_LIMIT    = 25;
our $TIME_ZONE    = 'Australia/Sydney';
our $LANGUAGE     = 'English';
our $PRC_WIDTH    = '60';
our $LOG_PATH     = '../../dbLifeLog/';
our $SESSN_EXPR   = '+30m';
our $DATE_UNI     = '0';
our $RELEASE_VER  = '1.4';
our $AUTHORITY    = '';
our $IMG_W_H      = '210x120';
our $AUTO_WRD_LMT = 200;

#END OF SETTINGS

my $cgi = CGI->new;
my $session =
  new CGI::Session( "driver:File", $cgi, { Directory => $LOG_PATH } );
my $sid      = $session->id();
my $dbname   = $session->param('database');
my $userid   = $session->param('alias');
my $password = $session->param('passw');

if ($AUTHORITY) {
    $userid = $password = $AUTHORITY;
    $dbname = 'data_' . $userid . '_log.db';
}
elsif ( !$userid || !$dbname ) {
    print $cgi->redirect("login_ctr.cgi?CGISESSID=$sid");
    exit;
}

my $database = '../../dbLifeLog/' . $dbname;
my $dsn      = "DBI:SQLite:dbname=$database";
my $db       = DBI->connect( $dsn, $userid, $password, { RaiseError => 1 } )
  or die "<p>Error->" & $DBI::errstri & "</p>";

my ( $imgw, $imgh );

### Authenticate session to alias password
&authenticate;
&getConfiguration($db );

my $tbl_rc      = 0;
my $tbl_rc_prev = 0;
my $tbl_cur_id;
my $rs_keys     = $cgi->param('keywords');
my $rs_cat_idx  = $cgi->param('category');
my $prm_vc      = $cgi->param("vc");
my $rs_dat_from = $cgi->param('v_from');
my $rs_dat_to   = $cgi->param('v_to');
my $rs_prev     = $cgi->param('rs_prev');
my $rs_cur      = $cgi->param('rs_cur');
my $rs_page     = $cgi->param('rs_page');
my $stmS        = "SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT from LOG WHERE";
my $stmE        = " ORDER BY DATE DESC;";
my $stmD        = "";
if ( !$rs_dat_to ) {
      $rs_dat_to = 'now';
}

if ( $rs_dat_from && $rs_dat_to ) {
     $stmD =qq(" DATE BETWEEN date('$rs_dat_from') AND date('$rs_dat_to') ");
}

my $toggle = "";
if ( $rs_keys || $rs_cat_idx || $stmD ) { $toggle = 1; }

$session->expire($SESSN_EXPR);

#tag related framed sizing.
my @arrwh = split /x/, $IMG_W_H;
if ( @arrwh == 2 ) {
      $imgw = $arrwh[0];
      $imgh = $arrwh[1];
}
else {    #defaults
      $imgw = 210;
      $imgh = 120;
}

print $cgi->header(
      -expires => "0s",
      -charset => "UTF-8"
  );
print $cgi->start_html(
      -title   => "Personal Log",
      -BGCOLOR => "#c8fff8",
      -onload  => "loadedBody('" . $toggle . "');",
      -style   => [
          { -type => 'text/css', -src => 'wsrc/main.css' },
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

my $rv;
my $st;
my $lang  = Date::Language->new($LANGUAGE);
my $today = DateTime->now;
$today->set_time_zone($TIME_ZONE);

my $stmtCat = "SELECT * FROM CAT;";
my $stmt =
"SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT FROM LOG ORDER BY DATE DESC, rowid DESC;";

$st = $db->prepare($stmtCat);
$rv = $st->execute() or die or die "<p>Error->" & $DBI::errstri & "</p>";

my $cats = qq(<select   class="ui-widget-content" id="ec" name="ec" 
 onFocus="showCat();" 
 onBlur="helpSelCategory(this);" 
 onScroll="helpSelCategory(this);updateSelCategory(this)" 
 onChange="updateSelCategory(this)">
 <option value="0">---</option>\n);
my %hshCats;
my %desc   = {};
my $c_sel  = 1;
my $cats_v = $cats;
$cats_v =~ s/\"ec\"/\"vc\"/g;

while ( my @row = $st->fetchrow_array() ) {
      if ( $row[0] == $c_sel ) {
          $cats =
              $cats
            . '<option selected value="'
            . $row[0] . '">'
            . $row[1]
            . '</option>\n';
      }
      else {
          $cats =
              $cats
            . '<option value="'
            . $row[0] . '">'
            . $row[1]
            . '</option>\n';
      }
      if ( $row[0] == $prm_vc ) {
          $cats_v =
              $cats_v
            . '<option selected value="'
            . $row[0] . '">'
            . $row[1]
            . '</option>\n';
      }
      else {
          $cats_v =
              $cats_v
            . '<option value="'
            . $row[0] . '">'
            . $row[1]
            . '</option>\n';
      }
      $hshCats{ $row[0] } = $row[1];
      $desc{ $row[0] }    = $row[2];
}

$cats = $cats . '</select>';

my $cat_descriptions = "";
for my $key ( keys %desc ) {
      my $kv = $desc{$key};
      if ( $kv ne ".." ) {
          $cat_descriptions .= qq(<li id="$key">$kv</li>\n);
    }
}

my $tbl =
qq(<form id="frm_log" action="remove.cgi" onSubmit="return formDelValidation();">
<table class="tbl" border="0" width="$PRC_WIDTH%">
<tr class="hdr">
	<th class="tbl">Date</th>
	<th class="tbl">Time</th>
	<th class="tbl">Log</th><th>#</th>
	<th class="tbl">Category</th><th>Edit</th>
</tr>);

if (defined $prm_vc) {    #view category form selection
      $rs_cat_idx = $prm_vc;
}

if ($rs_keys) {

      my @keywords = split / /, $rs_keys;
      if ($rs_cat_idx) {
          $stmS = $stmS . " ID_CAT='" . $rs_cat_idx . "' AND";
      }
      else {
          $stmS = $stmS . " ID_CAT='0' OR";
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
          $stmt = $stmS . $stmE;
    }
}
elsif ($rs_cat_idx) {

      if ($stmD) {
          $stmt = $stmS . $stmD . " AND ID_CAT='" . $rs_cat_idx . "'" . $stmE;
      }
      else {
          $stmt = $stmS . " ID_CAT='" . $rs_cat_idx . "'" . $stmE;
    }
}
else {
      if ($stmD) {
          $stmt = $stmS . $stmD . $stmE;
    }
}

###############
&processSubmit;
###############
#
# Uncomment bellow to see main query statement issued!
# print $cgi->pre("### -> ".$stmt);
#
my $tfId      = 0;
my $id        = 0;
my $tbl_start = index $stmt, "<=";
my $re_a_tag  = qr/<a\s+.*?>.*<\/a>/si;

if ( $tbl_start > 0 ) {

      #check if we are at the beggining of the LOG table?
      my $stc =
        $db->prepare('select rowid from LOG order by rowid DESC LIMIT 1;');
      $stc->execute();
      my @row = $stc->fetchrow_array();
      if ( $row[0] == $rs_prev && $rs_cur == $rs_prev ) {
          $tbl_start = -1;
      }
      $stc->finish();
}
#
#Fetch entries!
#
my $CID_EVENT = 9;
my $tags      = "";
$st = $db->prepare($stmt);
$rv = $st->execute() or die or die "<p>Error->" & $DBI::errstri & "</p>";
if ( $rv < 0 ) {
      print "<p>Error->" & $DBI::errstri & "</p>";
}
while ( my @row = $st->fetchrow_array() ) {

      $id = $row[0];

      my $ct  = $hshCats{ $row[1] };
      my $dt  = DateTime::Format::SQLite->parse_datetime( $row[2] );
      my $log = $row[3];
      my $amm = sprintf "%.2f", $row[4];

      #Apostrophe in the log value is doubled to avoid SQL errors.
      $log =~ s/''/'/g;
      #
      if ( !$ct ) {
          $ct = $hshCats{1};
      }
      if ( !$dt ) {
          $dt = $today;
      }
      if ( !$amm ) {
          $amm = "0.00";
      }
      if ( $tbl_rc_prev == 0 ) {
          $tbl_rc_prev = $id;
      }
      if ( $tfId == 1 ) {
          $tfId = 0;
      }
      else {
          $tfId = 1;
      }

      my $sub    = "";
      my $tagged = 0;

#Check for LNK takes precedence here as we also parse plain placed URL's for http protocol later.
      if ( $log =~ /<<LNK</ ) {
          my $idx = $-[0] + 5;
          my $len = index( $log, '>', $idx );
          $sub = substr( $log, $idx + 1, $len - $idx - 1 );
          my $url = qq(<a href="$sub" target=_blank>$sub</a>);
          $tags .= qq(<input id="tag$id" type="hidden" value="$log"/>\n);
          $tagged = 1;
          $log =~ s/<<LNK<(.*?)>/$url/osi;
      }

      if ( $log =~ /<<IMG</ ) {
          my $idx = $-[0] + 5;
          my $len = index( $log, '>', $idx );
          $sub = substr( $log, $idx + 1, $len - $idx - 1 );
          my $url = qq(<img src="$sub"/>);
          if ( !$tagged ) {
              $tags .= qq(<input id="tag$id" type="hidden" value="$log"/>\n);
          }
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
              $lnk =
qq(\n<img src="$lnk" width="$imgw" height="$imgh" class="tag_FRM"/>);
          }
          if ( !$tagged ) {
              $tags .= qq(<input id="tag$id" type="hidden" value="$log"/>\n);
          }
          $log =~ s/<<FRM<(.*?)>/$lnk/o;
      }

      #Replace with a full link an HTTP URI
      my @chnks = split( /($re_a_tag)/si, $log );
      foreach my $ch_i (@chnks) {
          next if $ch_i =~ /$re_a_tag/;
          next if index( $ch_i, "<img" ) > -1;
          $ch_i =~ s/https/http/gsi;
          $ch_i =~ s/($RE{URI}{HTTP})/<a href="$1" target=_blank>$1<\/a>/gsi;
      }
      $log = join( '', @chnks );

      while ( $log =~ /<<B</ ) {
          my $idx = $-[0];
          my $len = index( $log, '>', $idx ) - 4;
          my $sub = "<b>" . substr( $log, $idx + 4, $len - $idx ) . "</b>";
          $log =~ s/<<B<(.*?)>/$sub/o;
      }
      while ( $log =~ /<<I</ ) {
          my $idx = $-[0];
          my $len = index( $log, '>', $idx ) - 4;
          my $sub = "<i>" . substr( $log, $idx + 4, $len - $idx ) . "</i>";
          $log =~ s/<<I<(.*?)>/$sub/o;
      }
      while ( $log =~ /<<TITLE</ ) {
          my $idx = $-[0];
          my $len = index( $log, '>', $idx ) - 8;
          my $sub = "<h3>" . substr( $log, $idx + 8, $len - $idx ) . "</h3>";
          $log =~ s/<<TITLE<(.*?)>/$sub/o;
      }

      #Decode escaped \\n
      $log =~ s/\\n/<br>/gs;

      if ( $CID_EVENT == $row[1] ) {
          $log = "<font color='#eb4848' style='font-weight:bold'>$log</font>";
      }
      elsif ( 1 == $row[1] ) {
          $log =
"<font color='midnightblue' style='font-weight:bold;font-style:italic'>$log</font>";
      }

      my ( $dty, $dtf ) = $dt->ymd;
      my $dth = $dt->hms;
      if ( $DATE_UNI == 1 ) {
          $dtf = $dty;
      }
      else {
          $dtf = $lang->time2str( "%d %b %Y", $dt->epoch, $TIME_ZONE);
      }
      $tbl .= qq(<tr class="r$tfId">
		<td width="15%">$dtf<input id="y$id" type="hidden" value="$dty"/></td>
		<td id="t$id" width="10%" class="tbl">$dth</td>
		<td id="v$id" class="log" width="40%">$log</td>
		<td id="a$id" width="10%" class="tbl">$amm</td>
		<td id="c$id" width="10%" class="tbl">$ct</td>
		<td width="20%">
			<button class="edit" value="Edit" onclick="return edit($id);">Edit</button>
			<input name="chk" type="checkbox" value="$id"/>
		</td>
	</tr>);
      $tbl_rc += 1;

      if ( $REC_LIMIT > 0 && $tbl_rc == $REC_LIMIT ) {
          &buildNavigationButtons;
          last;
    }

}    #while end

##
#Fetch Keywords autocomplete we go by words larger then three.
#
$st = $db->prepare('select LOG from LOG;');
my $aw_cnt = 0;
my $autowords = qq("gas","money","today");
$rv = $st->execute() or die or die "<p>Error->" & $DBI::errstri & "</p>";
if ( $rv < 0 ) {
      print "<p>Error->" & $DBI::errstri & "</p>";
}
&fetchAutocomplete;

#End of table?
if ( $rs_prev && $tbl_rc < $REC_LIMIT ) {
      $st = $db->prepare("SELECT count(*) FROM LOG;");
      $st->execute();
      my @row = $st->fetchrow_array();
      if ( $row[0] > $REC_LIMIT ) {
          &buildNavigationButtons(1);
    }
}

if ( $tbl_rc == 0 ) {

      if ($stmD) {
          $tbl = $tbl . '<tr><td colspan="5">
			<b>Search Failed to Retrive any records on select: [<i>' . $stmD
            . '</i>] !</b></td></tr>';
      }
      elsif ($rs_keys) {
          my $criter = "";
          if ( $rs_cat_idx > 0 ) {
              $criter = "->Criteria[" . $hshCats{$rs_cat_idx} . "]";
          }
          $tbl = $tbl . qq(<tr><td colspan="5">
			<b>Search Failed to Retrive any records on keywords: [<i>$rs_keys</i>]$criter!</b></td>
			</tr>);
      }
      else {
          $tbl = $tbl
            . '<tr><td colspan="5"><b>Database is New or  Empty!</b></td></tr>\n';
    }
}

$tbl .=
'<tr class="r0"><td><a id="floating_menu_close" href="#" onclick="return showFloatingMenu();"><span  class="ui-icon ui-icon-heart"></span></a>
<a href="#top">&#x219F;</a></td><td colspan="5" align="right"> 
<input type="hidden" name="datediff" id="datediff" value="0"/>
<input type="submit" value="Date Diff Selected" onclick="return dateDiffSelected()"/>&nbsp;
<button onclick="return selectAllLogs()">Select All</button>
<input type="reset" value="Unselect All"/>
<input type="submit" value="Delete Selected"/>
</td></tr></form>
<tr class="r0"><form id="frm_srch" action="main.cgi"><td><b>Keywords:</b></td><td colspan="4" align="left">
<input id="rs_keys2" name="keywords" type="text" size="60"/></td>
<td><input type="submit" value="Search"/></form></td></tr>
</table>';

my $frm = qq(<a name="top"></a>
<form id="frm_entry" action="main.cgi" onSubmit="return formValidation();">
	<table class="tbl" border="0" width="$PRC_WIDTH%">
	<tr class="r0"><td colspan="3"><b>* LOG ENTRY FORM *</b></td></tr>	
	<tr>
	<td style="text-align:right;  vertical-align:top">Date:</td>
	<td id="al" colspan="1" style="text-align:top; vertical-align:top"><input id="ed" type="text" name="date" size="18" value=")
  . $today->ymd . " "
  . $today->hms . qq(">
	
	&nbsp;<button type="button" onclick="return setNow();">Now</button>
			&nbsp;<button type="reset">Reset</button></td>
			<td style="text-align:top; vertical-align:top">Category: 
$cats
				<br><br><div id="cat_desc" name="cat_desc"></div>
			</td>
	</tr>
	<tr><td style="text-align:right; vertical-align:top">Log:</td>
		<td id="al" colspan="2" style="text-align:top;">
			<textarea id="el" name="log" rows="3" style="float:left; width:99%;" onChange="toggleVisibility('cat_desc',true)"></textarea>
		</td>	
	</tr>
		<tr><td style="text-align:right"><a id="to_bottom" href="#bottom" title="Go to bottom of page.">&#x21A1;</a>&nbsp;Ammount:</td>
		<td id="al">
			<input id="am" name="am" type="number" step="any">			
		</td>
		<td align="right">			  
				<div 	style="float: right;"><button id="btn_srch" onclick="toggleSearch(this); return false;">Show Search</button>&nbsp;
				<input id="log_submit" type="submit" value="Submit"/></div>
		</td>		
	</tr>
	<tr><td colspan="3"></td></tr>
	</table>
	<input type="hidden" name="submit_is_edit" id="submit_is_edit" value="0"/>
	<input type="hidden" name="submit_is_view" id="submit_is_view" value="0"/>
	<input type="hidden" name="rs_all" value="0"/>
	<input type="hidden" name="rs_cur" value="0"/>
	<input type="hidden" name="rs_prev" value="$tbl_rc_prev"/>
	<input type="hidden" name="rs_page" value="$rs_page"/>
	<input type="hidden" name="CGISESSID" value="$sid"/>
	$tags</form>
	);

my $srh = qq(
	<form id="frm_srch" action="main.cgi">
	<table class="tbl" border="0" width="$PRC_WIDTH%">
					<tr class="r0"><td colspan="4"><b>Search/View By</b></td></tr>
		);

$srh .=
qq(<tr><td align="right"><b>View by Category:</b></td><td>$cats_v</td><td></td>
	<td colspan="1" align="left">
	<button id="btn_cat" onclick="viewByCategory(this);" style="float:left">View</button>
	<input id="idx_cat" name="category" type="hidden" value="0"></td></tr>
	<tr><td align="right"><b>View by Date:</b></td>
	<td align="left">
	From:&nbsp;<input name="v_from" type="text" size="16"/></td><td align="left">
	To:&nbsp;<input name="v_to" type="text" size="16"/>
	<td align="left"><button id="btn_dat" onclick="viewByDate(this);">View</button></td>
	</tr>
	<tr><td align="right"><b>Keywords:</b></td>
				<td colspan="2" align="left">
					<input id="rs_keys" name="keywords" type="text" size="60" value="$rs_keys"/></td>
				<td align="left"><input type="submit" value="Search" align="left"></td></tr>);

if ( $rs_keys || $rs_cat_idx || $stmD ) {
      $srh .= '<tr><td align="left" colspan="3">
	<button onClick="resetView()">Reset Whole View</button></td></tr>';
}

$srh .= '</table></form><br>';
#
#Page printout from here!
#
print qq(<center>\n
<div id="floating_menu" title="To close this menu click on its heart, and wait.">
<div class="hdr" style="marging=0;padding:0px;">
<a id="to_top" href="#top" title="Go to top of page."><span class="ui-icon ui-icon-arrowthick-1-n"></span></a>&nbsp;
<a id="to_bottom" href="#bottom" title="Go to bottom of page."><span class="ui-icon ui-icon-arrowthick-1-s"></span></a>
<a id="floating_menu_close" href="#"><span  class="ui-icon ui-icon-heart"></span></a>
</div>
<hr>
<a class="a_" href="stats.cgi">Stats</a><hr>
<a class="a_" href="config.cgi">Config</a><hr>
<br>
<a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a>
</div>

	  <div>\n$frm\n</div>\n<br>\n
	  <div id="div_srh">$srh</div>
	  <div>\n$tbl\n</div><br>
	  <div><a class="a_" href="stats.cgi">View Statistics</a></div><br>
	  <div><a class="a_" href="config.cgi">Configure Log</a></div><hr>
		<div><a class="a_" href="login_ctr.cgi?logout=bye">LOGOUT</a><hr><a name="bottom"/></div>
	);
print qq(</center>
        <ul id="cat_lst">
				$cat_descriptions
				</ul>	
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
undef($session);
exit;

=comm
sub parseDate{
	my $date = $_[0];
try{	
return DateTime::Format::SQLite->parse_datetime( $date );
}
catch{
  print "<font color=red><b>SERVER ERROR</b></font>date:$date]->".$_;
}
return $today;
}
=cut

sub processSubmit {

      my $date = $cgi->param('date');
      my $log  = $cgi->param('log');
      my $cat  = $cgi->param('ec')
        ;    #Used to be cat v.1.3, tag id and name should be kept same.
      my $amm = $cgi->param('am');

      my $edit_mode = $cgi->param('submit_is_edit');
      my $view_mode = $cgi->param('submit_is_view');
      my $view_all  = $cgi->param('rs_all');

      try {
#Apostroph's need to be replaced with doubles  and white space fixed for the SQL.
          $log =~ s/(?<=\w) ?' ?(?=\w)/''/g;

          if ( $edit_mode && $edit_mode != "0" ) {

              #Update

              my $stm =
                  "UPDATE LOG SET ID_CAT='"
                . $cat
                . "', DATE='"
                . $date . "',
	       		   LOG='"
                . $log
                . "', AMMOUNT='"
                . $amm
                . "' WHERE rowid="
                . $edit_mode . ";";
              my $st = $db->prepare($stm);
              $st->execute();
              return;
          }

          if ( $view_all && $view_all == "1" ) {
              $REC_LIMIT = 0;
          }

          if ( $view_mode == "1" ) {

              if ($rs_cur) {

                  if ( $rs_cur == $rs_prev )
                  {    #Mid page back button if id ordinal.
                      $rs_cur += $REC_LIMIT;
                      $rs_prev = $rs_cur;
                      $rs_page--;
                  }
                  else {
                      $rs_page++;
                  }

                  $stmt =
'SELECT rowid, ID_CAT, DATE, LOG, AMMOUNT from LOG where rowid <= "'
                    . $rs_cur
                    . '" ORDER BY DATE DESC;;;'
                    . $rs_page;
                  return;
            }
          }

          if ( $log && $date && $cat ) {

              #check for double entry
              #
              my $st =
                $db->prepare( "SELECT DATE,LOG FROM LOG where DATE='"
                    . $date
                    . "' AND LOG='"
                    . $log
                    . "';" );

              $st->execute();
              if ( my @row = $st->fetchrow_array() ) {
                  return;
              }

              $st = $db->prepare('INSERT INTO LOG VALUES (?,?,?,?)');
              $st->execute( $cat, $date, $log, $amm );
              #
              # After Insert renumeration check
              #
              my $dt    = DateTime::Format::SQLite->parse_datetime($date);
              my $dtCur = DateTime->now();
              $dtCur->set_time_zone($TIME_ZONE);
              $dtCur = $dtCur - DateTime::Duration->new( days => 1 );

              if ( $dtCur > $dt ) {
                  print $cgi->p('<b>Insert is in the past!</b>');

                  #Renumerate directly (not proper SQL but faster);
                  $st = $db->prepare('select rowid from LOG ORDER BY DATE;');
                  $st->execute();
                  my $cnt = 1;
                  while ( my @row = $st->fetchrow_array() ) {
                      my $st_upd =
                        $db->prepare( "UPDATE LOG SET rowid="
                            . $cnt
                            . " WHERE rowid='"
                            . $row[0]
                            . "';" );
                      $st_upd->execute();
                      $cnt = $cnt + 1;
                }
            }
        }
      }
      catch {
          print "ERROR:" . $_;
    }
}

sub buildNavigationButtons {

      my $is_end_of_rs = shift;

      if ( !$tbl_cur_id ) {

        #Following is a quick hack as previous id as current minus one might not
        #coincide in the database table!
          $tbl_cur_id = $id - 1;
      }
      if ( $tfId == 1 ) {
          $tfId = 0;
      }
      else {
          $tfId = 1;
      }

      $tbl .= qq!<tr class="r$tfId"><td></td>!;

      if ( $rs_prev && $rs_prev > 0 && $tbl_start > 0 && $rs_page > 0 ) {

          $tbl = $tbl . qq!<td><input type="hidden" value="$rs_prev"/>
	 <input type="button" onclick="submitPrev($rs_prev);return false;"
	  value="&lsaquo;&lsaquo;&ndash; Previous"/></td>!;

      }
      else {
          $tbl .= '<td><i>Top</i></td>';
      }

      $tbl .=
'<td colspan="1"><input type="button" onclick="viewAll();return false;" value="View All"/></td>';

      if ( $is_end_of_rs == 1 ) {
          $tbl = $tbl . '<td><i>End</i></td>';
      }
      else {

          $tbl .=
qq!<td><input type="button" onclick="submitNext($tbl_cur_id);return false;"
		                      value="Next &ndash;&rsaquo;&rsaquo;"/></td>!;

      }

      $tbl = $tbl . '<td colspan="2"></td></tr>';
}

sub authenticate {
      try {

          if ($AUTHORITY) {
              return;
          }

          my $st = $db->prepare(
              "SELECT * FROM AUTH WHERE alias='$userid' and passw='$password';"
          );
          $st->execute();
          if ( $st->fetchrow_array() ) { return; }

          #Check if passw has been wiped for reset?
          $st = $db->prepare("SELECT * FROM AUTH WHERE alias='$userid';");
          $st->execute();
          my @w = $st->fetchrow_array();
          if ( @w && $w[1] == "" ) {

              #Wiped with -> UPDATE AUTH SET passw='' WHERE alias='$userid';
              $st = $db->prepare(
                  "UPDATE AUTH SET passw='$password' WHERE alias='$userid';");
              $st->execute();
              return;
          }

          print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
          print $cgi->start_html(
              -title  => "Personal Log Login",
              -script => { -type => 'text/javascript', -src => 'wsrc/main.js' },
              -style  => { -type => 'text/css', -src => 'wsrc/main.css' },
          );

          print $cgi->center(
              $cgi->div("<b>Access Denied!</b> alias:$userid pass:$password") );
          print $cgi->end_html;

          $db->disconnect();
          $session->flush();
          exit;

      }
      catch {
          print $cgi->header( -expires => "+0s", -charset => "UTF-8" );
          print $cgi->p( "ERROR:" . $_ );
          print $cgi->end_html;
          exit;
    }
}

sub fetchAutocomplete {
      try {

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
                          my $end      = index( $autowords, '"', $idx );
                          my $existing = substr( $autowords, $idx, $end - $idx );
                          next if $word eq $existing;
                      }

                      $autowords .= qq(,"$word");
                      if ( $aw_cnt++ > $AUTO_WRD_LMT ) {
                          last;
                    }
                }
              }

              if ( $aw_cnt > $AUTO_WRD_LMT ) {
                  last;
            }
        }

      }
      catch {
          print "<font color=red><b>SERVER ERROR</b></font>:" . $_;
    }
}

sub getConfiguration {
      my $db = shift;
      try {
          $st = $db->prepare("SELECT * FROM CONFIG;");
          $st->execute();

          while ( my @r = $st->fetchrow_array() ) {

              switch ( $r[1] ) {
                  case "REC_LIMIT"    { $REC_LIMIT    = $r[2] }
                  case "TIME_ZONE"    { $TIME_ZONE    = $r[2] }
                  case "PRC_WIDTH"    { $PRC_WIDTH    = $r[2] }
                  case "SESSN_EXPR"   { $SESSN_EXPR   = $r[2] }
                  case "DATE_UNI"     { $DATE_UNI     = $r[2] }
                  case "LANGUAGE"     { $LANGUAGE     = $r[2] }
                  case "IMG_W_H"      { $IMG_W_H      = $r[2] }
                  case "AUTO_WRD_LMT" { $AUTO_WRD_LMT = $r[2] }
                  else {
                      print "Unknow variable setting: " . $r[1] . " == " . $r[2];
                }
            }

        }
      }
      catch {
          print "<font color=red><b>SERVER ERROR</b></font>:" . $_;
    }
}
