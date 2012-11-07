#!/usr/local/Cellar/python/2.7.3/bin/python
# coding: utf-8
import sys
try:
    import re2 as re
except ImportError:
    import re


def get_line_nums(path):
    line_num = 0
    rus = re.compile(u'(?P<rus>[а-яА-Я]+([ ]+[а-яА-ЯёЁ]+)*)')
    for line in open(path, 'r'):
        line_num += 1
        found = rus.findall(line.decode('utf-8'))
        if found:
            found = [i[0] for i in found]
            found = ', '.join(found)
            print line_num, ':', found
    return


if __name__ == "__main__":
    get_line_nums(sys.argv[1])
