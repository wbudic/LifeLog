# Configuration Network File Format Specifications

 Moon Stage v.1.0

## Introduction

This is a simple and fast file format. That allowes setting an network application with constant values.
SQL database structures and data. It is designed to accomodate an parser to read and parse CNF tags.
These can be of three types, using an textual similar presentation.
And are recognised as constants, anons and sqlites.
## CNF Formatting Rules

* Text that isn't CNF tagged is ignored in the file and can be used as comments.
* CNF tag begins with an **<<** and ends with an **>>**
* CNF instructions and constants are uppercase.
* CNF instructions are all uppercase and unique, to its processor.
* A CNF constant in its propety name is prefixed with an '**$**' signifier.
  * Constants are ususally scripted at the begining of the file, or parsed first in a separate file.
  * The instruction processor can use them if signifier $ surounds the constant name. Therefore, replacing it with the contants value if further found in the file.

        <<<CONST>$APP_PATH=~/MyApplication>>
        <<app_path>$APP_PATH$/module/main>>
  * CNF Constant values can't be changed for th life of the application.
  * CNF Constant values can be changed in the file itself only.
* A CNF Anon is to similar to constants but a more simpler property and value only pair.
  * Anon is not instruction processed. Hence anonymouse in nature for its value.
  * Anon has no signifier.
  * Anon value is global to the application and its value can be modified.

        <<USE_SWITCH>true>>
        <<DIALOG_TITLE_EN>MyApplication Title>>

* CNF supports basic SQL Database structure statment generation. This is done via instruction based CNF tags. Named sqlites.
  * Supported is table, view, index and data creation statments.
  * Database statments are generic text, that is not further processed.
  * There is no database interaction, handling or processing as part of this processing.

## CNF Tag Formats
### Property Value Tag
    <<{name}<{value}>>
### Instruction Value Tag
    <<<{instruction}
    {value\n...valuen\n}>>
### Full Tag
    <<{name}>{instruction}
        {value\n...value\n}
    >>
**Examples**

    <<CONST>$HELP
        Sorry help is currently.
        Not available.
    >>
    <<<CONST
        $RELEASE_VER = 1.8
        $SYS_1 =    10
        $SYS_2 = 20
        $SYS_3 =      "   Some Nice Text!   "
    >>
    <<PRINT_TO_HELP<true>>

## SQL Instruction Formatting

(section not complete, as of 2020-02-02)

* SQLites have the following reserved instructions.
  * TABLE
  * INDEX
  * DATA

        <<MyAliasTable>TABLE
            ID INT PRIMARY KEY NOT NULL,
            ALIAS VCHAR(16),
            EMAIL VCHAR(28),
            FULL_NAME VCHAR(128)
        >>

***



     Project ->  <https://github.com/wbudic/LifeLog/>
