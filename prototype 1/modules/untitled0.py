# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""

import datetime
import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_queue_module as rwQueue
import prototype1_email_module as rwEmail
import prototype1_type_classifiers as rwLearn
import json
import sys
import time
import base64
import pymongo
import networkx as nx
import matplotlib.pyplot as plt


from matplotlib import rc
rc('font',**{'family':'serif'})
rc('text', usetex=True)
rc('text.latex',unicode=True)
rc('text.latex',preamble='\usepackage[utf8]{inputenc}')
rc('text.latex',preamble='\usepackage[russian]{babel}')
import re

reload(sys)
sys.setdefaultencoding("utf-8")


session = rwObjects.Session()
superuser = rwObjects.get_by_uuid('4b0b843e-5546-11e5-a199-f46d04d35cbd')[0]
test_text = rwObjects.get_by_uuid('ce09e362-5875-11e5-9113-f46d04d35cbd')[0]

rwLearn.retrain_classifier(session, rwObjects.default_classifier)

"""
test_text.read(session)
test_text.clear_text()
print "Текст: %s" % test_text.text_clear
print "Оригинальные теги: %s\n" % test_text.__dict__['tags']
cl = rwObjects.get_by_uuid(rwObjects.default_classifier)[0]
targets = re.split(",",cl.targets)
custom = rwObjects.get_ktree_custom(session)

p, z = rwLearn.predict(rwObjects.default_classifier, [test_text.text_clear])
if z.any() != 1:
    print "Нет точно определенных элементов.\n"
    pp = 0
else:
    print "Есть точные данные:"
    pp = 1

for i in range(0,len(z)):
    if z[i] == pp and p[i] > 0.50:
        print targets[i]
        print "Вероятность: %s" % p[i]
        print custom[targets[i]].name
"""

rwLearn.autoclassify_all_notlinked_objects()
session.close()