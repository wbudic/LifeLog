# LifeLog Post Tags

```CNF
<<B<{Text To Bold}>>
<<I<{Text To Italic}>>
<<TITLE<{Title Text}>>
<<LIST<{List of items delimited by new line to terminate item or with '~' otherwise.}>>
<<IMG<{url to image}>>
<<FRM<{file name}_frm.png}>>
```

* frm.png images file pairs are located in the ./images folder of the cgi-bin directory. These are manually resized by the user. Next to the original. Otherwise, considered as standalone icons.
* _frm.png Image is resized to -> width="210" height="120"

Examples:

```sh
  ../cgi-bin/images/
			my_cat_simon_frm.png
      my_cat_simon.jpg

  For log entry, place:
  &nbsp;<<FRM<my_cat_simon_frm.png> <<TITLE<Simon The Cat>>
  This is my pet, can you hold him for a week while I am on holiday?

  Explicitly tag an URL in the log entry. Required if using in log IMG or FRM tags. 
  Otherwise link appears as plain text:
  &nbsp;<<LNK<{url to image}>>

```

* YouTube embed script is automatically parsed.

Example:

```pre

<iframe width="560" height="315" 
src="https://www.youtube.com/embed/xxxxxx" 
title="YouTube video player" frameborder="0" allowfullscreen>
</iframe>

```
