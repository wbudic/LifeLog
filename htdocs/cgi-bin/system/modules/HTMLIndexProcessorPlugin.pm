package HTMLIndexProcessorPlugin;

use strict;
use warnings;
no warnings qw(experimental::signatures);
use Syntax::Keyword::Try;
use Exception::Class ('HTMLIndexProcessorPluginException');
use feature qw(signatures);
use Scalar::Util qw(looks_like_number);
use Clone qw(clone);
use CGI;
use CGI::Session '-ip_match';

use constant VERSION => '1.0';

our $TAB = ' 'x4;

sub new ($class, $plugin){
    my $settings;
    if($plugin){
       $settings = clone $plugin; #clone otherwise will get hijacked with blessings.
    }
    return bless $settings, $class
}

###
# Process config data to contain expected fields and data.
###
sub convert ($self, $parser, $property) {
    my ($buffer,$title, $link, $body_attrs, $body_on_load, $give_me);
    my $cgi          = CGI -> new();
    my $cgi_action   = $cgi-> param('action');
    my $cgi_doc      = $cgi-> param('doc');
    my $tree         = $parser-> anon($property);
    die "Tree property '$property' is not available!" if(!$tree or ref($tree) ne 'CNFNode');
try{
    #TODO 20231002 Move -> %WEBAPP_SETTINGS into utility.
    my %THEME;
    my %wsettings = $parser -> collection('%WEBAPP_SETTINGS');
    if(%wsettings){
       my $theme = $wsettings{THEME};
       my @els = split(/, /, $theme);
       foreach (@els) {
         my ($key,$val) = split(/\s*=>\s*/, $_);
         $THEME{$key} = $val;
         last if $key eq 'css'
       }
       my $theme_file = $wsettings{LOG_PATH}.'current_theme';
       $theme_file =~ /^\.\.\/\.\.\// if(-e $theme_file);
       if(-e $theme_file){
         open my $fh, '<', $theme_file;
         my $theme = <$fh>;
         close($fh);
         if($theme =~ m/standard/i){
            $THEME{css} = "wsrc/main.css"
         }elsif($theme =~ m/moon/i){
            $THEME{css} = "wsrc/main_moon.css"
         }
         elsif($theme =~ m/sun/i){
            $THEME{css} = "wsrc/main_sun.css"
         }
         elsif($theme =~ m/earth/i){
            $THEME{css} = "wsrc/main_earth.css"
         }
       }
    }

    if (exists $parser->{'HTTP_HEADER'}){
        $buffer .= $parser-> {'HTTP_HEADER'};
    }else{
        if(exists $parser -> collections()->{'%HTTP_HEADER'}){
            my %http_hdr = $parser -> collection('%HTTP_HEADER');
            $buffer = $cgi->header(%http_hdr);
        }
    }
    if ($cgi_action and $cgi_action eq 'load'){
        $buffer .= $cgi->start_html(); my
        $load = loadDocument($parser, $cgi_doc);
        if($load){
           $buffer .= $$load if $load;
        }else{
           $buffer .= "Document is empty: $cgi_doc\n"
        }
    }else{
        $title  = $tree  -> {'Title'} if exists $tree->{'Title'};
        $link   = $tree  -> {'HEADER'};
        $body_attrs   = $tree -> {'Body'} if exists $tree -> {'Body'};
        $body_on_load = $tree -> {'OnLoad'} if exists $tree -> {'OnLoad'};
        $body_on_load = "onBodyLoadGeneric()" if !$body_on_load;
        my (@hhshCSS,@hhshJS);
        if($link){
        if(ref($link) eq 'CNFNode'){
                my $arr = $link->find('CSS/@@');
                foreach (@$arr){
                    if($THEME{css} && $_->val() =~ /main.css$/){
                        push  @hhshCSS, {-type => 'text/css', -src => $THEME{css}};
                    }else{
                        push  @hhshCSS, {-type => 'text/css', -src => $_->val()};
                    }
                }
                $arr = $link->find('JS/@@');
                foreach (@$arr){
                    push  @hhshJS, {-type => 'text/javascript', -src => $_->val()};
                }
                $arr = $link  -> find('STYLE');
                if(ref($arr) eq 'ARRAY'){
                    foreach (@$arr){
                        $give_me .= "\n<style>\n".$_ -> val()."\n</style>\n"
                    }}else{
                        $give_me .= "\n<style>\n".$arr -> val()."\n</style>\n"
                }
                $arr = $link  -> find('SCRIPT');
                if(ref($arr) eq 'ARRAY'){
                    foreach (@$arr){
                        my $attributes = _nodeHTMLAtrributes($_);
                        $give_me .= "\n<script$attributes>\n".$_ -> val()."\n</script>\n"
                    }}else{
                        my $attributes = _nodeHTMLAtrributes($arr);
                        $give_me .= "\n<script$attributes>\n".$arr -> val()."\n</script>\n";

                }
        }
        delete $tree -> {'HEADER'};
        }
        $buffer .= $cgi->start_html(
                            -title   => $title,
                            -onload  => $body_on_load,
                            # -BGCOLOR => $colBG,
                            -style   => \@hhshCSS,
                            -script  => \@hhshJS,
                            -head=>$give_me,
                            $body_attrs
                        );
        foreach my $node($tree->nodes()){
        $buffer .= build($parser, $node)  if $node;
        }
        $buffer .= $cgi->end_html();
    }
    $parser->data()->{$property} = \$buffer;
 }catch($e){
         HTMLIndexProcessorPluginException->throw(error=>$e);
 }
}

sub _nodeHTMLAtrributes {
    my $node = shift;
    my $attributes =" ";
    my @attrs = $node -> attributes();
    foreach my $a(@attrs){
        $attributes .= @$a[0] . " = \"" .@$a[1]."\""
    }
    $attributes = "" if $attributes eq " ";
    return $attributes
}
#
sub loadDocument($parser, $doc) {
    my $slurp = do {
                    open my $fh, '<:encoding(UTF-8)', $doc or HTMLIndexProcessorPluginException->throw(error=>"Document not avaliable -> \"$doc\" ", show_trace=>1);
                    local $/;
                    <$fh>;
    };
    if($doc =~/\.md$/){
        require MarkdownPlugin;
        my @r = @{MarkdownPlugin->new(undef)->parse($slurp)};
        return $r[0];
    }
    return \$slurp
}

###
# Builds the html version out of a CNFNode.
# CNFNode with specific tags here are converted also here,
# those that are out of the scope for normal standard HTML tags.
# i.e. HTML doesn't have row and cell tags. Neither has meta links syntax.
###
sub build {
    my $parser = shift;
    my $node = shift;
    my $tabs = shift; $tabs = 0 if !$tabs;
    my $bf;
    my $name = lc $node->name();
    if(isParagraphName($name)){
        $bf .= "\t"x$tabs."<div".placeAttributes($node).">\n"."\t"x$tabs."<div>";
            foreach my $n($node->nodes()){
                if($n->{'_'} ne '#'){
                    my $b = build($parser, $n, $tabs+1);
                    $bf .= "$b\n" if $b;
                }
            }
            if($node->{'#'}){
                my $v = $node->val();
                $v =~ s/\n\n+/\<\/br>\n/gs;
                $bf .= "\t<div>\n\t<p>\n".$v."</p>\n\t</div>\n";
            }
        $bf .= "\t</div>\t</div>\n"
    }elsif( $name eq 'row' || $name eq 'cell' ){
        $bf .=  "\t"x$tabs."<div class=\"$name\"".placeAttributes($node).">\n";
            foreach my $n($node->nodes()){
                if($n->{'_'} ne '#'){
                    my $b = build($parser,$n,$tabs+1);
                    $bf .= "$b\n" if $b;
                }
            }
        $bf .= $node->val()."\n" if $node->{'#'};
        $bf .= "\t"x$tabs."</div>"
    }elsif( $name eq 'img' ){
        $bf .= "\t\t<img".placeAttributes($node)."/>\n";
    }elsif($name eq 'list_images'){
        my $paths = $node->{'@@'};
        foreach my $ndp (@$paths){
            my $path = $ndp -> val();
            my @ext = split(',',"jpg,jpeg,png,gif");
            my $exp = " ".$path."/*.". join (" ".$path."/*.", @ext);
            my @images = glob($exp);
            $bf .= "\t<div class='row'><div class='cell'><b>Directory: $path</b></div></div>";
            foreach my $file(@images){
                ($file=~/.*\/(.*)$/);
                my $fn = $1;
                my $enc = "img@".ShortLink::obtain($file);
                $bf .= qq(\t<div class='row'><div class='cell'>);
                $bf .= qq(\t<a href="$enc"><img src="$enc" with='120' height='120'><br>$fn</a>\n</div></div>\n);
            }
        }
    }elsif($name eq '!'){
      return "<!--".$node->val()."-->\n";

    }elsif($node->{'*'}){ #Links are already captured, in future this might be needed as a relink from here for dynamic stuff?
            my $lval = $node->{'*'};
            if($name eq 'file_list_html'){ #Special case where html links are provided.
                foreach(split(/\n/,$lval)){
                     $bf .= qq( [ $_ ] |) if $_
                }
                $bf =~ s/\|$//g;
            }else{ #Generic included link value.
                #is there property data for it?
                my $prop = $parser->data()->{$node->name()};
                #if not has it been passed as an page constance?
                $prop = $parser -> {$node->name()} if !$prop;
                if ( !$prop ) {
                    if   ( $parser->{STRICT} ) { die "Not found as property link -> " . $node->name()}
                    else                       { warn "Not found as property link -> " . $node->name()}
                }
                if($prop){
                    my $ref = ref($prop);
                    if($ref eq "SCALAR"){
                        $bf .= $$prop;
                    }else{
                        $bf .= $prop;
                    }
                }else{
                    $bf .= $lval;
                }
            }
    }
    else{
        my $spaced = 1;
           $bf .= "\t"x$tabs."<".$node->name().placeAttributes($node).">";
            foreach my $n($node->nodes()){
                    my $b = build($parser, $n,$tabs+1);
                        if ($b){
                            if($b =~/\n/){
                               $bf =~ s/\n$//gs;
                               $bf .= "\n$b\n"
                            }else{
                               $spaced=0;
                               $bf .= $b;
                            }
                       }
            }

        if ($node->{'#'}){
            $bf .= $node->val();
            $bf .= "</".$node->name().">";
        }else{
            $bf .= "\t"x$tabs if $spaced;
            $bf .= "</".$node->name().">";
            $bf .= "\n" if !$spaced;
        }

    }
           $bf =~ s/\n\n/\n/gs;
    return $bf;
}
#


sub placeAttributes {
    my $node = shift;
    my $ret  = "";
    my @attr = $node -> attributes();
    foreach (@attr){
        if(@$_[0] ne '#' && @$_[0] ne '_'){
           if(@$_[1]){
              $ret .= " ".@$_[0]."=\"".@$_[1]."\"";
           }else{
              $ret .= " ".@$_[0]." ";
           }
        }
    }
    return $ret;
}

sub isParagraphName {
    my $name = shift;
    return $name eq 'p' || $name eq 'paragraph' ? 1 : 0
}

1;

=begin copyright
Programed by  : Will Budic
EContactHash  : 990MWWLWM8C2MI8K (https://github.com/wbudic/EContactHash.md)
Source        : https://github.com/wbudic/PerlCNF.git
Documentation : Specifications_For_CNF_ReadMe.md
    This source file is copied and usually placed in a local directory, outside of its repository project.
    So it could not be the actual or current version, can vary or has been modiefied for what ever purpose in another project.
    Please leave source of origin in this file for future references.
Open Source Code License -> https://github.com/wbudic/PerlCNF/blob/master/ISC_License.md
=cut copyright