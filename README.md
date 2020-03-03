# LifeLog


Web Application that keeps an everyday CGI accessible log of database entries of various categories.
Preferably on a small inexpensive server connected to your local network.

Written in Perl, easy to implement and modify.

Latest  version is **1.8 release** in **Sun** stable stage, requiring some Perl knowledge to install and enable, tweak. The main application sources are located in the ../htdocs/cgi-bin directory. Current unstable, development ver. 1.6 is in the GIT branch. The development and features are stable progressive, starting from Moon, Sun and finally Earth stable stage. This application was and is usable since its Moon stage.

https://www.sqlite.org/index.html database is required to run this web application. Note this isn't a full on blown database server requirment, that runs in your background and uses your computers resources.


## New in v.1.8 

* Automated install module script **`./install_modules.sh `**
* Has Secure Backup/Restore. Providing accurate full data restore and merging with existing for live databases.
* Now with a distinct data page and view mode.
* New category selection, storing approuch.
* Better and more efficient application configuration and setup.
* Numerous fixes, and better exception handling.

## Life Log version 1.7

- Views updated, having option to exlude by category now, during the session logging.
- New system configuration options. i.e. $DEBUG for some sql statements.
- Server system based snapshot logs, on stats invocation.
- Server indentifier on login.

## Life Log version 1.5+

- Ritch Text Documents can be attached to Logs.
- Theme support. Change the look and feel. From the congiguration page.
- Expenses and Income totals, various new calculations.
- LTags inclusion, format and output better information.
- Better interactivity.

![Sample](VS-on-METABOX-42.png)



![Sample](VS-on-METABOX-34.png)

### Notice
*Important SQLite update arraived, 19-Jun-2019. Full with security patches, on buffer over., Denial of Service attacks. Use this version onwards. If placing this application on the internet.
*
