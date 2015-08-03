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
from sklearn import svm
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


def init_classifier(clf_type):
    u"""
    Инициализация классификатора.
    """
    status = ['','']
    session = rwObjects.Session()
    CL = rwObjects.Classifier()
    
    if clf_type == "dtree":
        CL.clf_type = 'dtree'
        clf = tree.DecisionTreeClassifier()
    elif clf_type == "svc":
        CL.clf_type = 'svc'
        clf = svm.SVC(kernel='linear', C=1.0, probability=True)
    else:
        status[0] = "ERROR"
        status[1] = "Указан неверный тип классификатора."
        
        
    try:
        joblib.dump(clf, CL.clf_path, compress=9)
    except RuntimeError:
        status[0] = "ERROR"
        status[1] = "Ошибка сохранения классификатора в файл "+str(CL.clf_path)
        status[1] = status[1] + str(sys.exc_info())
        
    else:
        session.add(CL)
        session.commit()
        status[0] = "OK"
    finally:
        session.close()
        
    return status

def fit_classifier(clf_id,dataset,target):
    u"""
    Переобучение классификатора при неверной классификации.
    Периодическое переобучение.
    """
    session = rwObjects.Session()
    
    try:
        CL = session.query(rwObjects.Classifier).\
                filter(rwObjects.Classifier.id == clf_id).one()
    except rwObjects.sqlalchemy.orm.exc.NoResultFound:
        print "Классификатор не найден. "
        print sys.exc_info()
    else:
        print "Классификатор загружен."        
        clf = joblib.load(CL.clf_path)
        #print clf.get_params
        
    
    vectorizer = TfidfVectorizer(tokenizer=tokenizer_1,use_idf=True,\
                            max_df=0.95, min_df=2,\
                            max_features=200)
    
    v = vectorizer.fit(dataset)
    
    joblib.dump(v, CL.vec_path, compress=9)
    v = v.transform(dataset)
    V = v.todense()
    
    #terms = vectorizer.get_feature_names()
    
    #for i in terms:
     #   print i

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

    
    return s


def predict(clf_id,dataset):
    u"""
    Вызов классификатора.
    Возвращает категорию.
    """

    session = rwObjects.Session()
    
    try:
        CL = session.query(rwObjects.Classifier).\
                filter(rwObjects.Classifier.id == clf_id).one()
    except rwObjects.sqlalchemy.orm.exc.NoResultFound:
        print "Классификатор не найден. "
        print sys.exc_info()
    else:
        print "Классификатор загружен."        
        clf = joblib.load(CL.clf_path)
        #print clf.get_params
        
    
    v = joblib.load(CL.vec_path)
    
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
    train_text = data.loc['text']
    
    data = pd.DataFrame(testmsg)
    test_text = data.loc['text']
    
    cat = pd.Series(target)
    #print test_text.index[0]
    
    status = fit_classifier(8,train_text,cat)

    probe,Z = predict(8,dataset=test_text)
    
    print Z
    #print type(Z)
    print probe
    #print type(probe)
    
    print "Проверка SVM"
    
    
    status = fit_classifier(7,train_text,cat)

    probe1,Z1 = predict(7,dataset=test_text)
    
    print Z1
    print probe1
    
    session = rwObjects.Session()
    c = {}
    
    for q in session.query(rwObjects.MessageCategory).all():
        c[q.id] = q
    

    for i in range(Z.size):
        print "От кого:"
        print testmsg[data.columns[i]]['from']
        print "Тема:"        
        print testmsg[data.columns[i]]['subject']

        print "\n Определена категория DTree:"
        print c[Z[i]].name
        print "\n Определена категория SVC:"
        print c[Z1[i]].name
        
        
        print "-----------------------------------"
        
        
    
    mmmm = rwObjects.get_email_message(session,['e9b5f246-3614-11e5-b267-f46d04d35cbd',
    '457c878e-363d-11e5-83e3-f46d04d35cbd'])
    
    
    #print mmmm['457c878e-363d-11e5-83e3-f46d04d35cbd']['text']
    
    
        


    
