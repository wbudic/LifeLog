#!/usr/bin/env python
print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers
print "<TITLE>CGI script output</TITLE>"
print "<H1>This is my first CGI script</H1>"
print "Hello, world! <br/>"
for i in range(10):
    print i, '<br/>'
print 'Just to show that some stuff is "dynamically" generated server side<br/>'

