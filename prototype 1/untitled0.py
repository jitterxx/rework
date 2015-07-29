# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""

import datetime
import json
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

s = u'Что имеем на входе? Байты, которые IDLE передает интерпретатору. Что нужно на выходе? Юникод, то есть символы. Осталось байты превратить в символы — но ведь надо кодировку, правда? Какая кодировка будет использована? Смотрим дальше.'



tt = json.dumps({'to':s})

print s
print type(s)

print tt
print type(tt)

st = json.loads(tt)

print st
print type(st)

print st['to']
print type(st['to'])