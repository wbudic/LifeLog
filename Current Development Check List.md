# Current Branch Development Sun-1.5
## Current 
LifeLog Document using Quill
- 
* Separate Page
* Uses Encryption, Compression extension in SQLite.
* Provide file attachments.

**Log**
 x Sum selected, income, expense, totals. 
 x Sum on view.
 x Preserve from to date selections.
 
## Urgent
* Fix Interaction jumping edits and creating new entries via now button.
>Fix some LTAGS not saved as LTags server side.

*&#10004; Autologin feature, that expires on logout.
*&#10004; Data/Login control updated to read the configuration file.
&#10004; Configuration file to be updated to carry also categories.
* &#10004; Configuration page to be updated, system variables description field to be implemented.
* &#10004; Configuration page - data fix section to be implemented.
* &#10004; Build login_ctrl.cgi login controller alias and password based. Where each alias creates its own database. It server side session based, that unless you logged off keeps the session 24 hr. by default. Alias is therefore to an separate database. If user doesn't know the password, can't get access. Client remote IP address is checked to be on local only network (IP pinged).
* &#10004; Build config.cgi that creates database and allows editing of configuration. Main cgi redirect or links to it not doing that job no more.
* &#10004; Create View By Category Button
* &#10004; Main page display, has introduced complexity that needs smoothed out.
* &#10004; Implement Record Set operation re-numerating id's if inserting records in the past (rowid renum.).
* &#10004; Add Date Diff Selected button implementation.


## Minor
* Implement RTFDocumentation.
> Usefull as backup of and direct access of important documents at the day of attachement time.
* Provide Themes
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

## Bugs
* &#10004; Bug - 01, date validation for proper entered time, there is no 24 h.
* &#10004; Bug - 02, Record set paging to previous page not always working. Getting stuck.
>> This occurrs on new records placed in the far past. Complex problem.
* &#10004; Bug - 03, Keyword search not working on words as they are categorized wrongly by other dropdown in the background.
* &#10004; Bug - 04, Local not picked up properly on current date.
* &#10004; Bug - 05, CRLF and apostrophe replacement not working.
***

** Checked (&#10004;) Are items that have been done and submitted to the branch.**
**Project ->**  https://github.com/wbudic/LifeLog/
