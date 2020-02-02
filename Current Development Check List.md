# Branch Development LifeLog in Perl - Sun Stage v. 1.7

*This page lists current development and issues being worked on in the LifeLog app. Being in the **Sun** stage, means there is a production environment. And usable, used. When, the project reaches **Earth** stage. It will be at its final specification. No data structures or major new features can be added or requested anymore. Only bug fixes, enhancements and efficiency fixes, if any at the **Earth** stage.*

This version is not compatible in data structure to prior versions. Data migration is required, to transfer previous data (see ../dbLifeLog/main.cnf).


## LifeLog Development

### v.1.7 Encountered

* New CNF Development.
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
* Provide sub alias login that sets data visible to only a set of categories.
  * View specific based login on a different password.
* &#10004; Login page to indentify host.
* &#10004; Session cleanup on autologin not clearing properly.
  * A dbfix, should clear older entries as well.

### v.1.6 and less

* $CUR_MTH_SVIEW - Start view page is for current month, and the sticky set.
* Some System settings to be stored in session. As these are  known even before logon.
  * i.e. $SESSN_EXPR, $RELEASE_VER, $TIME_ZONE, $LOG_PATH
* &#10004; Various system setups, not dealing well with $ENV{'home'} in multi perl environment, releases.

## Urgent FIXES and Known Issuses

* Expired sessions, swallow submits into void.
* CVS Export and Import has not been implemented for RTF type log entries.
&#10004; Dynamic toggle of page sections, interaction fixed, bettered.

## New Features of Minor Relevance

* Theme colours to be revisited, bettered
* Enable file attachment to log entries.
* Enable Armour Mode
  * In this mode settings page is disabled. And can be enabled only by System Admin.
* Provide About button and info.

## LifeLog RTF Documents using Quill Javascript RTF API

* Deal with export/import of RTF Documents.

## Bugs

### v. 1.7 Encountered/Fixed

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
* Bug - 07, Editing and RTF entry, Dosen't strip the attached html to view in place.
* &#10004; Bug - 06, Invalid Time 00. Javascript error thrown, when 00am used.
* &#10004; Bug - 05, CRLF and apostrophe replacement not working.
* &#10004; Bug - 04, Local not picked up properly on current date.
* &#10004; Bug - 03, Keyword search not working on words as they are categorized wrongly by other dropdown in the background.
* &#10004; Bug - 02, Record set paging to previous page not always working. Getting stuck.
   * This occurs on new records placed in the far past. Complex problem.
* &#10004; Bug - 01, date validation for proper entered time, there is no 24 h.

***

     Checked (&#10004;) Are items that have been done and submitted to the branch.

     Project ->  <https://github.com/wbudic/LifeLog/>
