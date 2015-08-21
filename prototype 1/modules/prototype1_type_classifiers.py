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
from email import utils


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


# split for words
def tokenizer_3(entry):

    #print 'Text: \n', entry['message_text']
    splitter=re.compile('\\W*',re.UNICODE)
    splitter1=re.compile(',',re.UNICODE)
    fd = dict()
    fl = list()

    # Извлечь и аннотировать слова из заголовка
    # Извлечь слова из текста
    try:
        summarywords=[s for s in splitter.split(entry) if 2 < len(s) < 20]
    except KeyError:
        print "KeyError."
    else:
        #print 'sum words: ',summarywords
        # Подсчитать количество слов, написанных заглавными буквами
        uc=0
        for w in summarywords:
            if re.sub("\d+","",w) == "":
                #print "Убираем :",w
                summarywords.remove(w)

        for i in range(len(summarywords)):
            w=summarywords[i]
            fd[w.lower()]=1
            fl.append(w.lower())
            if w.isupper(): uc+=1
            # Выделить в качестве признаков пары слов из резюме
            if i<len(summarywords)-1:
                j = i+1
                l = [summarywords[i],summarywords[j]]
                twowords = ' '.join(l)
                #print 'Two words: ',twowords,'\n'
                fd[twowords.lower()]=1
                fl.append(twowords.lower())

    # UPPERCASE – специальный признак, описывающий степень "крикливости"
    if (len(summarywords)) and (float(uc)/len(summarywords)>0.2):
        fd['UPPERCASE']=1
        fl.append('UPPERCASE')

    for w in fl:
        if re.sub("\d+","",w) == "":
            #print "Убираем :",w
            fl.remove(w)

    return fl

""" Функция извлечения признаков """
def email_specfeatures(entry,specwords):
    """ Функция для получения признаков(features) из текста
    Выделяет следующие признаки:
    1. email отправителя
    2. email получателей
    3. Слова из темы сообщения
    4. Все пары слов из темы сообщения
    5. Определенные сочетания из темы сообщения
    6. Слова из текста
    7. Все пары слов из текста
    8. Определенные пары слов из текста (specwords)
    9. Оригинальное время создания сообщения, только HH:MM\
    """

    #print 'Text: \n', entry['message_text']
    splitter=re.compile('\\W*',re.UNICODE)
    splitter1=re.compile(',',re.UNICODE)
    fd = dict()
    fl = list()

    # Извлечь и аннотировать слова из заголовка
    try:
        titlewords=[s.lower( ) for s in splitter.split(entry.__dict__['subject']) if 2 < len(s) < 20]
    except KeyError:
        pass
    else:
        for w in titlewords:
            #print 'Title: ',w,'\n'
            fd['subject:'+w]=1
            fl.append('subject:'+w)

    """
    # Извлечь и аннотировать слова из recipients
    try:
        recipients=[s.lower( ) for s in splitter1.split(entry['recipients'])if 2 < len(s) < 20]
    except KeyError:
        pass
    else:
        for w in recipients:
            #print 'Recipit: ',w,'\n'
            f['Recipients:'+w]=1

    # Извлечь и аннотировать слова из recipients_name
    recipients_name=[s.lower( ) for s in splitter1.split(entry['recipients_name'])
                    if len(s)>2 and len(s)<20]
    for w in recipients_name:
        #print 'Recipit name: ',w,'\n'
        f['Recipients_name:'+w]=1
    """

    # Извлечь слова из текста
    try:
        summarywords=[s for s in splitter.split(entry.__dict__['text_clear'])if 2 < len(s) < 20]
    except KeyError:
        print "KeyError."
    else:
        #print 'sum words: ',summarywords
        # Подсчитать количество слов, написанных заглавными буквами
        uc=0
        for w in summarywords:
            if re.sub("\d+","",w) == "":
                #print "Убираем :",w
                summarywords.remove(w)

        for i in range(len(summarywords)):
            w=summarywords[i]
            fd[w.lower()]=1
            fl.append(w.lower())
            if w.isupper(): uc+=1
            # Выделить в качестве признаков пары слов из резюме
            if i<len(summarywords)-1:
                j = i+1
                l = [summarywords[i],summarywords[j]]
                twowords = ' '.join(l)
                #print 'Two words: ',twowords,'\n'
                fd[twowords.lower()]=1
                fl.append(twowords.lower())

        #Извлекаем спец слова
        str = re.compile(r'[,.!?*"\']*',re.U|re.I)
        text = str.sub('',entry.__dict__['text_clear'])
        #print text,'\n'
        for key in specwords.keys():
            match = re.search(specwords[key],text,re.U|re.I)
            if match:
                #print key,specwords[key],'\n'
                w = key+':'+specwords[key]
                fd[w.lower()] = 1
                fl.append(w.lower())



    # Оставить информацию об авторе без изменения
    sender = extract_addresses(entry.__dict__['from'])
    for w in sender.keys():
        fd['from:' + w] = 1
        fd['from_name:'+sender[w]]=1
        fl.append('from:' + w)
        fl.append('from_name:'+sender[w])


    # UPPERCASE – специальный признак, описывающий степень "крикливости"
    if (len(summarywords)) and (float(uc)/len(summarywords)>0.2):
        fd['UPPERCASE']=1
        fl.append('UPPERCASE')

    for w in fl:
        if re.sub("\d+","",w) == "":
            #print "Убираем :",w
            fl.remove(w)

    return fd,fl


def extract_addresses(field):
    """
    :param field: Строка из которой надо извлечь имена и адреса. ФОрмат строки: ФИО_пробел_<email>,
    ФИО_пробел_<email>,... .
    :return addresses: Возвращает словарь в формате: key - email: value - ФИО или email, если ничего не было указано.
    """
    addresses = dict()
    a = re.split(",",str(field))
    for each in a:
        name, addr = utils.parseaddr(each)
        if name == "":
            addresses[addr] = addr
        else:
            addresses[addr] = name

    return addresses


def init_classifier(session,clf_obj,clf_type):
    """
    Инициализация классификатора.
    :param clf_type: тип классификатора dtree или svc.
    :param session: ORM сессия rwObjects.Session()
    :param clf_obj: объект класса Classifier

    :return status -- статус операции
    :return CL -- объект класса rwObjects.Classifier()
    """

    status = [True,'']

    if not session:
        raise Exception("Не передан параметр сессии.")

    if clf_type == "dtree":
        clf_obj.clf_type = 'dtree'
        clf = tree.DecisionTreeClassifier()
    elif clf_type == "svc":
        clf_obj.clf_type = 'svc'
        clf = svm.SVC(kernel='linear', C=1.0, probability=True)
    else:
        status[0] = False
        status[1] = "Указан неверный тип классификатора."
        clf_obj = None

    try:
        joblib.dump(clf, clf_obj.clf_path, compress=9)
    except RuntimeError as e:
        status[0] = False
        status[1] = "Ошибка сохранения классификатора в файл "+str(clf_obj.clf_path)
        status[1] += str(e)
        clf_obj = None

    return status,clf_obj


def fit_classifier(clf_uuid,texts,answers):
    """
    Переобучение классификатора при неверной классификации.
    Периодическое переобучение.

    :param clf_uuid: UUID классфикатора
    :param texts: словарь, где ключами являются идентификаторы текстов(сообщений), а значениями тексты которые
    необходимо классифицировать.
    :param answers: словарь, где ключами являются идентификаторы текстов(сообщений), а значениями класс или
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

    vectorizer = TfidfVectorizer(tokenizer=tokenizer_3)
    print "\nГотовим обучающий набор текстов."
    #dataset = pd.DataFrame(texts)
    dataset = texts
    print len(dataset)

    print "\nГотовим обучающий набор ответов для текстов."
    #targets = pd.Series(answers)
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
    CL.targets = ','.join(clf.classes_)

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

    #print "Что-тО : %s" % clf.classes_

    session.close()
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
    :param session: сессия ORM
    :param clf_uuid: UUID классификатора для обучения
    :return: список статуса. Первый элемент - статус операции True/Flase, второй - описание.
    """

    status = check_conditions_for_classify()
    if not status[0]:
        raise Exception("Не соблюдены условия для тренировки."+status[1])

    # Готовим данные для тренировки. Делаем выборку из Reference с типами из FOR_CLASSIFY привязанных к custom веткам
    #  ДЗ.
    # Отбираем кастом ветки
    custom = rwObjects.get_ktree_custom(session)
    print custom
    custom_uuid = custom.keys()

    print "Custom ветки ДЗ: "
    for i in custom.values():
        print i.name

    # Делаем выборку всех DynamicObjects
    objects = list()
    try:
        res = session.query(rwObjects.DynamicObject).\
            filter(rwObjects.DynamicObject.obj_type.in_(rwObjects.FOR_CLASSIFY)).all()
    except Exception as e:
        return [False,"Ошибка доступа к базе DO."]
    else:
        for r in res:
            objects.append(r.uuid)

    # Ищем только связанные с custom узлами DO из нашего списка.
    try:
        res = session.query(rwObjects.Reference).\
            filter(rwObjects.and_(rwObjects.Reference.source_uuid.in_(custom_uuid),
                                  rwObjects.Reference.target_uuid.in_(objects))).all()
    except Exception as e:
        return [False,"Ошибка доступа к базе Reference объектов."]
    else:
        pass

    print "Объекты для обучения: "
    # Готовим данные в объектах для обучения классификатора
    keys = list()
    dataset = list()
    targets = list()
    for r in res:
        obj = rwObjects.get_by_uuid(r.target_uuid)[0]
        obj.clear_text()
        keys.append(r.target_uuid)
        dataset.append(obj.text_clear)
        targets.append(r.source_uuid)
        print "Объект: ",r.target_uuid
        print "Текст длина в признаках: ",obj.text_clear
        print "Категория",r.source_uuid
        print ""

    print "Dataset len :",len(dataset)
    print "Key len :",len(keys)
    print "Targets len :",len(targets)

    fit_classifier('ed38261a-41cb-11e5-aae5-f46d04d35cbd', dataset, targets)

    return [True,""]


def save_classification_result(session,target_uuid,clf_uuid,probe):
    """
    Сохраняет результат автоматической классификации в бд.
    Если результаты авто классификации для такого классификатора и объекта уже есть в таблице, то перезаписываем их \
    новыми.

    :return:
    """

    try:
        res = session.query(rwObjects.ClassificationResult).\
            filter(rwObjects.and_(rwObjects.ClassificationResult.clf_uuid == clf_uuid,\
                                  rwObjects.ClassificationResult.target_uuid == target_uuid)).one()
    except Exception:
        print "Новая автоклассификация для %s" % target_uuid
        result = rwObjects.ClassificationResult()
    else:
        print "Перезаписываем автоклассификацию для %s" % target_uuid
        result = res

    result.clf_uuid = clf_uuid
    result.target_uuid = target_uuid
    result.probe = ",".join(map(str,probe[0]))
    result.status = "new"

    CL = rwObjects.get_by_uuid(clf_uuid)[0]
    result.categories = CL.targets

    try:
        session.add(result)
        session.commit()
    except Exception as e:
        return [False,str(e)]
    else:
        pass

    return [True,"OK"]


def autoclassify_all_notlinked_objects():
    """
    Проводит автоматическую классификацию всех не связанных ни с одним custom узлом Навигатора Знаний объектов класса
    DynamicObject. При этом используется текущие настройки и обученная модель классификатора. Если автоматическая
    классификация для объекта уже существует, то ее результаты будут перезаписаны.

    :return:
    """

    # Ищем все сообщения, их них отбираем только те которые не имеют связей с custom
    # т.е. имею пустое свойство self.__dict__['custom_category']
    session = rwObjects.Session()

    resp = session.query(rwObjects.DynamicObject).all()
    for obj in resp:
        obj.read(session)
        print obj.uuid
        print obj.__dict__['custom_category']
        if not obj.__dict__['custom_category'] and obj.obj_type in rwObjects.FOR_CLASSIFY:
            print "-------- Классифицируем объект : %s ---------" % obj.uuid
            obj = rwObjects.get_by_uuid(obj.uuid)[0]
            clf_uuid = "ed38261a-41cb-11e5-aae5-f46d04d35cbd"
            obj.clear_text()
            #print str(obj.text_plain)
            probe,Z = predict(clf_uuid,[obj.text_plain])
            print 'Вероятности : %s' % probe
            categories = rwObjects.get_ktree_custom(session)
            print 'Категория : %s' % categories[Z[0]].name
            print "--------------Классификация закончена.------------------"

            # Сохраняем результаты классификации
            status = save_classification_result(session,obj.uuid,clf_uuid,probe)
            if status[0]:
                print "Данные классификации сохранены."
            else:
                print "Данные классификации НЕ сохранены."

    session.close()


def clear_autoclassify(session,target_uuid):
    """
    Удаление данных автоматической классфикации.

    :param session: Сессия ORM
    :param target_uuid: UUID объекта автоматическую классификацию которого надо удалить.
    :return: ничего
    """

    try:
        resp = session.query(rwObjects.ClassificationResult).\
            filter(rwObjects.ClassificationResult.target_uuid == target_uuid).all()
    except Exception:
        return [False,"Не могу найти указанный объект."]
    else:
        pass

    try:
        for obj in resp:
            session.delete(obj)
        session.commit()
    except Exception:
        return [False,"Не могу удалить указанный объект : %s" % obj]
    else:
        pass

    return [True,"OK"]
