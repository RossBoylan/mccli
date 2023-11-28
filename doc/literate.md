This file has some internal notes about the possible use of literate programming tools for this project.

# Origins and Motivation

The switch to the heart failure model brought a new primary way to get output from the `Fortran` program: `.csv` files with 100's of variables as the columns, simulation year and demographics as the row key, and values for the rest.  Call those the **data files**. This was eventually accompanied by a csv file listing the output file, variable name, and variable description; call it the **codebook file**.  

I wanted to skip  the intermediate steps of making human readable output and go directly to stuffing the variables into a database, with separate values for each simulation.  We were already using such a database, with `frmtToData.py` reading the `.frmt` files to produce it and `frmtReport.py` providing a GUI to pull summaries out of it.

We also had the idea that a configuration file could specify which variables we actually wanted to preserve.  Call it the **configuration file**.

The hope was to save time and disk space while running, and save development time involved in creating nicely formatted (for humans) output files and then reversing the process to get summaries that humans actually did look at.

I explored all these things in a test project, and got them to work.  But when I turned to integrating it into the main code base, I was unsure how to structure it.  I had developed one class, but it seemed there might be others that made sense as well.  It was a somewhat big, unwieldy mess. Should I develop separate classes?  Much of the logic broke down by file: the class already created was for reading the codebook file; perhaps there should be one for each of the other files.  Of course, some operations required combining information from multiple sources; that could be a manager object.

If I did that, it seemed natural to put each class definition in a separate file.  I'm using the older, `node`-specific, modules for everything else (rather than the `ES6` module system), and so it seemed best to stick with that.  But then I have a bunch of files that are tightly related to each other and somewhat separate from the existing files that focus on user-level commands like initializing or running the simulation.

I was commenting on what was going on through code comments that followed no standard pattern, some of which didn't seem to attach naturally to particular functions.  *I should review commenting conventions for `JavaScript`.*

Which led me to think of literate programming.  I could have one document that described the whole subsystem--perhaps expanding to include the whole system someday--including high level relations between things and diagrams and tables when appropriate.  It would spin the pieces off into separate files if that's what I decided on.

# Considerations

* Does it run on MS-Windows? Ideally the tools could be used on our primary platform, MS-Windows, without too much hassle.
* Portability: Ideally the tools could be used on any platform.
* Complexity: The standard tools for literate program include (La)TeX, the literate tool itself, and possibly a compiler/build system to make the tool.  That's a lot to manage, and also a lot to understand.
* Setup burden: both the initial effort of selecting a system and later effort replicating it.
* Programming language support: initially this is for `Javascript` code, though it might expand to include `Python`, `Fortran` and other languages.  This is an issue because many literate programming systems only handle a limited range of languages, usually `C` and derivatives.  They may handle others in a degraded way, like providing no syntax highlighting.  Often the fixed formatting of `Python` or the original `Fortran` is lost by even language "agnostic" tools.
* Documentation language support: $\TeX$? $\LaTeX$? Figures? Tables? Markdown?
* Output Formats: $\TeX$? pdf? html?
* Multifile handling: Especially, can one input file generate multiple output code files?
* Reversability: how easy is it to trace a line in the generated source back to the literate source file it came from?



# Alternatives

There are [a lot](https://en.wikipedia.org/wiki/Literate_programming) of them.  Some highlights:

## [`noweb`](https://github.com/nrnrnr/noweb)

My first thought because it claims not to care what language you are programming in.  Packaged for many Linux distributions, but there don't seem to be Windows binaries around.  The [FAQ](https://www.cs.tufts.edu/~nr/noweb/FAQ.html#toc5) seems to indicate a world of problems getting it to work on Windows.  Apparently it uses some binaries of other programs, icon in particular, that are a) not prepackaged and b) really DOS or 32 bit programs that throw off complaints when run.  Leading to the suggestion to rebuild them. Ugh.

Naturally, this provides no formatting for the source code.

Provides output in $\TeX$, $\LaTeX$, and html.  The documentation language can certainly use $\TeX$; not sure about $\LaTeX$.

There is a noweb mode for `emacs`, though the same FAQ indicates it is (was?) rough around the edges.  And there is a noweb extension for `VSCode`, though it only provides formatting in the buffer--it doesn't actually use noweb to build things.

The markup seems a bit cumbersome; in particular I need `@{` not `{`, though maybe that's unnecessary in code sections.

## [Literate](https://zyedidia.github.io/literate/)

Binaries available for man *nix, but not MS-Windows. Someone uploaded a [Windows version](https://github.com/zyedidia/Literate/issues/49);  it isn't current or secure.  Input format is markdown and output is html.  Requires supplementary tools to pretty format the source code.  Written in `D`.  Provides line number syncing back to source doc, it says; not sure how that can be done in a language independent way.

There is a `Makefile` that is entirely Unix oriented, i.e. it assumes a `bash` or similar shell and utilities.  The [compiler](https://dlang.org/) is available as a Windows installer, though that doesn't solve how to make it.  Approaches to deal with this:
   1. manually interpret the `Makefile` and type the resulting commands.
   2. Translate the requirements to `CMake` and hope VSCode can deal with it better.
   3. Build and use under *nix or equivalent: cygwin or WSL.
   4. Use `MINGW64` variant of `MSYS2` to do the building.  The result is a native Windows executable.

`VSCode` has an extension for `D`, `webfreak.code-d`.

## [literate extension for `VSCode`](https://marketplace.visualstudio.com/items?itemName=jesterking.literate)

No obvious relation to the previous entry, though like it uses markdown input and (I think) html output.  Supports any language known to markdown; does the language need to be specified in each fragment? Tab-preserving.  Shows the human document as you go; must execute command to generate programs.  It supports multiple `.literate` input files; unclear if one input can generate multiple outputs.  No indexing capability.

Looks beta-ish; no activity for a year.

Tried it and couldn't get it to work.

## [fweb](https://w3.pppl.gov/~krommes/fweb.html)

Does `C` and `Fortran` in both original and modern variants including `C++`. Also does $\TeX$, and may have a generic mode a la noweb, though it recommends against using the generic mode.  Support is iffy; author retired.

Could it be used with JavaScript or Python?  There are several routes:
   1. Lie and say it's C.  Best case it works and formatting is a bit off.  Worst case it gags on some construct.
   2. Use the generic mode.  Not recommended.
   3. Extend the parser for the new language classes.  Major project.
   4. Use a 3rd party tool to classify the code.  Possibilities include the syntax definitions for `ANTLR`, `emacs` mode definitions, or the language servers used by `VSCode` (among others).  Probably also a big project.

fweb uses hand-tuned parsers for the languages it understands; in the past, I found those sometimes ran into trouble.

Examined fweb source on my home machine, including weaving `fweave` and `prod`.  Only confirms that modification would be hard.

## [FunnelWeb](http://www.ross.net/funnelweb/)

Works with any language; output in $\TeX$ or html; platform agnostic.  Binaries available for most platforms, though Windows 95/NT is latest for Windows.  Seriously documented.  *Doesn't handle tabs in source file well*, or 8 bit characters at all.

## [LyX](https://www.lyx.org)

Has a noweb extension, which says it depends on other things that aren't present.  There are also some notes about how to use `LyX` with `noweb` on the wiki; the difficulties stem from the fact that a .lyx file is not exactly $\LaTeX$.  But it sounds hokey--though since the versions are old, maybe things are better now.

This route does not look promising.

## Cygwin

One possible route to get stuff available on Unix but not MS-Windows is `cygwin`.  None of the literate processors discussed above are pre-packaged in cygwin (`LyX` is, presumably, but it's available directly for Windows).

It might be easier to build from source in this environment, but it doesn't offer any quick solutions.

## many others

https://github.com/justinmeiners/srcweave/ is a descendant of literate, done in a lispy language with a few changes.

## Only on Linux

I could only run the literate programming tools on Linux, using them to generate the program source files (`.js`, `.py`), committing the files, and then running them on Windows.

Probably too cumbersome to be practical since each debug, edit code cycle would need to make this trip across systems.

## Punt

User documentation should not be in literate programming form anyway, and can be done in plain text, markdown, or something more elaborate.

Design notes can go in a separate document with similar format options.

Detailed comments on the code can go in comments.

One of my original reasons for wanting a literate tool was to be  able to consider different classes or code sections separately.  They can go in separate files.

A weakness of anything that is not in the code file is that it tends to get out sync with the code.
