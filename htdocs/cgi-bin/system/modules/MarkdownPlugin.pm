package MarkdownPlugin;

use strict;
use warnings;
use Syntax::Keyword::Try;
use Exception::Class ('MarkdownPluginException');
use feature qw(signatures);
use Date::Manip;
##no critic ControlStructures::ProhibitMutatingListFunctions

our $TAB = ' 'x4;
our $PARSER;

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
    $PARSER = $parser;
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


package HTMLListItem {    
    sub new{
        my $class = shift;
        my ($type,$item,$spc) = @_;
        my @array = ();
        return bless{type=>$type,item=>$item,spc=>$spc,list=>\@array},$class;
    }
    sub parent($self) {
        return  exists($self->{parent}) ? $self->{parent} : undef
    }
    sub add($self, $item){
        push @{$self->{list}}, $item;        
        $item ->{parent} = $self;
    }    
    sub hasItems($self){        
        return @{$self->{list}}>0
    }
    sub toString($self){        
        my $t = $self->{type};
        my $isRootItem = $self -> {spc} == 0 ? 1 : 0;
        my $hasItems   = $self->hasItems()   ? 1 : 0;
        my $ret = "<li>".$self -> {item}."</li>\n";  
        if($hasItems){
           $ret = "<li>".$self -> {item}."<$t>\n";
        }
        foreach my $item(@{$self->{list}}){
            if($item->hasItems()){
                $ret .= $item->toString()."\n"
            }else{
                $ret .= '<li>'.$item->{item}."</li>\n"
            }
        }
        if($hasItems){
           $ret .= "</$t></li>\n";
        }
        return $ret
    }
}

sub setCodeTag($tag, $class){
    if($tag){
        $tag = lc $tag;        
        if($tag eq 'html' or $tag eq 'cnf' or $tag eq 'code' or $tag eq 'perl'){
            $class = $tag;
            $tag = 'div';
        }else{
            $tag = 'pre' if($tag eq 'sh' or $tag eq 'bash');
        }
        if($tag eq 'perl'){
            $class='perl'; 
            $tag  ='div';                                   
        }
    }else{
        $tag = $class = 'pre';
    }
    return [$class, $tag]
}

sub parse ($self, $script){
try{
    my ($buffer, $para, $ol, $lnc); 
    my @list; my $ltype=0;  my $nix=0; my $nplen=0; my $list_item;
    my @titels;my $code = 0; my ($tag, $class);  my $pml_val = 0;  my ($bqte, $bqte_nested,$bqte_tag);
    $script =~ s/^\s*|\s*$//;
    foreach my $ln(split(/\n/,$script)){        
        $ln =~ s/\t/$TAB/gs;  
        $lnc++;
        if($ln =~ /^```(\w*)\s(.*)```$/g){
            $tag = $1;
            $ln  = $2;
            my @code_tag = @{ setCodeTag($tag, "") }; 
            $buffer .= qq(<$code_tag[1] class='$code_tag[0]'>$ln</$code_tag[1]>\n);
            next
        }elsif($ln =~ /^\s*```(\w*)/){
            if(!$tag){
                my @code_tag = @{ setCodeTag($1, $1) };
                $class = $code_tag[0];         
                $tag = $code_tag[1] if !$tag;
            }
            if($code){
               if($para){ 
                  $buffer .= "$para\n"
               }
               $buffer .= "</$tag><br>"; undef $para;
               $code = 0; undef $tag;
            }else{
               $buffer .= "<$tag class='$class'>"; 
               if($class eq 'perl'){
                  $buffer .= qq(<h1><span>$class</span></h1>);
                  $code = 2;
                }else{
                  if($class eq 'cnf' or $class eq 'html'){
                     $buffer .= '<h1><span>'.uc $class.'</span></h1>'
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
        elsif(!$code &&  ($ln =~ /^(\s*)(\d+)\.\s(.*)/ || $ln =~ /^(\s*)([-+*])\s(.*)/)){
            
            my $spc = length($1);
            my $val = $3 ? ${style($3)} : "";
            my $new = HTMLListItem->new((/[-+*]/?'ul':'ol'), $val, $spc);

            if(!$list_item){                
                $list_item = $new;
                $list[@list] = $list_item;
                $nplen = $spc;
                
            }elsif($spc>$nplen){                
                $list_item -> add($new);                
                $list_item = $new;
                $nplen = $spc;
                
            }else{                
               while($list_item->{spc}>=$spc && $list_item -> parent()){
                     $list_item = $list_item -> parent();
               }                
               if ( !$list_item ){$list_item = $new}else{
                     $list_item -> add($new);
                     $list_item = $new;                
               }
            }
        }elsif(!$code && $ln =~ /(^|\\G)[ ]{0,3}(>+) ?/){
            my $nested = length($2);
             $ln =~ s/^\s*\>+//;
            ($ln =~ /^(\s+)   (\d+) \.\s (.*)/x || $ln =~ /^(\s*) ([-+*]) \s(.*)/x);
            if($2 && $2 =~ /[-+*]/){
                $bqte_tag = "ul";
            }elsif($2){
                $bqte_tag = "ol";
            }else{
                $bqte_tag = "p";
            }
            if(!$bqte_nested){
                $bqte_nested = $nested;
                $bqte .="<blockquote><$bqte_tag>\n"
            }elsif($bqte_nested<$nested){
                $bqte .="</$bqte_tag><blockquote><$bqte_tag>";
                $bqte_nested = $nested;
            }elsif($bqte_nested>$nested){
                $bqte .="</$bqte_tag></blockquote><$bqte_tag>";
                $bqte_nested--;
            }
            if($ln !~ /(.+)/gm){
               $bqte .= "\n</$bqte_tag><p>\n"               
            }else{
                if($bqte_tag eq 'p'){
                   $ln =~ s/^\s*//g;
                   $bqte .= ${style($ln)}."</br>";
                }else{
                   $ln =~ s/^\s*[-+*]\s*|^\s*\d+\.\s*//g; 
                   $bqte .= "<li>".${style($ln)}."</li>\n"; 
                }
            }            
        }
        elsif(!$code && $ln =~ /^\s*\*\*\*/){
            if($para){
                $para   .= qq(<hr>\n)
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
                    $para .= code2HTML($v)."<br>\n";
                }else{           


                    $v =~ m/  ^(<{2,3}) ([\$@%]*\w*)$ 
                            | ^(>{2,3})$
                            | (<<) ([\$@%]*\w*) <(\w+)>
                     /gx;

                    if($1&&$2){
                        my $t = $1;  
                        my $i = $2;  
                        $t =~ s/</&#60;/g;                      
                        $para .= qq(<span class='bra'>$t</span><span class='ins'>$i</span><br>);
                        $pml_val = 1;
                        next;
                        
                    }elsif($3){
                        my $t = $3; 
                        $t =~ s/>/&#62;/g;  
                        $para .= "<span class='bra'>$t</span><br>\n";
                        $pml_val = 0;
                        next;
                    }elsif($4&&$5&&6){
                        my $t = $4;   
                        my $v = $5;
                        my $i = $6;
                        $t =~ s/</&#60;/g;
                        $para .= qq(<span class='bra'>$t</span><span class='var'>$v</span>
                                    <span class='bra'>&#60;</span><span class='ins'>$i</span><span class='bra'>&#62;</span><br>);
                        $pml_val = 1;
                        next;

                    }
                    
                    $v =~ m/ ^(<<)  ([@%]<) ([\$@%]?\w+) ([<>])
                            |^(<{2,3})                          
                                ([\$@%\w]+)\s*
                                      <*([^>]+)
                              (>{2,3})$
                            
                           /gx;# and my @captured = @{^CAPTURE};
                    
                    if($5&&$6&&$7&&$8){
                        my $t = $5;
                        my $v = $6;
                        my $i = $7;
                        my $c = $8;
                        $t =~ s/</&#60;/g;
                        $c =~ s/>/&#62;/g;
                        $pml_val = 1;                       
                        $para .= qq(<span class='bra'>$t</span><span class='var'>$v</span><span class='bra'>&#60;</span><span class='inst'>$i</span><span class='bra'>$c</span><br>);
                       
                    }elsif($5&&$6){
                        my $t = $5;
                        my $i = $6;
                        $t =~ s/</&#60;/g; $pml_val = 1;
                        $para .= qq(<span class='bra'>$t</span><span class='inst'>$i</span><br>);

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
                if($bqte){
                    while($bqte_nested-->0){$bqte .="</$bqte_tag></blockqoute>\n"}
                    $para   .= $bqte;
                    undef $bqte;
                }
                $para .= ${style($1)}."\n"         
            }
        }else{            
            
            if(@list){
                $buffer .= "<".$list[0]->{type}.">\n"; #This is the root list type, it can only be one per item entry.
                foreach (@list){
                $buffer .= $_->toString()."\n";    
                }
                $buffer .= "</".$list[0]->{type}.">\n";
                undef @list
            }
            elsif($para){
               if($code){
                    $buffer .= $para;
               }else{
                $buffer .= qq(<p>$para</p><br>\n);
               }
               $para=""
            }
        }
    }

    if($bqte){
        while($bqte_nested-->0){$bqte .="\n</$bqte_tag></blockquote>\n"}
        $buffer .= $bqte;        
    }
    
    if(@list){
        $buffer .= "<".$list[0]->{type}.">\n"; #This is the root list type, it can only be one per item entry.
        foreach my$item(@list){
        $buffer .= $item->toString()."\n";    
        }
        $buffer .= "</".$list[0]->{type}.">\n";
    }
    $buffer .= qq(<p>$para</p>\n) if $para;    

return [\$buffer,\@titels]
}catch($e){
        MarkdownPluginException->throw(error=>$e ,show_trace=>1);
}}

sub code2HTML($v){
        $v =~ s/([,;=\(\)\{\}\[\]]|->)/<span class='opr'>$1<\/span>/g;
        $v =~ s/(['"].*['"])/<span class='str'>$1<\/span>/g;        
        $v =~ s/(my|our|local|use|lib|require|new|while|for|foreach|while|if|else|elsif)/<span class='bra'>$1<\/span>/g;                    
        $v =~ s/(\$\w+)/<span class='inst'>$1<\/span>/g;
        return $v
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

    #Inline code
    $ret =~ m/```(.*)```/g;
    if($1){
        my $v = $1; 
           $v =~ m/ ^(<<)  ([@%]<) ([\$@%]?\w+) ([<>])
                            |^(<{2,3})                          
                                ([^>]+)
                                    ( (<[\W\w ]*>) | (>{2,3})$ )
                /gx;
            if($5&&$6&&$7){
                my $t = $5;
                   $v = $6;
                my $c = $7;
                $t =~ s/</&#60;/g; 
                $c =~ s/>/&#62;/g;
                $v=~m/^(\w+)/;
                my $w = $1; 
                
                if($PARSER->isReservedWord($w)){
                    $v =~ s/^(\w+)/<span class='inst'>$w<\/span>/;

                }
                $v = qq(<span class='bra'>$t</span><span class='var'>$v</span></span><span class='bra'>$c</span>);                
                
            }elsif($5&&$6){
                my $t = $5;
                my $i = $6;
                my $c = $7; $c = $8 if !$c;
                $t =~ s/</&#60;/g; 
                $c =~ s/>/&#62;/g if $c;
                $v = qq(<span class='bra'>$t</span><span class='inst'>$i</span>$c);
            }            
            elsif($1 && $2 && $3){
                $v = qq(<span class='bra'>&#60;&#60;$2<\/span><span class='var'>$3</span><span class='bra'>&#62;<\/span>);
                
            }
        $ret =~ s/```(.*)```/\<span\>$v<\/span\>/;         
    }
    
    #Images
    $ret =~ s/!\[(.*)\]\((.*)\)/\<div class="div_img"><img class="md_img" src=\"$2\"\ alt=\"$1\"\/><\/div>/;
    #Links [Duck Duck Go](https://duckduckgo.com)
    $ret =~ s/\[(.*)\]\((.*)\)/\<a href=\"$2\"\>$1\<\/a\>/;
    return \$ret;
}

#




1;