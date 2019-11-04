# Branch Development LifeLog in Perl - Sun Stage v. 1.6

*This page lists current development and issues being worked on in the LifeLog app. Being in the **Sun** stage, means there is a production environment. And usable, used. When, the project reaches **Earth** stage. It will be at its final specification. No data structures or major new features can be added or requested anymore. Only bug fixes, enhancements and efficiency fixes, if any at the **Earth** stage.*

This version is not compatible in data structure to prior versions. Data migration is required, to transfer previous data (see ../dbLifeLog/main.cnf).

## LifeLog
* Various system setups, not dealing well with $ENV{'home'} in multi perl environment, releases.
* Paging of datasets to be redone.
* &#10004; Implement sticky log entries.
* $CUR_MTH_SVIEW - Start view page is for current month, and the sticky set.
* Some System settings to be stored in session. As these are  known even before logon.
> i.e. $SESSN_EXPR, $RELEASE_VER, $TIME_ZONE, $LOG_PATH

* &#10004; Dropdown for type of log amount (Mark as Expense). Default is Asset. Asset is neither, income or expense.
* &#10004; Implement RTF Documents.
> Useful as more document style formated details can be added instead of just plain text.
*&#10004; Preserve Search view selections. After edits and submit.
> * &#10004; Preserve from to date selections.
> * &#10004; Date View not working on Local entered date format.
*&#10004; Sum selected, income, expense, totals.
&#10004; Sum on view.


## Urgent FIXES and Known Issuses
* Expired sessions, swallow submits into void.
* CVS Export and Import has not been implemented for RTF type log entries.
&#10004; Dynamic toggle of page sections, interaction fixed, bettered.
&#10004; View by Date - search not showing current month entries.
&#10004; Fix Interaction jumping edits and creating new entries via now button.
>&#10004;  Fix some LTAGS not saved as LTags server side.

&#10004; Autologin feature, that expires on logout.
&#10004; Data/Login control updated to read the configuration file.
&#10004; Configuration file to be updated to carry also categories.
* &#10004; Configuration page to be updated, system variables description field to be implemented.
* &#10004; Configuration page - data fix section to be implemented.
* &#10004; Build login_ctrl.cgi login controller alias and password based. Where each alias creates its own database. It server side session based, that unless you logged off keeps the session 24 hr. by default. Alias is therefore to an separate database. If user doesn't know the password, can't get access. Client remote IP address is checked to be on local only network (IP pinged).
* &#10004; Build config.cgi that creates database and allows editing of configuration. Main cgi redirect or links to it not doing that job no more.
* &#10004; Create View By Category Button
* &#10004; Main page display, has introduced complexity that needs smoothed out.
* &#10004; Implement Record Set operation re-numerating id's if inserting records in the past (rowid renum.).
* &#10004; Add Date Diff Selected button implementation.


## New Features of Minor Relevance
* &#10004; Config page, links on menu to sections.
* Theme colours to be revisited, bettered
* &#10004; Config Export of Log and Categories to be provided as a button..
* &#10004; Provide Exclude an Category View (if posible multiple categories). Should have option to session or not.
* &#10004; Provide Themes
* &#10004; Enable sticky log entries
* Enable file attachment to log entries.
* Enable Armour Mode
> In this mode settings page is disabled. And can be enabled only by System Admin.
* Provide About button and info.
* &#10004; Configuration page - JQuery look and feel implemented.
* &#10004; Migration for data structural changes to be bettered.
* &#10004; Floating side menu for links and navigation.
* &#10004; JQUERY Integration, UI and autocomplete.
* &#10004; HTML - Align [Reset View] button in search panel, not so visible.
* &#10004; Fix CSS spacing.
* &#10004; Add other categories. i.e. Work, Recurring.
* &#10004; Add category description column and page, view and editing.

## LifeLog RTF Documents using Quill Javascript RTF API

&#10004; Separate JSON service page.
>* Provide for file attachments. 
> &#10004; Display in log, read only RTF on click of button.
> &#10004; Uses compressed RTF Documents in a Notes tabe.
>&#10004; Deletion of log, deletes the document.

## Bugs
Bug - 11 View runs, brocken since sticky feature implentation. Page record sets don't work.
* &#10004; Bug - 10 Expense type entries don't fill ammount field on edit button clicked.
* &#10004; Bug - 09 RTF documents lost on data renumeration of log. Data fix options in config. Needs urgent revision.
* Bug - 08 CSV imports duplicate on DB Fix in config page.
* Bug - 07, Editing and RTF entry, Dosen't strip the attached html to view in place.
* &#10004; Bug - 06, Invalid Time 00. Javascript error thrown, when 00am used.
* &#10004; Bug - 05, CRLF and apostrophe replacement not working.
* &#10004; Bug - 04, Local not picked up properly on current date.
* &#10004; Bug - 03, Keyword search not working on words as they are categorized wrongly by other dropdown in the background.
* &#10004; Bug - 02, Record set paging to previous page not always working. Getting stuck.
>> This occurs on new records placed in the far past. Complex problem.
* &#10004; Bug - 01, date validation for proper entered time, there is no 24 h.



***

** Checked (&#10004;) Are items that have been done and submitted to the branch.**
**Project ->**  https://github.com/wbudic/LifeLog/
