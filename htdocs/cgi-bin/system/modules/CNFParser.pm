#!/usr/bin/perl -w
#
# Programed by: Will Budic
# Open Source License -> https://choosealicense.com/licenses/isc/
#
package CNFParser;

use strict;
use warnings;
use Try::Tiny;


our %anons  = ();
our %consts = ();
our @sql    = ();


sub new {
    my $class = shift;
    my $self = {};
    bless $self, $class;
    return $self;
}


sub anons {return %anons}
sub constant {my $s=shift;if(@_ > 0){$s=shift;} return $consts{$s}}
sub constants {return keys %consts}
sub SQLStatments {return @sql}
sub anonsToENV {
    # foreach my $prp (keys %anons){
    #     print "{{",$prp, '=' , $anons{$prp}, "}}\n";
    # }
}


sub parse {
        my ($self, $cnf, $content) = @_;
        open(my $fh, "<:perlio", $cnf ) or die "Can't open $cnf -> $!";
        read $fh, $content, -s $fh;
        close $fh;
try{

    my @tags = ($content =~ m/<<(\w*<(.*?).*?>>)/gs);
    foreach my $tag (@tags){
	  next if not $tag;
      if(index($tag,'<CONST')==0){#constant

            foreach  (split '\n', $tag){
                my @prps = map {
                    s/^\s+\s+$//;  # strip unwanted spaces
                    s/^\"//;      # strip start quote
                    s/\"$//;      # strip end quote
                    s/<const\s//i; # strip  identifier
                    s/\s>>//;
                    $_             # return the modified string
                }
                split /\s*=\s*/, $_;

                my $k;
                foreach (@prps){
                      if ($k){
                            $consts{$k} = $_;
                            undef $k;
                      }
                      else{
                            $k = $_;
                      }
                }
            }

        }
        elsif(index($tag,'CONST<')==0){#multiline constant.
            my $i = index $tag, "\n";
            my $k = substr $tag, 6, $i-6;
            my $v = substr $tag, $i, (rindex $tag, ">>")-$i;
            $consts{$k} = $v;
        }
        else{

            my ($st,$v);
            my @kv = split /</,$tag;
            my $e = $kv[0];
            my $t = $kv[1];
            my $i = index $t, "\n";
            if($i==-1){
               $t = $v = substr $t, 0, (rindex $t, ">>");
            }
            else{
               $v = substr $t, $i, (rindex $t, ">>")-$i;
               $t =  substr $t, 0, $i;
            }

           # print "Ins($i): with $e do $t\n";
           if($t eq 'DATA'){
               $st ="";
               foreach(split /\n/,$v){
                   my $d = $i = "";
                   foreach $d (split /\`/, $_){
                       $t = substr $d, 0, 1;
                       if($t eq '$'){
                          $v =  $d;            #capture spected value.
                          $d =~ s/\$$|\s*$//g; #trim any space and system or constant '$' end marker.
                          if($v=~m/\$$/){
                             $v = $consts{$d}
                          }
                          else{
                             $v = $d;
                          }
                          $i .= "'$v',";
                       }
                       else{
                          #First is always ID a number and '#' signifies number.
                          if(!$i || $t eq "\#") {
                            $i .= "$d,";
                          }
                          else{
                            $i .= "'$d',";
                          }
                       }
                   }
                   $i =~ s/,$//;
                   $st .="INSERT INTO $e VALUES($i);\n" if $i;
               }
            }
            elsif($t eq 'TABLE'){
               $st = "CREATE TABLE $e(\n$v\n);";
            }
            elsif($t eq 'INDEX'){
               $st = "CREATE INDEX $v;";
            }
            elsif($t eq 'VIEW'){
                $st = "CREATE VIEW $v;";
            }
            else{
                #Register application statement as an anonymouse one.
                $anons{$e} = $v;
                next;
            }
            push @sql, $st;#push application statement as SQL one.
        }
	 }

    # foreach my $prp (keys %consts){
    #     print "[[",$prp, '=' , constant($prp), "]]\n";
    # }
    # foreach my $prp (keys %anons){
    #     print "{{",$prp, '=' , $anons{$prp}, "}}\n";
    # }
    # foreach (@sql){
    #     print "$_\n";
    # }

} catch{
      die $_;
}

}
### CGI END
1;
