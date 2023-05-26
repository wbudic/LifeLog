package MarkdownPlugin;

use strict;
use warnings;
use Syntax::Keyword::Try;
use Exception::Class ('MarkdownPluginException');
use feature qw(signatures);
use Date::Manip;

our $TAB = ' 'x4;

sub new ($class, $fields={Language=>'English',DateFormat=>'US'}){      

    if(ref($fields) eq 'REF'){
       warn "Hash reference required as argument for fields!"
    }
    my $lang =   $fields->{'Language'};
    my $frmt =   $fields->{'DateFormat'};
    Date_Init("Language=$lang","DateFormat=$frmt");            
    $fields->{'disk_load'} = 0 if not exists $fields->{'disk_load'};
   
    return bless $fields, $class
}

###
# Process config data to contain expected fields and data.
###
sub convert ($self, $parser, $property) {    
try{    
    my ($item, $script) =  $parser->anon($property);
    die "Property not found [$property]!" if !$item;

    my $ref = ref($item); my $escaped = 0;
    if($ref eq 'CNFNode'){
       $script = $item->{script}  
    }elsif($ref eq 'InstructedDataItem'){
       $script = $item->{val};
       $escaped = $item->{ins} eq 'ESCAPED'
    }elsif($script !~ /\n/ and -e $script ){
        my $file = $parser->anon($property);
        $script = do {
        open my $fh, '<:encoding(UTF-8)', $script or MarkdownPluginException->throw("File not avaliable: $script");
        local $/;
        <$fh>;    
        };
    }
    if($escaped){        
        $script =~ s/\\</</gs;
        $script =~ s/\\>/>/gs;
        #$script =~ s/\n/<br>/gs;
    }
    my @doc = @{parse($self,$script)};
    $parser->data()->{$property} =  $doc[0];
    $parser->data()->{$property.'_headings'} = $doc[1];
   
}catch($e){
        MarkdownPluginException->throw(error=>$e ,show_trace=>1);
}}



sub parse ($self, $script){
try{
    my ($buffer, $para, $ol, $lnc); 
    my @list; my $ltype=0;  my $nix=0;my $nplen=0;
    my @titels;my $code = 0; my $tag;  my $pml_val = 0;  my $bqoute;my $bqoute_nested;
    $script =~ s/^\s*|\s*$//;    
    foreach my $ln(split(/\n/,$script)){        
        $ln =~ s/\t/$TAB/gs;  
        $lnc++;
        if($ln =~ /^```(\w*)/){
            my $class = $1;         
            if($1){
               $tag = $1;
               if($tag eq 'html' or $tag eq 'CNF' or $tag eq 'code' or $tag eq 'perl'){
                  $class = $tag;
                  $tag = 'div';
               }else{
                  $tag = 'pre' if($tag eq 'sh' or $tag eq 'bash');
               }
               if($tag eq 'perl'){
                  $class='perl'; 
                  $tag  ='div';                                   
               }
            }elsif(!$tag){
               $tag = $class = 'pre';
            }
            if($code){
               if($para){ 
                  $buffer .= "$para\n"
               }
               $buffer .= "</$tag><br>"; $tag = $para = "";
               $code = 0;
            }else{
               $buffer .= "<$tag class='$class'>"; 
               if($class eq 'perl'){
                  $buffer .= qq(<h1><span>$class</span></h1>);
                  $code = 2;
                }else{
                  if($class eq 'CNF' or $class eq 'html'){
                     $buffer .= qq(<h1><span>$class</span></h1>);
                  }
                  $code = 1
                }
            }
        }elsif(!$code && $ln =~ /^\s*(#+)\s*(.*)/){
            my $h = 'h'.length($1);
            my $title = $2; 
            $titels[@titels] = {$lnc,$title};
            $buffer .= qq(<$h>$title</$h><a name=").scalar(@titels)."\"></a>\n"
        }
        elsif(!$code &&  ($ln =~ /^(\s+)(\d+)\.\s(.*)/ || $ln =~ /^(\s*)([-+*])\s(.*)/)){
            my @arr;
            my $spc = length($1);
            my $val = ${style($3)};
            $ltype  = $2 =~ /[-+*]/ ? 1:0;            
            if($spc>$nplen){            
               $nplen = $spc;               
               $list[@list] = \@arr;
               $nix++;
            }elsif($spc<$nplen){
               $nix--; 
            }
            if($list[$nix-1]){
                @arr = @{$list[$nix-1]};                        
                $arr[@arr] = $ltype .'|'.$val;
                $list[$nix-1] = \@arr;
            }else{
                $arr[@arr] = $ltype .'|'.$val;
                $list[@list] = \@arr;
            }            
        }elsif(!$code && $ln =~ /(^|\\G)[ ]{0,3}(>+) ?/){
            my $nested = length($2);
            $ln =~ s/^\s*\>+//;
            if(!$bqoute_nested){
                $bqoute_nested = $nested;
                $bqoute .="<blockquote><p>\n"
            }elsif($bqoute_nested<$nested){
                $bqoute .="</p><blockquote><p>";
                $bqoute_nested = $nested;
            }elsif($bqoute_nested>$nested){
                $bqoute .="</p></blockquote><p>";
                $bqoute_nested--;
            }
            if($ln !~ /(.+)/gm){
               $bqoute .= "\n</p><p>\n"
            }else{
               $bqoute .= ${style($ln)}."</br>";
            }
            
        }
        elsif(!$code && $ln =~ /^\s*\*\*\*/){
            if($para){
                $para .= qq(<hr>\n)
            }else{
                $buffer .= qq(<hr>\n)
            }
        }
        elsif($ln =~ /^\s*(.*)/ && length($1)>0){
            if($code){
                 my $v=$1;
                if($tag eq 'pre' && $code == 1){
                    $v =~ s/</&#60;/g;
                    $v =~ s/>/&#62;/g;
                    $para .= "$v\n"; 
                }elsif($code == 2){
                    $v =~ s/([,;=\(\)\{\}\[\]]|->)/<span class=opr>$1<\/span>/g;
                    $v =~ s/(['"].*['"])/<span class='str'>$1<\/span>/g;
                    $v =~ s/class=opr/class='opr'/g;
                    $v =~ s/(my|our|local|use|lib|require|new|while|for|foreach|while|if|else|elsif)/<span class='bra'>$1<\/span>/g;                    
                    $v =~ s/(\$\w+)/<span class='inst'>$1<\/span>/g;                    
                    $para .= "$v<br>\n";
                }else{                   
                    
                    $v =~ m/ ^(<<)  ([@%]<) ([\$@%]?\w+) ([<>])
                            |^(<{2,3})                          
                                ([\$@%\w]+)
                                      (<[\w\ ]*>)* 
                            |(>{2,3})$
                           /gx;# and my @captured = @{^CAPTURE};

                    if($5&&$6&&$7){
                        my $t = $5;
                        my $v = $6;
                        my $i = $7;
                        $i =~ m/^<([\$@%\w]+?)>$/;
                        $i = $1; $pml_val = 1;                       
                        $para .= qq(<span class='bra'>&#60;&#60;</span><span class='var'>$v</span><span class='bra'>&#60;</span><span class='inst'>$i</span><span class='bra'>&#62;</span><br>);
                       
                    }elsif($5&&$6){
                         my $t = $5;
                         my $i = $6;
                         $t =~ s/</&#60;/g; $pml_val = 1;
                        $para .= qq(<span class='bra'>$t</span><span class='inst'>$i</span><br>
                                );

                    }elsif($1 && $2 && $3){
                        
                        $pml_val = 1;
                        $para .= qq(<span class='bra'>&#60;&#60;$2<\/span><span class='var'>$3</span><span class='bra'>&#62;<\/span><br>);

                       
                    }elsif($8){
                        my $t = $8; 
                        $t =~ s/>/&#62;/g;  $pml_val = 0;
                        $para .= "<span class='bra'>$t</span><br>\n";
                    }
                    else{
                        if($pml_val){
                            $v =~ m/(.*)([=:])(.*)/gs;
                            if($1&&$2&&$3){
                                $para .= "<span class='var'>$1</span> <span class='bra'>$2</span> <span class='val'>$3</span> <br>\n";
                            }else{
                                $para .= " <span class='val'>$v</span><br>\n";
                            }
                        }else{
                            $para .= "$v<br>\n";
                        }
                    }
                }
                
            }else{
                if($bqoute){
                    while($bqoute_nested-->0){$bqoute .="</p></blockqoute>\n"}
                    $para   .= $bqoute;
                    undef $bqoute;
                }
                $para .= ${style($1)}."\n"         
            }
        }else{            
            if(@list){
                if($para){
                   my @arr;
                   if($list[$nix-1]){
                        @arr = @{$list[$nix-1]};
                        $arr[@arr] = '2|'.$para;
                        $list[$nix-1] = \@arr; 
                   }else{
                        $arr[@arr] = '2|'.$para;
                        $list[@list] = \@arr;
                   }
                   $para=""
                }
               $buffer .= createList(0,$ltype,\@list);
               undef @list; $nplen = 0
            }
            elsif($para){
               if($code){
                    $buffer .= $para;
               }else{
                $buffer .= qq(<p>$para</p><br>\n);
               }
               $para=""
            }else{
               #$buffer .= qq(<br>\n);
            }
        }
    }

    if($bqoute){
        while($bqoute_nested-->0){$bqoute .="\n</p></blockquote>\n"}
        $buffer .= $bqoute;        
    }

    $buffer .= createList(0,$ltype,\@list) if(@list);
    $buffer .= qq(<p>$para</p>\n) if $para;    

return [\$buffer,\@titels]
}catch($e){
        MarkdownPluginException->throw(error=>$e ,show_trace=>1);
}}

my @LIST_ITEM_TYPE = ('ol','ul','blockquote');

sub createList ($nested,$type,@list){
    $nested++;
    my ($bf,$tabs) =("", " "x$nested);
    my $tag = $LIST_ITEM_TYPE[$type];

    foreach my $arr(@list){
            $bf .= qq($tabs<$tag>\n) if $nested>1;
            foreach my $li(@$arr){
                if(ref($li) eq 'ARRAY'){
                    $bf =~ s/\s<\/($tag)>\s$//gs if $bf;
                    my $r = $1;
                    my @lst = \@$li;
                    my $typ = get_list_type(@lst);
                    $bf .= createList($nested,$typ,@lst);
                    $bf .= qq($tabs</$tag>\n) if($r)                    
                }else{
                    $li =~ s/^(\d)\|//;
                    if($1 == 2){
                        $bf .= "$tabs<blockquote>$li</blockquote>\n"
                    }else{
                        $bf .= "$tabs<li>$li</li>\n"
                    }
                }
            }
            $bf .= qq($tabs</$tag>\n) if $nested>1;
    }
    return $bf
}

sub get_list_type (@list){
    foreach my $arr(@list){
        foreach my $li(@$arr){
            if($li =~ /^(\d)|/){
                return $1;
            }
            last;
        }
    }
    return 0;
}

sub style ($script){
    MarkdownPluginException->throw(error=>"Invalid argument passed as script!",show_trace=>1) if !$script;
    #Links <https://duckduckgo.com>
    $script =~ s/<(http[:\/\w.]*)>/<a href=\"$1\">$1<\/a>/g;
        
    my @result = map {
        s/\*\*(.*)\*\*/\<em\>$1<\/em\>/;
        s/\*(.*)\*/\<strong\>$1<\/strong\>/;
        s/__(.*)__/\<del\>$1<\/del\>/;
        s/~~(.*)~~/\<strike\>$1<\/strike\>/;        
        $_
    } split(/\s/,$script); 
    
    my $ret = join(' ',@result);    
    #Images
    $ret =~ s/!\[(.*)\]\((.*)\)/\<div class="div_img"><img class="md_img" src=\"$2\"\ alt=\"$1\"\/><\/div>/;
    #Links [Duck Duck Go](https://duckduckgo.com)
    $ret =~ s/\[(.*)\]\((.*)\)/\<a href=\"$2\"\>$1\<\/a\>/;
    return \$ret;
}

#




1;