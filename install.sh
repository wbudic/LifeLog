
sudo apt install libpq-dev
sudo mkdir /usr/include/postgresql
apt install zlib1g-dev



#
# From LifeLog v.3.5 installation is to local user directory if you have latest perl recompiled under your users home.
# And want to develop and test it from latest relases runing user localy, which is recomended. When all works and you are happy
# with latest changes and release, you can then move cgi and files, setup to your system or production server.
# Run this script as user root, if want to install required modules for the whole system.
#
perl -MCPAN -e 'install DBI'
perl -MCPAN -e 'install CGI'
perl -MCPAN -e 'install CGI::Session'
perl -MCPAN -e 'install DBD::SQLite'
perl -MCPAN -e 'install DBD::Pg'
perl -MCPAN -e 'install Exception::Class '
perl -MCPAN -e 'install Syntax::Keyword::Try'
perl -MCPAN -e 'install DateTime::Format::SQLite'
perl -MCPAN -e 'install Capture::Tiny'
perl -MCPAN -e 'install Text::CSV'
perl -MCPAN -e 'install Text::Markdown'
perl -MCPAN -e 'install Regexp::Common'
perl -MCPAN -e 'install Gzip::Faster'
perl -MCPAN -e 'install CGI:Session'
perl -MCPAN -e 'install Crypt::CBC'
perl -MCPAN -e 'install Crypt::Blowfish'
perl -MCPAN -e 'install DateTime'
perl -MCPAN -e 'install DateTime::Format::Human::Duration'
perl -MCPAN -e 'install DateTime::Format::SQLite'
perl -MCPAN -e 'install IO::Compress::Gzip'
perl -MCPAN -e 'install IO::Interactive '
perl -MCPAN -e 'install IO::Prompter'
perl -MCPAN -e 'install IPC::Run'
perl -MCPAN -e 'install JSON'
perl -MCPAN -e 'install Regexp::Common'
perl -MCPAN -e 'install Perl::LanguageServer'
perl -MCPAN -e 'install Log::Log4perl'
perl -MCPAN -e 'install Number::Bytes::Human'
perl -MCPAN -e 'install File::ReadBackwards'

