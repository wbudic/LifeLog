eval {
    require DBI;
    require DBI::DBD;
    die "Too old" unless $DBI::VERSION >= 1.03;
};
use ExtUtils::MakeMaker;
use Config;
use strict;

WriteMakefile(
    'NAME'          => 'DBD::SQLite2',
    'VERSION_FROM'  => 'lib/DBD/SQLite2.pm', # finds $VERSION
    'PREREQ_PM'     => {DBI => 1.21}, # e.g., Module::Name => 1.1
    'OBJECT'        => '$(O_FILES)',
    'INC'           => '-I$(DBI_INSTARCH_DIR)',
    'OPTIMIZE'      => "-O2",
    'DEFINE'        => "-DNDEBUG=1 -DSQLITE_PTR_SZ=$Config{ptrsize}" .
                       ($Config{d_usleep} ? " -DHAVE_USLEEP=1" : ""),
    'clean'         => { FILES => 'SQLite2.xsi config.h' },
);

package MY;
sub postamble { 
  DBI::DBD::dbd_postamble(@_);
}
sub libscan {
    my ($self, $path) = @_;
    ($path =~ m/\~$/) ? undef : $path;
}
