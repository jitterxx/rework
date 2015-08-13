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


# split for words
def tokenizer_1(data):
    print 'data tokenizer: ', data
    morph = pymorphy2.MorphAnalyzer()

    splitter = re.compile('\W',re.I|re.U)
    
    clear = splitter.split(data)
    f = []
    for i in clear:
        #print i
        if 2 < len(i) < 20:
            word = morph.parse(i)[0]
            if word.tag.POS not in ('NUMR','PREP','CONJ','PRCL','INTJ'):
                f.append(word.normal_form)
                #print word.tag.POS
                print word.normal_form

    return f


# split for words
def tokenizer_2(data):
    print 'data tokenizer: ', data
    morph = pymorphy2.MorphAnalyzer()

    splitter = re.compile('\W',re.I|re.U)

    clear = splitter.split(data)
    f = []
    for i in clear:
        if 2 < len(i) < 20:
            print i
            f.append(i)

    return f


def init_classifier(session,clf_type):
    """
    Инициализация классификатора.
    :param clf_type: -- тип классификатора dtree или svc.
    :param session: -- ORM сессия rwObjects.Session()
    :return status -- статус операции
    :return CL -- объект класса rwObjects.Classifier()
    """
    status = ['','']

    if not session:
        raise Exception("Не передан параметр сессии.")

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
    except RuntimeError as e:
        status[0] = "ERROR"
        status[1] = "Ошибка сохранения классификатора в файл "+str(CL.clf_path)
        status[1] += str(e)
        
    else:
        session.add(CL)
        session.commit()
        status[0] = "OK"
    finally:
        session.close()
        
    return status,CL

def fit_classifier(clf_uuid,texts,answers):
    u"""
    Переобучение классификатора при неверной классификации.
    Периодическое переобучение.
    :param clf_uuid -- UUID классфикатора
    :param dataset -- словарь, где ключами являются идентификаторы текстов(сообщений), а значениями тексты которые
    необходимо классифицировать.
    :param target -- словарь, где ключами являются идентификаторы текстов(сообщений), а значениями класс или
    категория к которой относиться текст(сообщение).
    """
    session = rwObjects.Session()
    
    try:
        CL = session.query(rwObjects.Classifier).\
            filter(rwObjects.Classifier.uuid == clf_uuid).one()
    except rwObjects.sqlalchemy.orm.exc.NoResultFound:
        print "Классификатор не найден. "
        print sys.exc_info()
    except rwObjects.sqlalchemy.orm.exc.MultipleResults:
        print "Найдено больше одного классификатора с данным UUID: %s. "%clf_uuid
        print sys.exc_info()
    else:
        print "\nКлассификатор загружен."
        clf = joblib.load(CL.clf_path)
        print clf.get_params

    vectorizer = TfidfVectorizer(tokenizer=tokenizer_2)
    print "\nГотовим обучающий набор текстов."
    dataset = pd.DataFrame(texts)
    dataset = texts
    print dataset

    print "\nГотовим обучающий набор ответов для текстов."
    targets = pd.Series(answers)
    targets = answers
    print targets

    print "\nГотовим матрицу векторов ..."
    v = vectorizer.fit(dataset)

    print "\nСохраняем матрицу векторов."
    joblib.dump(v, CL.vec_path, compress=9)

    print "\nТрансформируем набор текстов для обучения."
    v = v.transform(dataset)
    V = v.todense()
    
    #terms = vectorizer.get_feature_names()
    
    #for i in terms:
     #   print i

    print "\nОбучаем классификатор..."
    clf.fit(V,targets)
    
    try:
        print "\nСохраняем классификатор в файл..."
        joblib.dump(clf, CL.clf_path, compress=9)
    except RuntimeError:
        s = "Ошибка сохранения классификатора в файл "+str(CL.clf_path)
        s += str(sys.exc_info())
        
    else:
        session.add(CL)
        session.commit()
        print "\nКлассификатор сохранен..."
        s = "OK"
    finally:
        session.close()
    
    print u"Классификатор сохранен после обучения :" + str(s)

    return s


def predict(clf_uuid,dataset):
    u"""
    Вызов классификатора.
    Возвращает категорию.
    """

    session = rwObjects.Session()
    
    try:
        CL = session.query(rwObjects.Classifier).\
                filter(rwObjects.Classifier.uuid == clf_uuid).one()
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
        
        
def check_conditions_for_classify():
    """
    Проверяет:
     -- сколько кастомных разделов в ДЗ создано, если меньше 2-х то не дает инициировать классификатор.
     -- сколько объектов с типами из FOR_CLASSIFY создано в системе и с какими кастомными разделами они связаны. Если
     в разделе нет ни одного документа, то не дает инициировать классификатор.

    :return: Список. Первый элемент статус - True/False проверки условий, второй - строка с комментарием.
    """
    session = rwObjects.Session()

    # Проверка кастомных разделов
    try:
        count = session.query(rwObjects.KnowledgeTree).filter(rwObjects.KnowledgeTree.type == 'custom').count()
    except Exception as e:
        return [False,"Ошибка доступа к базе классификаторов."]
    else:
        pass
    if count < 2:
        return [False,"Мало разделов в ДЗ."]

    # Проверка количества объектов из FOR_CLASSIFY. Должно быть >= количеству разделов.
    try:
        obj_count = session.query(rwObjects.DynamicObject).\
            filter(rwObjects.DynamicObject.obj_type.in_(rwObjects.FOR_CLASSIFY)).count()
    except Exception as e:
        return [False,"Ошибка доступа к объектам."]
    else:
        pass

    if obj_count < count:
        return [False,"Мало объектов для связи с ДЗ."]

    session.close()
    return [True,"OK"]



def retrain_classifier(session,clf_uuid):
    """
    Готовит данные для тренировки классификатора и проводит ее.
    :param session:
    :param clf_uuid:
    :return:
    """
    status = check_conditions_for_classify()
    if not status[0]:
        raise Exception("Не соблюдены условия для тренировки."+status[1])

    # Готовим данные для тренировки. Делаем выборку из Reference с типами из FOR_CLASSIFY привязанных к custom веткам
    #  ДЗ.
    # Отбираем кастом ветки
    custom_uuid = rwObjects.get_ktree_custom(session)[1]


    print custom_uuid

    # Делаем выборку всех DynamicObjects
    objects = list()
    try:
        res = session.query(rwObjects.DynamicObject).\
            filter(rwObjects.DynamicObject.obj_type.in_(rwObjects.FOR_CLASSIFY)).all()
    except Exception as e:
        return [False,"Ошибка доступа к базе классификаторов при обучении."]
    else:
        for r in res:
            objects.append(r.uuid)
    print objects

    # Ищем только связанные с custom узлами DO из нашего списка.
    try:
        ref,s = session.query(rwObjects.Reference).\
            filter(rwObjects.and_(rwObjects.Reference.source_uuid.in_(custom_uuid),
                                  rwObjects.Reference.target_uuid.in_(objects))).all()
    except Exception as e:
        return [False,"Ошибка доступа к базе классификаторов при обучении."]
    else:
        pass

    print ref


    return [True,""]


