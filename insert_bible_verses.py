#!/usr/bin/python

'''
Author: Jemmin Chang (jchang504@gmail.com)

Finds Bible verse references in a LaTeX source file with this syntax:

\bible{ISA3:1-5}{\text_wrapper}

and replaces them with the text of the passage from the ESV wrapped under
\text_wrapper, with the citation at the end. The acceptable syntax is
determined by the API used, which is http://www.esvapi.org/api. The first
argument is used as the value for the "passage" URL parameter, so whatever that
URL parameter accepts will work. In particular, the beginning and ending verse
numbers are optional, according to the usual practice, so ISA3, ISA3:4, are
also fine. The book name can be specified fully or with the first 3
letters/numbers (e.g. 2co for 2 Corinthians), and capitalization doesn't
matter. For more details, see the API website. Note that there is a (pretty
comfortable) rate limit of 5,000 queries/day/IP.

The idea is to use this script as a preprocessor for LaTeX files. Define the
\bible macro in your LaTeX file as something like:

\newcommand{\bible}[2]{ERROR: Unresolved \textbackslash{}bible reference
        found. Aborting compilation here. \end{document}}

That way, if you forget to run this preprocessor before compiling, it will be
obvious. For convenience, you can combine the steps in a function in your
bashrc, e.g. (assuming this script lives in your home directory):

function biblepdflatex {
    python ~/CMU/kupc/bible_verse_latex_preprocessor/insert_bible_verses.py $1 > ${1}bibleversepreprocessed
    pdflatex ${1}bibleversepreprocessed
    rm ${1}bibleversepreprocessed
}

(Of course, this will prevent you from using additional options with pdflatex,
so if you need that, you may need to run the preprocessor separately first.)
'''

import re
import requests
import sys

BIBLE_MACRO_REGEX = r'\\bible{([^}]+)}{([^}]+)}'
CITATION_REGEX = r'(?:\d )?[\w\s]+ [0-9:-]+'
OPEN_QUOTE_REGEX = r'"(\S)'
CLOSE_QUOTE_REGEX = r'(\S)"'
VERSE_NUMBER_REGEX = r'\[(\d*)\]'
API_QUERY = 'http://www.esvapi.org/v2/rest/passageQuery?key=IP&passage=%s&output-format=plain-text&include-passage-references=true&include-first-verse-numbers=false&include-verse-numbers=true&include-footnotes=false&include-short-copyright=false&include-passage-horizontal-lines=false&include-heading-horizontal-lines=false&include-headings=false&include-subheadings=false&include-selahs=false&include-content-type=false&line-length=79'

# Given the raw plain text from the API, return the passage formatted for LaTeX
def format_response(raw, text_wrapper):
    formatted = raw

    # Convert plain text quotes to LaTeX open and close quotes
    def latex_open_quote(match):
        return '``%s' % match.group(1)
    def latex_close_quote(match):
        return "%s''" % match.group(1)
    formatted = re.sub(OPEN_QUOTE_REGEX, latex_open_quote, formatted)
    formatted = re.sub(CLOSE_QUOTE_REGEX, latex_close_quote, formatted)

    # Convert verse numbers like [1] to LaTeX superscripts
    def superscript_verse_number(match):
        return '\\textnormal{\\textsuperscript{%s}}' % match.group(1)
    formatted = re.sub(VERSE_NUMBER_REGEX, superscript_verse_number, formatted)

    # Move citation from beginning to end, wrap text, return
    m = re.match(CITATION_REGEX, formatted)
    if m:
        formatted = re.sub(CITATION_REGEX, '', formatted)
        return '%s{%s} -- %s' % (text_wrapper, formatted, m.group(0))
    else:
        sys.stderr.write('ERROR: Failed to find verse citation in API response: %s\n' % formatted)
        sys.exit(1)

# Given a re.MatchObject matching a Bible macro, return the passage specified,
# formatted for LaTeX
def get_formatted_bible_text(match):
    response = requests.get(API_QUERY % match.group(1))
    if response.status_code != requests.codes.ok:
        sys.stderr.write('ERROR: Request to Bible API failed with status code: %s\n' % r.status_code)
        sys.exit(1)
    if response.text.startswith('ERROR'):
        sys.stderr.write('ERROR: Invalid passage argument: %s\n' % match.group(1))
        sys.exit(1)
    return format_response(response.text, match.group(2))

filename = sys.argv[1]
with open(filename) as f:
    tex_source = f.read()

print re.sub(BIBLE_MACRO_REGEX, get_formatted_bible_text, tex_source)
