# -*- coding: utf-8 -*-
"""
Created on Mon May 25 16:01:48 2015

@author: sergey

Модуль содержит функции необходимые для проведения классификации текстовых
данных.


"""

#!/usr/bin/python -t
# coding: utf8

import pandas as pd
import prototype1_objects_and_orm_mappings as rwObjects
import datetime
import json
import re
import pymorphy2
from time import time
import pandas as pd
import chardet


from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.cross_validation import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn import metrics
from sklearn import tree
import ast
import base64
from sklearn.externals import joblib
import sqlalchemy


import sys
reload(sys)
sys.setdefaultencoding("utf-8")

debug = True

#split for words
def tokenizer_1(data):
    #print 'data tokenizer: ', data
    morph = pymorphy2.MorphAnalyzer()
    
    
    splitter = re.compile('\W',re.I|re.U)
    
    clear = splitter.split(data)
    f = []
    for i in clear:
        #print i
        m = morph.parse(i)
        if len(m) > 2 and len(m)<20: 
            word = m[0]
            if word.tag.POS not in ('NUMR','PREP','CONJ','PRCL','INTJ'):
                  f.append(word.normal_form)
                  #print word.tag.POS
        
       
    return f


def init_classifier():
    u"""
    Инициализация классификатора.
    """
    session = rwObjects.Session()
    CL = rwObjects.Classifier()
    CL.clf_type = 'DTree'
    CL.clf_path = str(CL.uuid) + '_'+str(CL.clf_type)+'_classifier.joblib.pkl'
    
    clf = tree.DecisionTreeClassifier()
        
    try:
        joblib.dump(clf, CL.clf_path, compress=9)
    except RuntimeError:
        print "Ошибка сохранения классификатора в файл "+str(CL.clf_path)
        print sys.exc_info()
        
    else:
        session.add(CL)
        session.commit()
    finally:
        session.close()

def fit_classifier(dataset,target):
    u"""
    Переобучение классификатора при неверной классификации.
    Периодическое переобучение.
    """
    session = rwObjects.Session()
    
    try:
        CL = session.query(rwObjects.Classifier).filter(rwObjects.Classifier.id == 1).one()
    except rwObjects.sqlalchemy.orm.exc.NoResultFound:
        print "Классификатор не найден. "
        print sys.exc_info()
    else:
        print "Классификатор загружен."        
        clf = joblib.load(CL.clf_path)
        print clf.get_params
        
    
    vectorizer = TfidfVectorizer(tokenizer=tokenizer_1,use_idf=True,\
                            max_df=0.95, min_df=2,\
                            max_features=200)
    
    v = vectorizer.fit(dataset)
    joblib.dump(v, 'vectorizer.joblib', compress=9)
    v = v.transform(dataset)
    V = v.todense()
    
    terms = vectorizer.get_feature_names()
    
    for i in terms:
        print i

    clf.fit(V,target)
    
    try:
        joblib.dump(clf, CL.clf_path, compress=9)
    except RuntimeError:
        s = "Ошибка сохранения классификатора в файл "+str(CL.clf_path)
        s = s + str(sys.exc_info())
        
    else:
        session.add(CL)
        session.commit()
        s = "OK"
    finally:

        session.close()
    
    if debug:
        print u"Классификатор сохранен после обучения :" + str(s)

    
    return clf


def predict(clf,dataset):
    u"""
    Вызов классификатора.
    Возвращает категорию.
    """

    session = rwObjects.Session()
    
    try:
        CL = session.query(rwObjects.Classifier).filter(rwObjects.Classifier.id == 1).one()
    except rwObjects.sqlalchemy.orm.exc.NoResultFound:
        print "Классификатор не найден. "
        print sys.exc_info()
    else:
        print "Классификатор загружен."        
        clf = joblib.load(CL.clf_path)
        #print clf.get_params
        
    
    v = joblib.load('vectorizer.joblib')
    
    v = v.transform(dataset)
    V = v.todense()    
    Z = clf.predict(V)
    proba = clf.predict_proba(V)
    
    return proba,Z
    

def test():

    session = rwObjects.Session()
    target = {}
    
    try:
        query = session.query(rwObjects.Message)
    except rwObjects.sqlalchemy.orm.exc.NoResultFound:
        print 'No messages.'        
    else:
        messages = {}
        testmsg = {}
        
        for msg in query.all():
            
            email = json.loads(msg.data)
           
            for k in email.keys():
                email[k] = base64.b64decode(email[k])
            
            #print email.keys()     
            #print "---------------------------------"

            if msg.category == 0:
                testmsg[msg.uuid] = email
            else:
                messages[msg.uuid] = email
                target[msg.uuid] = msg.category

    finally:
        session.close()


    
    data = pd.DataFrame(messages)
    #train_text = data.loc['text']
    
    data = pd.DataFrame(testmsg)
    test_text = data.loc['text']
    
    cat = pd.Series(target)
    #print test_text.index[0]
    
    #cls = fit_classifier(train_text,cat)

    probe,Z = predict('',dataset=test_text)
    
    #print Z.size
    #print type(Z)
    #print probe
    #print type(probe)
    
    session = rwObjects.Session()
    m = {}
    c = {}
    
    for q in session.query(rwObjects.Message).all():
        m[q.uuid] = q
        
    
    for q in session.query(rwObjects.MessageCategory).all():
        c[q.id] = q
    
    
    for i in range(Z.size):
        print "От кого:"        
        print data.loc['from',data.columns[i]]
        print "Тема:"        
        print data.loc['subject',data.columns[i]]

        print "\nКатегория:"
        print c[Z[i]].name
        print "-----------------------------------"
        
    

test()


    
