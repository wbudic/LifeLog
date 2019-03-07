https://www.tutorialspoint.com/sqlite/sqlite_perl.htm
set LATEST=1.641
wget http://search.cpan.org/CPAN/authors/id/T/TI/TIMB/DBI-$LATEST.tar.gz
tar xvfz DBI-1.625.tar.gz
cd DBI-1.625
perl Makefile.PL
make
make install

wget http://search.cpan.org/CPAN/authors/id/T/TI/TIMB/DBI-$LATEST.redme.tar.gz

set LATEST=2-.0.33
wget http://search.cpan.org/CPAN/authors/id/M/MS/MSERGEANT/DBD-SQLite$LATEST.tar.gz
$ tar xvfz DBD-SQLite-1.11.tar.gz
$ cd DBD-SQLite-1.11
$ perl Makefile.PL
$ make
$ make install

wget http://search.cpan.org/CPAN/authors/id/M/MS/MSERGEANT/DBD-SQLite$LATEST.readme.tar.gz
