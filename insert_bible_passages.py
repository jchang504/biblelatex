#!/usr/bin/python

'''
For documentation, see README.md.
'''
import re
import requests
import sys

API_QUERY = 'http://www.esvapi.org/v2/rest/passageQuery?key=IP&passage=%s&output-format=plain-text&include-passage-references=true&include-first-verse-numbers=true&include-verse-numbers=true&include-footnotes=false&include-short-copyright=false&include-passage-horizontal-lines=false&include-heading-horizontal-lines=false&include-headings=false&include-subheadings=false&include-selahs=false&include-content-type=false&line-length=0'

# Regex strings and compiled regexes

BIBLE_MACRO_STRING = r'\\bible{([^}]+)}'
BIBLE_MACRO_REGEX = re.compile(r'\\bible{([^}]+)}')
SET_BIBLE_MACRO_STRING = r'\\setbible{([^}]+)}{([^}]*)}'
SET_BIBLE_MACRO_REGEX = re.compile(r'\\setbible{([^}]+)}{([^}]*)}')
BIBLE_OR_SET_MACRO_REGEX = re.compile(BIBLE_MACRO_STRING + '|' +
        SET_BIBLE_MACRO_STRING)
OPEN_SINGLE_QUOTE_REGEX = re.compile(r'([^A-Za-z])' + "'" + '([^\s"])')
CLOSE_SINGLE_QUOTE_REGEX = re.compile(r"(\S)'")
OPEN_DOUBLE_QUOTE_REGEX = re.compile(r'"(\S)')
CLOSE_DOUBLE_QUOTE_REGEX = re.compile(r'(\S)"')
VERSE_NUMBER_STRING = r'\[(\d+)\]'
VERSE_NUMBER_REGEX = re.compile(r'\[(?:\d+:)?(\d+)\]')
POETRY_SMALL_INDENT_STRING = r'^' + r'  (' + VERSE_NUMBER_STRING + r')?(\S+)'
POETRY_BIG_INDENT_STRING = r'^' + r'    (' + VERSE_NUMBER_STRING + r')?(\S+)'

# Hardcoded passage and citation mapping keys
PASSAGE = 'passage'
CITATION = 'citation'

# Default output format configuration (mutable)
format_string = '%(passage)s -- %(citation)s (ESV)'
text_wrapper = '\\textit'

# Given the raw plain text from the API, return the passage formatted for LaTeX
def format_response(raw):
    formatted = raw

    # Add n indents before poetry line (e.g. Psalms), after verse number
    def indent_after_verse_number(n):
        def indent_n(match):
            verse_number = match.group(1)
            if verse_number is None:
                verse_number = ''
            first_word = match.group(3)
            return verse_number + (n * '\\indent{}') + first_word
        return indent_n

    # Indent poetry lines
    formatted = re.sub(POETRY_SMALL_INDENT_STRING,
            indent_after_verse_number(1), formatted, flags=re.MULTILINE)
    formatted = re.sub(POETRY_BIG_INDENT_STRING, indent_after_verse_number(2),
            formatted, flags=re.MULTILINE)

    # Convert plain text quotes to LaTeX open and close quotes

    # Single quotes
    def latex_open_single_quote(match):
        return '%s`%s' % (match.group(1), match.group(2))
    def latex_close_single_quote(match):
        return "%s'{}" % match.group(1)
    formatted = OPEN_SINGLE_QUOTE_REGEX.sub(latex_open_single_quote, formatted)
    formatted = CLOSE_SINGLE_QUOTE_REGEX.sub(latex_close_single_quote,
            formatted)

    # Double quotes
    def latex_open_double_quote(match):
        return '``{}%s' % match.group(1)
    def latex_close_double_quote(match):
        return "%s''" % match.group(1)
    formatted = OPEN_DOUBLE_QUOTE_REGEX.sub(latex_open_double_quote, formatted)
    formatted = CLOSE_DOUBLE_QUOTE_REGEX.sub(latex_close_double_quote,
            formatted)

    # Convert verse numbers like [1] to LaTeX superscripts
    def superscript_verse_number(match):
        return '\\textnormal{\\textsuperscript{%s}}' % match.group(1)
    formatted = VERSE_NUMBER_REGEX.sub(superscript_verse_number, formatted)

    # Wrap paragraphs with text_wrapper
    paragraphs = formatted.splitlines()
    citation = paragraphs[0]
    wrapped_paragraphs = ['%s{%s}' % (text_wrapper, p) for p in paragraphs[1:]]

    # Format according to output format configuration
    return format_string % {PASSAGE: '\n\n'.join(wrapped_paragraphs), CITATION:
            citation}

# Given a re.MatchObject matching BIBLE_MACRO_REGEX, return the passage
# specified, formatted for LaTeX
def get_formatted_bible_text(match):
    passage_param = match.group(1)

    response = requests.get(API_QUERY % passage_param)
    if response.status_code != requests.codes.ok:
        sys.stderr.write('ERROR: Request to Bible API failed with status code: %s\n' % r.status_code)
        sys.exit(1)
    if response.text.startswith('ERROR'):
        sys.stderr.write('ERROR: Invalid passage argument: %s\n' % passage_param)
        sys.exit(1)
    return format_response(response.text)

# Given a re.MatchObject matching SET_BIBLE_MACRO_REGEX, set the global output
# format configuration
def set_output_format(match):
    global format_string, text_wrapper
    format_string = match.group(1)
    text_wrapper = match.group(2)
    return ''

# Given a re.MatchObject matching either BIBLE_MACRO_REGEX or
# SET_BIBLE_MACRO_REGEX, check and call the appropriate function
def handle_command(match):
    command = match.group(0)
    bible_match = BIBLE_MACRO_REGEX.match(command)
    if bible_match:
        return get_formatted_bible_text(bible_match)
    set_bible_match = SET_BIBLE_MACRO_REGEX.match(command)
    if set_bible_match:
        return set_output_format(set_bible_match)
    sys.stderr.write('ERROR: String matching BIBLE_OR_SET_MACRO_REGEX matches neither BIBLE_MACRO_REGEX nor SET_BIBLE_MACRO_REGEX\n')
    sys.exit(1)

filename = sys.argv[1]
with open(filename) as f:
    tex_source = f.read()

print BIBLE_OR_SET_MACRO_REGEX.sub(handle_command, tex_source)
