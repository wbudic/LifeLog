# Branch Development LifeLog in Perl

*This page lists current development and issues being worked on in the LifeLog app. Being in the **Sun** stage, means there is a production environment. And usable, used. When, the project reaches **Earth** stage. It will be at its final specification. No data structures or major new features can be added or requested anymore. Only bug fixes, enhancements and efficiency fixes, if any at the **Earth** stage.*

This version is not compatible in data structure to prior versions. Data migration is required, to transfer previous data (see ../dbLifeLog/main.cnf).


## LifeLog Development

### v.1.8 SUN STABLE

* &#10004; Introduce a new column header background colour.
* &#10004; Autologin bypasses actual wanted login.
  * This is bug 20.

### v.1.7 Encountered

* &#10004; Database backup tgz ball, upload and download button on config page.
  * You must have the password you logged in to unscramble the backup.
    * Alias -> pass -> backup password. Information required.
* Application log needed in the background for System based logs.
* New CNF Development.
  * &#10004; Migration is currently hard to maintain and data export and import is wrongly reliant to CVS.
  * &#10004; Anons to be enabled.
  * CVS imports/exports are to be made obsolete in the future. It is not safe.
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
* &#10004; In config page Categories section to appear after system settings. As less likelly to be changed.
  * System Configuration section is to be sorted. As in future it is more likelly to grow.
* &#10004; New system setting, $VIEW_ALL_LMT=1000. To limit view all records displayed on huge databases.
* &#10004; Provide system logs on stats page runs.
* &#10004; Menus updated in other pages to have button look.
* &#10004; main.cnf newer versions should have precedence to id and entry name to previously set or stored in db.
* &#10004; Config stored list of excludes. Provide multiple excludes view.
* &#10004; Settings module requires subroutines for debug logging and db properties access.
* &#10004; LifeLog codebase release verion upgrade tracking and procedures with older databases.
* &#10004; JS based session logout timer warning to be implemented.
* &#10004; Mutli new alias access flood attack security trigger implementation.
* &#10004; Debug system settings implementaiton.
* &#10004; Delete page updated to show better display of entries.
* &#10004; Login page to indentify host.
* &#10004; Session cleanup on autologin not clearing properly.
  * A dbfix, should clear older entries as well.

### v.1.6 and less

* $CUR_MTH_SVIEW - Start view page is for current month, and the sticky set.
* &#10004; Some System settings to be stored in session. As these are  known even before logon.
  * i.e. $SESSN_EXPR, $RELEASE_VER, $TIME_ZONE, $LOG_PATH
* &#10004; Various system setups, not dealing well with $ENV{'home'} in multi perl environment, releases.

## Urgent FIXES and Known Issuses

* &#10004; Expired sessions, swallow submits into void.
* CVS Export and Import has not been implemented for RTF type log entries.
* &#10004; Dynamic toggle of page sections, interaction fixed, bettered.

## Planned New Possible Features of Minor Relevance

* Plugin subpages.
  * Configured in main.cnf
  * Appear on menu or as dropdouwn in the header.
  * Downloaded/Configurated from the configuration page.
* View save feature. Where you name and save to config or session a dropdown of views.
* Fit to page log. Making log subpage scrollable rather than whole page to see the bottom.
* Make session timeot sub pages aware via JSON.
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

## LifeLog RTF Documents using Quill Javascript RTF API

* Deal with export/import of RTF Documents.

## Bugs

### v. 1.9 Encountered/Fixed

* &#10004 Bug 22 - Delete selection of entries not working after a while, db fix in config page required.
* Bug 21 - Income sum for year in stats is displayed wrong.
* &#10004 Bug 20 - Autologin bypasses, wanted new alias login (on logoff).

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

* &#10004; Bug - 11 View runs, brocken since sticky feature implentation. Page record sets don't work.
* &#10004; Bug - 10 Expense type entries don't fill ammount field on edit button clicked.
* &#10004; Bug - 09 RTF documents lost on data renumeration of log. Data fix options in config. Needs urgent revision.
* Bug - 08 CSV imports duplicate on DB Fix in config page.
* &#10004; Bug - 07, Editing and RTF entry, Dosen't strip the attached html to view in place.
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

<center>Sun Stage v.1.8 - 2020</center>
