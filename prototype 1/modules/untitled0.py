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
"""
from sklearn.neighbors import NearestNeighbors
from sklearn.decomposition import PCA

# Данные для анализа
msg1 = rwObjects.get_by_uuid('61779b3a-475a-11e5-8833-f46d04d35cbd')[0]
msg1.clear_text()
test_data = [msg1.__dict__['text_clear']]
print test_data

# Данные для обучения кластера
# Получаем все кейсы
resp = session.query(rwObjects.Case).all()
train_data = []
train_uuid = []
vectorizer = rwLearn.TfidfVectorizer(tokenizer=rwLearn.tokenizer_3, max_features=200)
pca = PCA()

for case in resp:
    c = rwObjects.get_text_from_html(case.query)
    train_data.append(c)
    train_uuid.append(case)
    print case.subject
    print c

x = vectorizer.fit_transform(train_data)
print "Размеры : %s %s " % x.shape
#x = pca.fit_transform(x.todense())
#print "Размеры после PCA: %s %s " % x.shape
X = x.todense()

# Тренировка
nbrs = NearestNeighbors(n_neighbors=3, algorithm='ball_tree').fit(X)

# Готовим тестовые данные
t = vectorizer.transform(test_data)
#t = pca.transform(t.todense())
T = t.todense()


# Расчет расстояний
distances, indices = nbrs.kneighbors(T)
print "Индексы компонент : \n %s" % indices
print "Расстояния : \n %s" % distances

for i in indices[0]:
    print i
    print train_uuid[i].subject


#rwLearn.train_neighbors(session, rwObjects.default_neighbors_classifier)


result = rwLearn.predict_neighbors(rwObjects.default_neighbors_classifier, test_data)

print "Самые похожие объекты :"
for i in result:
    obj = rwObjects.get_by_uuid(i[0])[0]
    print "Кейс : %s (расстояние %s)" % (obj.subject,i[1])
"""



obj = rwObjects.get_by_uuid('39ed6a36-44cb-11e5-a8fd-f46d04d35cbd')[0]
obj.clear_text()
case = rwObjects.get_by_uuid('402faaee-4b15-11e5-92a4-f46d04d35cbd')[0]

from prototype1_tools import extract_addresses
import urllib
from bs4 import BeautifulSoup

email_to = "mailto:"
params = {'subject':'','references':'','body':'','cc':''}
param_to = ''
pre_body = ''

for adr,names in extract_addresses(obj.__dict__['from']).iteritems():
    param_to += adr + ","

params['subject'] = "Re: " + obj.__dict__['subject']
params['references'] = obj.__dict__['message-id'].replace(" ","")

soup = BeautifulSoup(obj.__dict__['raw_text_plain'], from_encoding="utf8")
body = str(soup.find('body').contents)
body = ""

pre_body = "<pre>" + body + "</pre>"

params['body'] = """<html>
                    <head><meta http-equiv="content-type" content="text/html; charset=utf-8"></head>
                    <body text="#000000" bgcolor="#FFFFFF">""" + str(case.solve) + pre_body + "</body></html>"


email_to += param_to + "?"

for k in params.keys():
    print k
    print params[k]
    print urllib.quote(params[k])
    email_to += "&" + k + "=" + urllib.quote(params[k])


print email_to

session.close()
