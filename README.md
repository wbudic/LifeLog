# Life Log

Web Application that keeps an everyday CGI accessible log of database entries of various categories.
Preferably on a small inexpensive server connected to your local network.

Written in Perl, easy to implement and modify.

Latest  stable version is **2.2** in **SUN** stage, requiring some Perl knowledge to install and enable, tweak. The main application sources are located in the ../htdocs/cgi-bin directory. Current unstable, development ver. 1.6 is in the GIT branch. The development and features are stable progressive, starting from Moon, Sun and finally Earth stable stage. This application was and is usable since its Moon stage.

https://www.sqlite.org/index.html database is required to run this web application. Note this isn't a full on blown database server requirment, that runs in your background and uses your computers resources.

## PC Requirements

* Any Operating System
* Processor Celeron 1.2+ GHZ or any better, 2+ cores.
* RAM from 2 GB+, to allow for OS. For this application 125KB+ reserved, is recommended.

## Life Log version v.2.+

* Mulitple SQL database support ready and tested, currently ProgreSQL, LightSQL (default).
* Data searches, views, updated, enhanced and upgraded.
* Migration upgraded and test.
* Cross version releases, automatic migration of data and structures.
* Tested and provided also now installation instruction for HTTPS based webserver lighty.
* Tested and working now on ubuntu, debian and mint distros.
  
## Life Log version v.1.8 

* Automated install module script **`./install_modules.sh `**
* Has Secure Backup/Restore. Providing accurate full data restore and merging with existing for live databases.
* Now with a distinct data page and view mode.
* New category selection, storing approuch.
* Better and more efficient application configuration and setup.
* Numerous fixes, and better exception handling.

## Life Log version 1.7

* Views updated, having option to exlude by category now, during the session logging.
* New system configuration options. i.e. $DEBUG for some sql statements.
* Server system based snapshot logs, on stats invocation.
* Server indentifier on login.

## Life Log version 1.5+

* Ritch Text Documents can be attached to Logs.
* Theme support. Change the look and feel. From the congiguration page.
* Expenses and Income totals, various new calculations.
* LTags inclusion, format and output better information.
* Better interactivity.

![Sample](VS-on-METABOX-42.png)



![Sample](VS-on-METABOX-34.png)


