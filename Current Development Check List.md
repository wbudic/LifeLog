# Current Branch Development Moon-Stable-1.4
### Checked (&#10004;) Has been done and submitted to branch.
## Urgent
*&#10004; Bug, date validation for proper entered time, there is no 24 h.
*&#10004; Build login_ctrl.cgi login controler alias and password based. Where each alias creates its own database. It server side session based, that unless you logged off keeps the session 24 hr. by default. Alias is therefore to an separate database. If user doesn't know the password, can't get access. Client remote IP address is checked to be on local only network (IP pinged).
* &#10004; Build config.cgi that creates database and allowes editing of configuration. Main cgi redirect or links to it not doing that job no more.
* &#10004; Create View By Category Button
* >> &#10004; Main page display, has introduced complexity that needs smoothed out.
* &#10004; Implement Record Set operation renumerating id's if inserting records in the past (rowid renum.).
* &#10004; Add Date Diff Selected button implementation.

## Minor
* &#10004; HTML - Align [Reset View] button in search panel, not so visible.
* &#10004; Fix CSS spacing.
* &#10004; Add other categories. i.e. Work, Reacurring.
* &#10004; Add category desciption column and page, view and editing.
