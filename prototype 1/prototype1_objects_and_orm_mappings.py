# -*- coding: utf-8 -*-
"""
Created on Wed Jul 22 16:23:47 2015

@author: sergey
"""

import sqlalchemy
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer
import uuid
import datetime
import json
import base64
from sklearn.externals import joblib
import inspect

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#Подключение БД
Base = sqlalchemy.ext.declarative.declarative_base()
Engine = sqlalchemy.create_engine('mysql://rework:HtdjhR123@localhost/rework?charset=utf8')
Session = sqlalchemy.orm.sessionmaker(bind=Engine)    

"""
Constants
"""
#Каналы взаимодействия reWork с внешним миром
rwChannel_type = ["email","facebook","phone","vk    "]
LEARN_PATH = "learn_machine/"

"""
reWork classes
"""

def create_tables():
    #Пересоздание таблиц
    Base.metadata.create_all(Engine)


class Company(Base):
    
    __tablename__ = 'companies'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50))
    name = sqlalchemy.Column(sqlalchemy.String(256))
    prefix = sqlalchemy.Column(sqlalchemy.String(10))
    employees = relationship("Employee", backref = "companies")


class Employee(Base):
    
    __tablename__ = 'employees'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50),default=uuid.uuid1())
    name = sqlalchemy.Column(sqlalchemy.String(256))
    surname = sqlalchemy.Column(sqlalchemy.String(256))
    login = sqlalchemy.Column(sqlalchemy.String(50))
    password = sqlalchemy.Column(sqlalchemy.String(20))
    comp_id = Column(Integer, ForeignKey('companies.id'))
    accounts = relationship("Account", backref = "employees")        

class Account(Base):
    """
        Объект для работы с аккаунтами Employees.
        Необходим для получения сообщений в объекты Message.
        -- Электронная почта. Acc_type = email
        -- Facebook. Acc_type = facebook
        
    """
    
    __tablename__ = 'accounts'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50),default=uuid.uuid1())
    acc_type = Column(sqlalchemy.String(256),default=rwChannel_type[0])
    server = sqlalchemy.Column(sqlalchemy.String(256))
    port = sqlalchemy.Column(sqlalchemy.String(6))
    login = sqlalchemy.Column(sqlalchemy.String(50))
    password = sqlalchemy.Column(sqlalchemy.String(20))
    dirs = Column(sqlalchemy.String(256), default="{'inbox':'INBOX','sent':'[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-'}")
    last_check = Column(sqlalchemy.DATETIME(),default = datetime.datetime.now())
    employee_id = Column(Integer, ForeignKey('employees.id'))

class Client(Base):

    
    __tablename__ = 'clients'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50),default=uuid.uuid1())
    name = sqlalchemy.Column(sqlalchemy.String(256))
    contacts = relationship("Contact", backref = "clients")

class Contact(Base):

    __tablename__ = 'contacts'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50),default=uuid.uuid1())
    name = sqlalchemy.Column(sqlalchemy.String(256))
    channels = relationship("Channel", backref = "contacts")
    client_id = Column(Integer, ForeignKey('clients.id'))
    

class Channel(Base):

    __tablename__ = 'channels'
    
    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    channel_type = Column(sqlalchemy.String(256),default=rwChannel_type[0])
    address = Column(sqlalchemy.String(256))
    contact_id = Column(Integer, ForeignKey('contacts.id'))

class Reference(Base):
    """
    Класс хранит данные о связях между объектами. 
    Значение аттрибута link равно 0, если это ребро между source и target.
    Заначение аттрибута link равно 1, если это событие создания target объекта.
    Source/target_type - содержат название таблицы __tablename__ хранения объекта.
    """
    
    __tablename__ = 'references'
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    source_uuid = sqlalchemy.Column(sqlalchemy.String(50))
    source_type = sqlalchemy.Column(sqlalchemy.String(30))
    source_id = sqlalchemy.Column(Integer)
    target_uuid = sqlalchemy.Column(sqlalchemy.String(50))
    target_type = sqlalchemy.Column(sqlalchemy.String(30))
    target_id = sqlalchemy.Column(Integer)
    link = Column(Integer,default = 0)
    timestamp = Column(sqlalchemy.DATETIME(),default = datetime.datetime.now())

class Event():
    """
    Класс аналогичен классу Reference, но значение аттрибута link равно 1.
    """

   
""" 
Бизнес объекты
"""

class Request(Base):

    __tablename__ = 'requests'
    
    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    subject = Column(sqlalchemy.String(256))
    content = Column(sqlalchemy.TEXT())
    status = Column(sqlalchemy.String(30))
    authors = Column(sqlalchemy.String(256))
    responsibles = Column(sqlalchemy.String(256))
    must_case = Column(sqlalchemy.String(256))
    content_sources = Column(sqlalchemy.String(256))
    parent = Column(sqlalchemy.String(256))
    childs = Column(sqlalchemy.String(256))
    

class Response(Base):
    
    __tablename__ = 'responses'
    
    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    subject = Column(sqlalchemy.String(256))
    content = Column(sqlalchemy.TEXT())
    authors = Column(sqlalchemy.String(256))
    responsibles = Column(sqlalchemy.String(256))
    content_sources = Column(sqlalchemy.String(256))
    parent = Column(sqlalchemy.String(256))
    childs = Column(sqlalchemy.String(256))


class Case(Base):
    
    __tablename__ = 'cases'
    
    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    category = Column(sqlalchemy.String(256))
    subject = Column(sqlalchemy.String(256))
    query = Column(sqlalchemy.TEXT())
    solve = Column(sqlalchemy.TEXT())
    algorithm = Column(sqlalchemy.TEXT())


class Used_case(Base):

    __tablename__ = 'used_cases'
    
    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    used_case = Column(sqlalchemy.String(256))
    rating = Column(sqlalchemy.String(256))
    used_for = Column(sqlalchemy.String(256))


class Message(Base):

    __tablename__ = 'messages'
    
    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    channel_type = Column(sqlalchemy.String(256))
    message_id = Column(sqlalchemy.String(256))
    viewed = Column(Integer,default=0)
    category = Column(Integer,default=0)
    data = Column(sqlalchemy.TEXT())
    
    def __init__(self):    
        self.uuid = uuid.uuid1()
        self.category = 0
        self.viewed = 0
    
    def is_exist_msg(self,session,msg_id):    
        """
        Проверяет есть ли в базе сообщение с таким же идентификатором.
        Если есть, возвращает True, если нет False.
        """
        check = False
        try:        
            session.query(Message).filter(Message.message_id == msg_id).one()
        except:
            print "Сообщений не найдено."
        else:
            print "Сообщение найдено."
            check = True
        
        return check
    
    def create_email(self,session,source,email,msg_id):
        """
        Функция создания объекта Message типа Email.
        На вход получает:
        session -- текущйи объект Session для работы с БД.
        Source -- параметры объекта Account через который было получено
        сообщение.
        Email - сообщение в виде dict {Заголовок поля: значение поля,...}. Из 
        преобразованного в словарь email.
        
        Выполняет действия:
        -- Заполняет свойство data объекта Message типа email. Данные сообщения
            пишуться в json форматe.
        -- Создает объект Reference - событие создания объекта(link = 1)

        """
        r_status = ["",""]
        t_status = ["",""]
        
        self.channel_type = rwChannel_type[0]
        #self.data = json.dumps(email)
        #print type(email)       
        #self.data = str(email)
        
        
        for k in email.keys():
            email[k] = base64.b64encode(email[k])
        
        self.data = json.dumps(email)
        
        
        #print self.data
        #print type(self.data)
        
        self.message_id = msg_id
        
        #Записываем объект
        session.add(self)

        try:
            session.commit()
        except RuntimeError:
            t_status[0] = 'ERROR'
            t_status[1] = 'Message object ID: ' + str(self.id) + ' NOT writed.'
        else:
            t_status[0] = 'OK'
            t_status[1] = 'Message object ID: ' + str(self.id) + ' writed.'
            t_status[1] = t_status[1] + '\n ' + str(self.uuid)
            

        """ Создаем Reference на новый объект """        
        ref = Reference(source_uuid = source['uuid'], 
                        source_type = source['source_type'],
                        source_id = source['id'],
                        target_uuid = self.uuid,
                        target_type = self.__tablename__,
                        target_id = self.id,
                        link = 1)
        
        
        #Записываем объект
        session.add(ref)
        try:
            session.commit()
        except RuntimeError:
            r_status[0] = 'ERROR'
            r_status[1] = 'Reference object ID: ' + str(ref.id) + ' NOT writed.'
        else:
            r_status[0] = 'OK'
            r_status[1] = 'Reference object ID: ' + str(ref.id) + ' writed.'
        
        return t_status,r_status


def get_email_message(session,uuid):
    """
    Возвращает распакованные email сообщения по списку переданных UUID.
    Параметр uuid -- список (List) uuid сообщений которые необходимо распаковать.
    """
    messages = {}
           
    if uuid == None:
        #Получить все сообщения
        pass
    else:
        #Получить сообщения по списку UUID
        try:
            query = session.query(Message).filter(Message.uuid.in_(uuid))
        except sqlalchemy.orm.exc.NoResultFound:
            print 'No emails.'        
        else:
            
            for msg in query.all():
                
                email = json.loads(msg.data)
               
                for k in email.keys():
                    email[k] = base64.b64decode(email[k])
                
                #print email.keys()     
                #print "---------------------------------"
    
                    messages[msg.uuid] = email
    
        finally:
            session.close()
    
    return messages

class Classifier(Base):
    """
    Хранит список классификаторов.
    """
    
    __tablename__ = "classifiers"
    
    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    description = Column(sqlalchemy.String(256))
    clf_path = Column(sqlalchemy.String(256))
    clf_type = Column(sqlalchemy.String(256))
    vec_path = Column(sqlalchemy.String(256))
    
    def __init__(self):
        self.uuid = uuid.uuid1()
        self.clf_path = LEARN_PATH + str(self.uuid) + str("_classifier.joblib.pkl")
        self.vec_path = LEARN_PATH + str(self.uuid) + str("_vectorizer.joblib.pkl")
    

   

class MessageCategory(Base):
    """
    Типы сообщений. Используется для классификации.
    """
    
    __tablename__ = "message_category"

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    name = Column(sqlalchemy.String(256))
    description = Column(sqlalchemy.String(256))
    
    def __init__(self):
        self.uuid = uuid.uuid1()
 
class KnowledgeTree(Base):
    """
    Иерархическая структура знаний.
    Каждый узел представляет собой описание темы с параметрами.
    
    """

    __tablename__ = "knowledge_tree"
    childs = []
    parent = []
    

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50),default=uuid.uuid1())
    parent_id = Column(sqlalchemy.String(50))
    name = Column(sqlalchemy.String(256))
    tags = Column(sqlalchemy.String(256))
    description = Column(sqlalchemy.String(256))
    expert = Column(sqlalchemy.String(256))
    tags_clf = Column(sqlalchemy.String(256),default = "")

    def __init__(self):
        self.uuid = uuid.uuid1()
    
    def return_childs(self,session,lvl,parent_id):


        string = ""
        obj = []
        
        try:
            query = session.query(KnowledgeTree).\
                filter(KnowledgeTree.parent_id == parent_id)
           
        except sqlalchemy.orm.exc.NoResultFound:
            print "Больше нет дочерних узлов."
            string = "1"
        else:
            for each in query.all():
                #print each.id, each.name, each.parent_id
                string = string + "|" + lvl*"--" + str(each.name) + "\n"
                obj.append(each.id)
                s,o = self.return_childs(session,lvl+1,each.id)
                string = string + s
                
                if o:                
                    obj.append(o)
        
        return string,obj
        
    
    def return_full_tree(self,outformat):
        """
        Возвращает дерево в виде строки или словаря, согласно формату.
        Строка - только названия узлов.
        Словарь - все свойства.
        """
        
        session = Session()
        s = ""
        ss,obj = self.return_childs(session,0,0)
        s = s + ss
        session.close()
        
        return s,obj
        
        
        
        
        

def test():
    
    session = Session()
    
    try:
        company1 = Company(uuid = str(uuid.uuid1()),name = 'Test company', prefix = 'tc_')

    except RuntimeError:
        print sys.exc_info()
        session.close()
        
    else:
        company1.employees = [Employee(name = 'Второй ',surname = 'Сотрудник')]
        company1.employees.append(Employee(name = 'Третий ',surname = 'Сотрудник'))
        
        
        session.add(company1)
        session.commit()
        
        company1 = Company(uuid = str(uuid.uuid1()),name = '2 Test company', prefix = '2tc_')
        session.add(company1)
        
        session.commit()
        
        for inst in session.query(Company).all():
            print inst.id,inst.name,inst.uuid
        
        
        for inst in session.query(Employee).all():
            print inst.id,inst.name,inst.uuid, inst.comp_id
        
    
        email_data = {'From':'sergey@reshim.com','Subj':'Проверка','Text':'Я хочу все знать!\
                        "Но не все", а только часть.?%%№;!'}
       
        source = {'uuid':'0000', 'source_type':'system','id':0} 
        
        msg = Message()
        msg.create_email(session,source,email_data)
        
        msg1 = Message()
        try:        
            msg1 = session.query(Message).filter(Message.id == 2).one()
        except sqlalchemy.orm.exc.NoResultFound:
            print 'No records.'
        else:
            email = json.loads(msg1.data)
            print email['From'], email['Text']
        finally:
            session.close()
        

def get_by_uuid(uuid):
    """

    Возвращает объект любого типа по его uuid.
    
    В качестве параметров ждет UUID объекта.
    Существование объекта определяется по наличию связи в References со статусом 1.
    Параметры объекта определяются через его тип.
    
    Возвращает:
    -- сам объект 
    -- статус в виде списка. Первый элемент True/False в зависимости от итога
    операций и сообщение во втором элемента (пустой если прошло успешно).
    
    """

    session = Session()
    obj_class = {}
    status = [True,""]
    #print sys.modules[__name__]
    #print inspect.getmembers(sys.modules[__name__], inspect.isclass)
    
    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        try:
            obj.__tablename__
        except AttributeError:
            status[0] = False
            status[1] = "Нет класса для этого объекта. AttributeError. "

        else:
               obj_class[obj.__tablename__] = name
               #print name,type(name)
               #print obj,type(obj)
               #print obj.__tablename__
    
    if not status:
        raise
    
    #print "obj_class :",obj_class

    try:
        query = session.query(Reference).\
                filter(sqlalchemy.and_(Reference.target_uuid == uuid,\
                        Reference.link == 1)).first()
    except RuntimeError:
         status[0] = False
         status[1] = "Нет объекта в References. RuntimeError. "
        #print "нет объекта"
    else:
        t = query.target_type                        
            
        #print "type(query) :",type(query)
        #print "query type : ",t 
        #print "obj_class[t] :",obj_class[t]
        
        kk = globals()[obj_class[t]]
        #print kk,type(kk)

    if not status:
        raise
        
    try:
        obj = session.query(kk).filter_by(uuid = uuid).first()
    except RuntimeError:
         status[0] = False
         status[1] = "Не могу найти объект в базе. RuntimeError. "
    else:
        pass
    
    return obj,status