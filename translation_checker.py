#!/usr/local/Cellar/python/2.7.3/bin/python
# coding: utf-8
from optparse import OptionParser
import os
import tokenize
import cStringIO


try:
    import re2 as re
except ImportError:
    import re


REGEXP_RUS_LETTER = re.compile(u'[а-яА-ЯёЁ]+')
REGEXP_HTML_SUB = re.compile(
    '\{%[ ]*blocktrans.*?endblocktrans[ ]*%\}|{%[ ]*trans.*?%\}|<!.*?>|\{%[ ]*comment.*?endcomment[ ]*%\}',
    flags=re.DOTALL
)
REGEXP_JS_SUB = re.compile(  #regexp += '//.*?\n'
    'OTA\.utils\.gettext\(".*?"\)|' + "OTA\.utils\.gettext\('.*?'\)",
    flags=re.DOTALL
)
REGEXP_FIND = re.compile(
    u'[а-яА-ЯёЁ]+[^<]*|[а-яА-ЯёЁ]+[^>]*',
    flags=re.DOTALL
)
REGEXP_FIND_JS = re.compile(
    u'"[^"]*?[а-яА-ЯёЁ]+[^"]*?"|' + u"'[^']*?[а-яА-ЯёЁ]+[^']*?'",
    flags=re.DOTALL
)


def _str_prepare(string):
    return string.strip().replace('\n', '\\n')


def _print_found(text, path, regexp=REGEXP_FIND):
    rus_str = regexp.findall(text)
    const_dict = dict((i, rus_str.count(i)) for i in rus_str)

    if const_dict:
        print '\033[93mPath is:\033[92m {}\033[0m'.format(path)

    for rus_str, rus_str_count in const_dict.iteritems():
        print u'\033[90mFound {0} occurrences:\033[0m {1}'.format(
            rus_str_count, _str_prepare(rus_str)
        )


def check_py(path):
    """
    _(u'Ололо')
    """
    # v3.1
    text = open(path, 'r').read()
    io_obj = cStringIO.StringIO(text)
    out = []
    inside_gettext = 0
    prev_token_type = None
    prev_token_string = None
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1].decode('utf-8')
        start_line, start_col = tok[2]

        if token_type == tokenize.OP and token_string == '(' and inside_gettext:
            inside_gettext += 1

        if token_type == tokenize.OP and token_string == ')' and inside_gettext:
            inside_gettext -= 1

        if (token_type == tokenize.OP and token_string == '(' and
            prev_token_type == tokenize.NAME and prev_token_string == '_'):
            inside_gettext = 1

        if (token_type == tokenize.STRING and not inside_gettext and
            prev_token_type not in [tokenize.INDENT, tokenize.NEWLINE] and
            start_col):
            if len(REGEXP_RUS_LETTER.findall(token_string)):
                out.append(tok)

        prev_token_string = token_string
        prev_token_type = token_type

    if out:
        print '\033[93mPath is:\033[92m {}\033[0m'.format(path)

    for tok in out:
        token_string = tok[1]
        start_line, start_col = tok[2]
        for sub_str in token_string.decode('utf-8').split('\n'):
            print u'\033[90mLine #{0}:\033[0m {1}'.format(start_line, sub_str)
            start_line += 1
    return


def check_html(path):
    """
    {% blocktrans with un=user.name %}{{un}}, здарова!{% endblocktrans %}
    {% trans "Найти отели" as button_text %}
    """
    text = open(path, 'r').read().decode('utf-8')
    text = REGEXP_HTML_SUB.sub('', text)
    _print_found(text, path)


def check_js(path):
    """
    OTA.utils.gettext('Январь')
    OTA.utils.gettext('за {$nights} ночь|за {$nights} ночи|за {$nights} ночей')
    """
    text = open(path, 'r').read().decode('utf-8')
    text = REGEXP_JS_SUB.sub('', text)
    _print_found(text, path, regexp=REGEXP_FIND_JS)


def check_jst(path):
    """
    OTA.utils.gettext('Январь')
    OTA.utils.gettext('за {$nights} ночь|за {$nights} ночи|за {$nights} ночей')
    """
    text = open(path, 'r').read().decode('utf-8')
    text = REGEXP_JS_SUB.sub('', text)
    _print_found(text, path)


TRANSLATION_CHECKERS = {
    'py': check_py,
    'js': check_js,
    'jst': check_jst,
    'html': check_html,
}


def find_untranslated(path, exclude=None, mask=None, quiet=False):
    if exclude:
        for ex in exclude:
            if path.startswith(ex):
                return

    if mask:
        for ma in mask:
            if ma in path:
                return

    directory = os.path.split(path)[-1]
    if directory.startswith('.'):
        return

    if os.path.isdir(path):
        for dir_ in os.listdir(path):
            find_untranslated(
                os.path.join(path, dir_),
                exclude=exclude,
                mask=mask,
                quiet=quiet
            )
        return

    file_extension = directory.split('.')[-1]
    checker = TRANSLATION_CHECKERS.get(file_extension)

    if not checker:
        if not quiet:
            print '\033[91mUnknown extension for\033[0m {}'.format(path)
        return

    checker(path)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-e", "--exclude_path", dest="exclude",
        help="PATH to be excluded")
    parser.add_option("-m", "--exclude_mask", dest="mask",
        help="MASK to be excluded")
    parser.add_option("-q", "--quiet",
        action="store_true", dest="quiet", default=False,
        help="No output about wrong file extensions.")

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.error("incorrect number of arguments.")
    else:
        find_untranslated(
            args[0],
            exclude=options.exclude and options.exclude.split(','),
            mask=options.mask and options.mask.split(','),
            quiet=options.quiet
        )
