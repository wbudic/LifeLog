# L-Tags
```HTML
 <<B<{Text To Bold}>>

<<I<{Text To Italic}>>

<<TITLE<{Title Text}>>

<<LIST<{List of items delimited by new line to terminate item or with '~' otherwise.}>

<<IMG<{url to image}>>

<<FRM<{file name}_frm.png}>>
```HTML

*_frm.png images file pairs are located in the ./images folder of the cgi-bin directory.
These are manually resized by the user. Next to the original. Otherwise considered as stand alone icons. *_frm.png Image resized to -> width="210" height="120"
Example:
```

  ../cgi-bin/images/
			my_cat_simon_frm.png
   my_cat_simon.jpg

          For log entry, place:

	  <<FRM>my_cat_simon_frm.png> <<TITLE<Simon The Cat>>
	  This is my pet, can you hold him for a week while I am on holiday?
```

```HTML
<<LNK<{url to image}>>
```HTML
Explicitly tag an URL in the log entry. Required if using in log IMG or FRM tags. Otherwise link appears as plain text.