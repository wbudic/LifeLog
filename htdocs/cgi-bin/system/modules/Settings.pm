#!/usr/bin/perl -w
package Settings;

use strict;
use warnings;
use Switch;

use DBI;

#DEFAULT SETTINGS HERE!
our $REC_LIMIT    = 25;
our $TIME_ZONE    = 'Australia/Sydney';
our $LANGUAGE     = 'English';
our $PRC_WIDTH    = '60';
our $LOG_PATH     = '../../dbLifeLog/';
our $SESSN_EXPR   = '+30m';
our $DATE_UNI     = '0';
our $RELEASE_VER  = '1.6';
our $AUTHORITY    = '';
our $IMG_W_H      = '210x120';
our $AUTO_WRD_LMT = 1000;
our $FRAME_SIZE   = 0;
our $RTF_SIZE     = 0;
our $THEME        = 'Standard';

### Page specific settings Here
my $TH_CSS        = 'main.css';
my $BGCOL         = '#c8fff8';
#Set to 1 to get debug help. Switch off with 0.
my $DEBUG        = 0;
#END OF SETTINGS



sub new {
    return bless {}, shift;
}
sub release        {return $RELEASE_VER;}
sub logPath        {return $LOG_PATH;}
sub theme          {return $THEME;}
sub language       {return $LANGUAGE;}
sub timezone       {return $TIME_ZONE;}
sub sessionExprs   {return $SESSN_EXPR;}
sub imgWidthHeight {return $IMG_W_H;}
sub pagePrcWidth   {return $PRC_WIDTH;}
sub recordLimit    {return $REC_LIMIT;}
sub frameSize      {return $FRAME_SIZE;}
sub universalDate  {return $DATE_UNI;}
sub autoWordLimit  {return $AUTO_WRD_LMT;}
sub windowRTFSize  {return $RTF_SIZE;}


sub bgcol           {return $BGCOL;}
sub css             {return $TH_CSS;}
sub debug           {return $DEBUG;}



sub getConfiguration {
    my $db = shift;
    try {
        my $st = $db->prepare("SELECT ID, NAME, VALUE FROM CONFIG;");
        $st->execute();

        while ( my @r = $st->fetchrow_array() ) {

            switch ( $r[1] ) {
                case "RELEASE_VER"  { $RELEASE_VER  = $r[2] }
                case "REC_LIMIT"    { $REC_LIMIT    = $r[2] }
                case "TIME_ZONE"    { $TIME_ZONE    = $r[2] }
                case "PRC_WIDTH"    { $PRC_WIDTH    = $r[2] }
                case "SESSN_EXPR"   { $SESSN_EXPR   = $r[2] }
                case "DATE_UNI"     { $DATE_UNI     = $r[2] }
                case "LANGUAGE"     { $LANGUAGE     = $r[2] }
                case "IMG_W_H"      { $IMG_W_H      = $r[2] }
                case "AUTO_WRD_LMT" { $AUTO_WRD_LMT = $r[2] }
                case "FRAME_SIZE"   { $FRAME_SIZE   = $r[2] }
                case "RTF_SIZE"     { $RTF_SIZE     = $r[2] }
                case "THEME"        { $THEME        = $r[2] }
            }

        }
        return &new;
    }
    catch {
        print "<font color=red><b>SERVER ERROR</b></font>:" . $_;
    }
}


sub getTheme {

        switch ($THEME){
            case "Sun"  { $BGCOL = '#D4AF37'; $TH_CSS = "main_sun.css"; }
            case "Moon" { $BGCOL = '#000000'; $TH_CSS = "main_moon.css"; }
            case "Sun"  { $BGCOL = 'green';   $TH_CSS = "main_earth.css"; }
            else{
                # Standard;
                $BGCOL    = '#c8fff8';
                $TH_CSS   = 'main.css';
            }
        }

}

1;