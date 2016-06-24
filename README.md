# Bible Reference LaTeX Preprocessor

Author: Jemmin Chang (jchang504@gmail.com)

This script finds Bible passage references in a LaTeX source file like:

`\bible{Gen1:1-5}`

and replaces them with the text of the passage from the ESV in a configurable
format (see [Configuring output format](#configuring-output-format), outputting
the result to stdout. The acceptable syntax is determined by the web API used,
which is http://www.esvapi.org/api. The first argument is used as the value for
the "passage" URL parameter, so whatever that URL parameter accepts will work.
In particular, the beginning and ending verse numbers are optional, according
to the usual practice, so Gen1, Gen1:1, are also fine. The book name can be
specified fully or with the first 3 letters/numbers (e.g. 1Co for 1
Corinthians), and capitalization doesn't matter. For more details, see the API
website. Note that there is a (pretty comfortable) rate limit of 5,000
queries/day/IP.

## Configuring output format

To configure the output format, add this command to your LaTeX source _before_
the `\bible` commands you want it to configure (you can run this command again
to reconfigure; `\bible` commands will always output according to the last
`\setbible` configuration):

`\setbible{format_string}{[\text_wrapper]}`

`format_string` is a [Python-style formatting
string](https://docs.python.org/2/library/stdtypes.html#string-formatting) with
these specific two mapping keys: `(passage)` and `(citation)`. These keys are
hardcoded in the script; you must use them exactly. `(passage)` will be
substituted with the passage text and `(citation)` will be substituted with the
passage citation (e.g. 'Genesis 1:1-5').  See [Default output
format](#default-output-format) for an example.

`\text_wrapper` is a single text-formatting LaTeX command which will be wrapped
around each paragraph of the passage, with `\textnormal` used to cancel it
around the verse numbers. (This works for things like `\textit` or `textbf`,
but not arbitrary commands, of course.) It is optional in the sense that if you
let it be the empty string, it won't have any effect, as wrapping things in
braces does nothing in LaTeX.

### Default output format

The default output format configuration before you run any `\setbible` is as
follows.

```
format_string: '%(passage)s -- %(citation)s (ESV)'
\text_wrapper: '\textit'
```

## Running the preprocessor

The idea is to use this script as a preprocessor for LaTeX files (run before
you compile with your normal LaTeX compiler). For convenience, you can combine
the steps in a function in your bashrc, e.g. (assuming this script lives in
your home directory):

```
function biblepdflatex {
    python ~/insert_bible_passages.py $1 > ${1}biblerefpreprocessed
    pdflatex ${1}biblerefpreprocessed
    rm ${1}biblerefpreprocessed
}
```

Of course, this will prevent you from using additional options with pdflatex,
so if you need that, you may need to run the preprocessor separately first.
