# Branch Development Life Log in Perl

*This page lists current development and issues being worked on in the LifeLog app.*

## Life Log Application Development

### New Development v.2.3+

* [ ] Backup options revisited/retested.
* [ ] Categories display and intereaction to be bettered.
* [ ] Bug 37 Keywords only search not wotking on detecting very old items.
* [x] Fix uninitialized $scalars and warnings. My style of programming uses this as a perl feature, as unutilized is also null or empty. Linter disagrees with that. Empty or null  isn't also 0 for it. Null, empty, undef, and zero should be the same thing in scalar context and logic.
* [ ] Stats and config page should check github for latest version, as background pull.
* [ ] Implement template based CGI processing (slower but better separation of concerns).
  * This separation of concern currently not really necessary as at the main.cgi is the whole file, that also incorporates buffering and complex database rendering. Thereby a slight performance penalty would be having to read and process also an template. Buffering is also directly compressed to client. Giving fast pages that some webservers might not have inbuilt or provide (rare). We will see. Templates are good, as the page layout is easier to change and rearrange.
* [ ] Module installation script should check, on main.cnf and on perl soundness and compatibility.
  * Should check and display autonomes that contain expected defaults changed or disabled in configuration. i.e AUTO_LOGIN or DBI_MULTI_USER_DB
  * A trouble_shoot_configuration.pl should  be available to perform this, and be independently available from the main directory.
* [ ] Process actions.
  * Configured in main.cnf, to import perl action to execute, in parallel of returning pages.
  * Action programable are on login, logout, row. 
    * Where the row action processed is pushed back to browser on each main.cgi page call, logout action is pushed back to login_ctr.cgi page. 

    ```html
      # Separate process actions to execute in parallel.
      <<ACTION$$<login>actions/reminders.pl>>
      <<ACTION$$<row>actions/log.pl>>
      <<ACTION$$<logout>actions/log.pl>>
     ```

* [ ] Search panel revisited.
  * [ ] Search and previous view setup made fully session persisted.
  * [ ] Provide button reset search.
  * [x] Some longer keywords, even repeating from log to log, don't  show in autocomplete.
* [x] Sums and dynamic calculations, interactions further to be refined.
  * Canceling submit, leaves the translated '**\n**' for transfer not reverted.
* [x] Setting should provide page color defaults in form of an hash.
  * These should/can change based on selected theme. That possibly in future can be changed via config.
  * colBG,colFG, colSHDW, etc...
* [x] Printout page to include Amount column if category of items has valued asset, expense or income set. Providing also totals. Of Assets, and total on income and expense.
  * Introduce Currency setting, to replace amount '#'. Even though it could be number of, something not currency related.
* [x] Interaction - When editing an existing log entry, it needs confirmation, if it isn't a copy (now button wasn't pressed), before overwriting.
  * i.e, Warning! - Existing entry has been changed, are you sure do you want to overwrite it?
* [x] Configuration needs to be updated, to use CNF 2.2, for system reset, etc.
  * Config file "Data Fix* reset of settings updated to properly revert to factory defaults.
  * We need to also display stats for log file of the web server.
    * Maybe provide an rotational purge on config page access. i.e. if line count is over 1000, purge to tail -n 1000.
      * This sure an config file setting. i.e. <<WEB_SERVER_LOG_TAIL_LIMIT><1000>>>
* [x] Backup/Restore made various db engine aware and compatible. As the data is the same.
  * The data is the same, Structure, binary data and password handling is different, engine dependant.
* [x] Fix themes. Themes don't display and set consistently the pages throughout.
  * Login page should use standard default or last set theme.
  * All provided themes to have background image.
  * Stats page needs, new layout.
* [x] Add AUTO_LOGOFF setting. Default is no.
  * On session expired makes the page semi usable and still visible.
* [x] RTF load of the zero document if present. When RTF attaching to a new log, you can save the rtf,
  it is called a zero document (not assigned), as the log hasn't been saved yet. This reload can be useful, as it is always stored...
* [x] Implement backup/restore on Pg based data. Restore only partially works from older backup.
* &#10004; Bug 35. SQL migration, version update, not working for PG based databases.
* &#10004; JS - Event, on expense sum in log numbers found at beginning of lines.
* &#10004; Update to CNF v.2.2, branch to $RELEASE_VER = 2.3, Earth Stage initial.
  
#### Not Urgent New Development ( In Planning/Suggestions )

* Plugins
  * Perl files enabled by being including them in main.cnf file under the <<PLUGINS<>>> list, and placed in the plugins directory.
  * This plugin perl file is then be executed, to provide auto installation and checks.
  * The plugins are further stored and made available to the system via database settings and dynamics.
    * Removed entry in config file, will also start the process of removing it from the database settings.
* Config file custom SQL tables.
* Bank Statements Page
  * Import/Display by Account
    * CSV Format, stored in separate table.
      * BANK_ACCOUNT  = ID, BANK, ACC_NAME(16), ACC_NUMBER(20) 
      * BANK_TRANSACTIONS = ACC_ID, DATE, AMOUNT, DETAILS(64)
* Email selected log entries.
  * Sendmail must be working, and configuration file has an jason property <<JS_SENDMAIL>>>.
  * Selection on foot might need an menu instead of buttons.

 ``` JSON
        <<JS_SENDMAIL< 
        {
          From:""
          To_emails_choise:[
            "1","2","3"
          ]
          mailhub: default
          body_head:""
          body_foot:""
        }
        >>> 
 ```

* Migration from SQLite to Server SQL script provided.
  * This one will use the new config settings in main.cnf to migrate log data from and SQLite local db file.
* Global view overrides. These get generated in the db if set on logon. And used instead of the normal view.
* Overrides must always show todays log entries, regardless of criteria.
* VIEW_OVERRIDE_SYSLOGS={0/1}, anon if set 1-true, will hide older than today system logs. Doesn't affect category and keywords searches/views.
* VIEW_OVERRIDE_WHERE={""/{your where clause}}, allows your own WHERE override. Doesn't affect category and keywords searches/views.
  * i.e. <<VIEW_OVERRIDE_WHERE<"RTF==1 OR STICKY==1">>>, will show only these type of log entries.  
  * i.e. <<VIEW_OVERRIDE_WHERE<"DATE > DATE('now','start of month', '-2 month')">>>, will show only logs from current last two months.
  * i.e. <<VIEW_OVERRIDE_WHERE<"ID_CAT!==(select id from cat where name like 'system log')>>>, same as setting <<VIEW_OVERRIDE_SYSLOGS<<1>>>.
* Page section plugins.
  * Appears and is rendered in page section, via dynamic loading, json rendered html, server side in real time.
  * Configured in main.cnf.
  * Accessed via side menu to appear.
  * Default is to link to documentation, and about page.
  * Plugin behavior is to be invoked in real time on demand, utilizing in most complex scenario JSON as medium.
    * i.e. News or service feed, special view, file interaction.
  
### v.2.2 SUN STABLE
  
* Search keep in session should preserve and always set options as selection till it is ticked.
  * Reset Whole View to page view, should still set the search option till it is ticked.
  * Unticking Keep in Session should be honored on next browsing.
  * Keyword should be stripped from, punctuations.
* Deleting multiple items, RTF, should mark for vacuum on next logout.
* Order by Categories added to search/view.
* Search on multiple words should rank by encounter of words specified and display first. (That one is difficult)
* Auto collapse/expand on multi line logs by 0-none as default. Setting to 1 or more shows only that number of lines. (That one is difficult)
* &#10004; Send to system log, password change, backup issued, main.inf page view changes.
* &#10004; Command line logging, server side. i.e. LifeLog/log.pl -database {name} {-alias} {-password:}
  * Update CNFParser v.2.0.
* &#10004; Bug 34 - DB fix in config, removes associated RTF documents to logs, for some reason.
* &#10004; Page categories exclusion option in main.cnf. Log view server side is modified not to include excluded categories 
older by certain amount of days, default is 0, for from today older.

### v.2.1 RC1

*It has been 2 years, 4 months, 8 hours, 56 minutes, and 55 seconds
between 2018-08-22 04:13:55 **Moon Stable** production release and this
2020-12-22 13:10:50 **Sun Stable v.2.1**, next and final is the Earth release stage.*

* &#10004; Print View Selected.
* &#10004; Config. page set session expires times has to be validated not to be under 2 minutes.
* &#10004; Implement mapped provision of named timezones via main.inf, for cities not available in global zone list.
  * Javascript also needs to be updated to translate this properly.
* &#10004; PostgreSQL to be further tested. Implement server managed database.
  * On errors sessions appear not to be closed by driver, maybe this is required and they expire?
  * Not all sql has been translated or proper database everywhere established.
* &#10004; Session expired should disable the log entry form.
* &#10004; Implement log text field limit setting.  0 - Unlimited, 1024 - Default n>128 as minimum size.
* &#10004; System configuration variables should be sorted and listed by name and grouped by type. Anons presented at the bottom.
* &#10004; Provide office share public link for main.inf linked categories, No login required but no log creation or search is possible.
* &#10004; main.inf - Make the dbname uniform across all source types with Settings, as backups use the file format, not the database name.
* &#10004; Edit button to show if hidden is the log entry section.
* &#10004; Implement title bolding on logs using markdown, so tags can be avoided, for multiline logs.
* &#10004; Multi db driver type support. Earth stage requires same SQL related code to work on at least one more DBMS type other than SQLight.
  * PostgreSQL is the candidate as MySQL is not easy to install and bulky for all systems.
  * Developing and adopting to MySQL or any other system is not prerogative, as it works well as it is with inbuilt simplicity.
* &#10004; Single database, multi-user login.
* Static pages setting for the pages directory.
* Provide markdown text functionality to html pages. For quick vanilla plain documentation.

### v.2.0 SUN RC2 Encountered

* Sub users list with passwords in config to be provided, with access and category, permissions settings. Default enabled permission is Event view category.
* [Scrapt] Multiple search views and their settings, should be preserved as last preset. Maybe even have named multiple ones in a dropdown or part of the page menu.
  * Scrapt -> as view display is different to actual time based normal page display of records. Maybe in the future.
* [Scrapt] Multiple category assignment to be enabled, where the first selected is the primary, others put in a separate cross reference table, parseed as hashtags maybe.
  * Scrapt -> as many categories per log complex and not necessary as many categories per view is already there.
* &#10004; Export to CVS button on selected logs.
* &#10004; RTF based view of log entries.
* &#10004; Check and test cross release migration.
* &#10004; Minimise Log form when in View Mode.
* &#10004; Restore of backup on different version of LifeLog should fail with detecting this in provided error.
  * Provided Backup/Restore Specifications, and message that restoration has been invalidated as that is an invalid backup file.

### v.1.9 SUN RC1 Encountered

* &#10004; Hover over log entries, to make more visible what log entry is being ticked on wider screens.
* &#10004; Implement gzip http page encoding compression of traffic.
* &#10004; Autocompletion picks up long false words, in html and code type logs.

### v.1.8 SUN STABLE Encountered/Fixed

* &#10004; Implement View by Amount Type, reset button for categories.
* &#10004; Introduce a new column header background colour.
* &#10004; Autologin bypasses actual wanted login.
  * This is bug 20.

### v.1.7 MOON STAGE Encountered?Fixed 

* &#10004; Database backup tgz ball, upload and download button on config page.
  * You must have the password you logged in to unscramble the backup.
    * Alias -> pass -> backup password. Information required.
* Application log needed in the background for System based logs.
* New CNF Development.
  * &#10004; Migration is currently hard to maintain and data export and import is wrongly reliant to CVS.
  * &#10004; Anons to be enabled.
  * CVS imports/exports of full database are to be made obsolete in the future. It is not safe.
    * This will be still available via command line.
* RTF Documents header lister page, to provide for, new log entry assignment, deletion, edits.
  * There isnt and shouldn't be a full relationship to docs. Hence new log entries can link to existing, docs.
* &#10004;Use the pages cat_list meta data elements for dealing with categories in java scripts.
* &#10004; New Categories dropdown, grouping in ascending order and presenting in columns of five at a time.
* &#10004; Sticky rows bg colour, to be a shade different to other normal rows.
* &#10004; Login system log and out to be implemented. With system variable $TRACK_LOGINS to disable/enable.
* &#10004;Change all code to use Exceptions as project is becoming hard to manage.
  * The harder it is to foresee possible problems, the less likely you will add unnecessary complexity. -- bud@
* &#10004; Notes to Log table should be other way in relationship direction.
  * LOG.ID_RTF -> NOTES.rowid
  * This is currently causing problems when the log renumerates, or entries are imported.
* &#10004; In config page Categories section to appear after system settings. As less likely to be changed.
  * System Configuration section is to be sorted. As in future it is more likelly to grow.
* &#10004; New system setting, $VIEW_ALL_LMT=1000. To limit view all records displayed on huge databases.
* &#10004; Provide system logs on stats page runs.
* &#10004; Menus updated in other pages to have button look.
* &#10004; main.cnf newer versions should have precedence to id and entry name to previously set or stored in db.
* &#10004; Config stored list of excludes. Provide multiple excludes view.
* &#10004; Settings module requires subroutines for debug logging and db properties access.
* &#10004; LifeLog codebase release version upgrade tracking and procedures with older databases.
* &#10004; JS based session logout timer warning to be implemented.
* &#10004; Mutli new alias access flood attack security trigger implementation.
* &#10004; Debug system settings implementation.
* &#10004; Delete page updated to show better display of entries.
* &#10004; Login page to identify host.
* &#10004; Session cleanup on autologin not clearing properly.
  * A dbfix, should clear older entries as well.

### v.1.6 and less

* &#10004; $CUR_MTH_SVIEW - Start view page is for current month, and the sticky set.
* &#10004; Some System settings to be stored in session. As these are  known even before logon.
  * i.e. $SESSN_EXPR, $RELEASE_VER, $TIME_ZONE, $LOG_PATH
* &#10004; Various system setups, not dealing well with $ENV{'home'} in multi perl environment, releases.

## Urgent FIXES and Known Issues

* &#10004; CVS Export and Import has not been implemented for RTF type log entries.
  * CVS feature has been made obsolete, it shouldn't be used.
* &#10004; Expired sessions, swallow submits into void.
* &#10004; Dynamic toggle of page sections, interaction fixed, bettered.

## Planned New Possible Features of Minor Relevance

* Plugin subpages.
  * Configured in main.cnf
  * Appear on menu or as dropdouwn in the header.
  * Downloaded/Configured from the configuration page.
* View save feature. Where you name and save to config or session a dropdown of views.
* Fit to page log. Making log subpage scrollable rather than whole page to see the bottom.
* Make session timeout sub pages aware via JSON.
* Multiple category assignment table (set via hashtags and end of a post).
* Log cards Export/Import. Send log entries via email or USB, why not?
* Provide sub alias login that sets data visible to only a set of categories.
  * View specific based login on a different password.
* &#10004; Table sort in config system settings by variable name.
* Enable automatic bold title heading for specified cattegories.
* Theme colours to be revisited, bettered
* Enable file attachment to log entries.
* Enable Armour Mode
  * In this mode settings page is disabled. And can be enabled only by System Admin.
* Provide About button and info.

## Life Log RTF Documents using Quill Javascript RTF API

* Deal with export/import of RTF Documents.

## Bugs

### v. 2.3+ Encountered/Fixed

* Bug 37 Keywords only search not wotking on detecting very old items.
* &#10004; Bug 36.1, Introduced bug, old backup delete not working.
* &#10004; Bug 36, DBFix not fully working on PG based install and restore not working from backups made with older versions of OpenSSL.
  * Also, restore not working on uploaded backups, from local computer.
  
### v. 2.2 Encountered/Fixed

* &#10004; Bug 35, Migration and version updating SQL is wrong for PG database, it doesn't have rowid's.
* Bug 34, DB fix in config, removes associated RTF documents, for some reason.
* &#10004; Bug 33 Changing session timeout in config to an lib. background unparsable format cause unrecoverable system error.
  * i.e. Putting +1hr instead of +1h.
* &#10004; Bug 32 RTF creating/saving is broken.

### v. 2.1 Encountered/Fixed

* &#10004; Bug 31 PostgreSQL new created log view is not being created.
  * On  newly created database the view without the schema specified are seen as temporary views.
* &#10004; Bug 30 Wrongly entered or modified locale can't be reset no more to an valid one.

### v. 2.0 Encountered/Fixed

* &#10004; Bug 29 HTML output is incorrect since introducing buffering and content compression. Browser corrects, hence it was not noticed before.

### v. 1.9 Encountered/Fixed

* &#10004; Bug 28 - System info stats logs not reporting host anymore.
* Bug 27 - Restore of old backups not working anymore.
* Bug 26 - In Chrome editing log entry not working. Something refreshes page, after 5 seconds.
* &#10004; Bug 25 - SQLite view not properly sorting in new databases. Newer records listed last.
  * View should order by time function desc, ascended is default.
* &#10004; Bug 24 - Logs row sum calculation not working/wrong, with negative and positive values.
* &#10004; Bug 23 - Delete not working in view mode.
* &#10004; Bug 22 - Delete selection of entries not working after a while, db fix in config page required.
* &#10004; Bug 21 - Income sum for year in stats is displayed wrong.
* &#10004; Bug 20 - Autologin bypasses, wanted new alias login (on logoff).

### v. 1.8 Encountered/Fixed

* &#10004; Bug 19 - Same day datediff is displaying wrong report in time stack on the page.
* &#10004; Issue 18 - Setting excludes for views, deliveres page but long delays with server finished exchange (page doesn't hang).
  * The page is server delivered, if sections contain external internet links, this timeouts page browser delivery if the internet is down.
* &#10004; Bug 17 - Editing of entries on occasions, duplicates entries.
* &#10004; Bug 16 - Saving new log entries with rtf overides previous log entries rtf.
  * Issue 16.1 - Currently importing of records linked to rtf notes is not supported.
* &#10004; Issue 15 Date diff, showes upside down first range by current date with multiple selections.
  * Range should be selected from date in selected latest to current date last as inbetween difference.
* &#10004; Issue 14 Subpages pages links to main, restart main page session counter, making the main page fully usable.
  * Not really a bug. Session will expire but time remaining will be displayed wrong on the main page.
  * All subpages need either to inherit the counter, and jump user to the login screen if expired.
  * Or update main pages timer countdown. Which is not possible if browsers back button is pressed.
  * Pressing back button brings the page display to initial time it was loaded from.
  * This has been now marked as an complex issue. Not worth much spending time on.

* &#10004; Bug 13 - Migrated old data, linking to wrong id, db fix in config page seems to fix this.
* &#10004; Bug 12 - Invalid login only shows db error.

### v. 1.6 Encountered/Fixed

* &#10004; Bug - 11 View runs, brocken since sticky feature implementation. Page record sets don't work.
* &#10004; Bug - 10 Expense type entries don't fill amount field on edit button clicked.
* &#10004; Bug - 09 RTF documents lost on data renumeration of log. Data fix options in config. Needs urgent revision.
* Bug - 08 CSV imports duplicate on DB Fix in config page.
* &#10004; Bug - 07, Editing and RTF entry, doesn't strip the attached html to view in place.
* &#10004; Bug - 06, Invalid Time 00. Javascript error thrown, when 00am used.
* &#10004; Bug - 05, CRLF and apostrophe replacement not working.
* &#10004; Bug - 04, Local not picked up properly on current date.
* &#10004; Bug - 03, Keyword search not working on words as they are categorized wrongly by other dropdown in the background.
* &#10004; Bug - 02, Record set paging to previous page not always working. Getting stuck.
  * This occurs on new records placed in the far past. Complex problem.
* &#10004; Bug - 01, date validation for proper entered time, there is no 24 h.

***

   Document is from project ->  <https://github.com/wbudic/LifeLog/>

   An open source application.

<center>Life Log - Sun Stable Stage v.2.1 (2020)</center>
