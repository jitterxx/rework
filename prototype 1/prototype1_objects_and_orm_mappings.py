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
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

#Подключение БД
Base = sqlalchemy.ext.declarative.declarative_base()
Engine = sqlalchemy.create_engine('mysql://rework:HtdjhR123@localhost/rework?charset=utf8')
Session = sqlalchemy.orm.sessionmaker(bind=Engine)    

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
    acc_type = sqlalchemy.Column(sqlalchemy.String(256))
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
    
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50),default=uuid.uuid1())
    channel_type = sqlalchemy.Column(sqlalchemy.String(256))
    address = sqlalchemy.Column(sqlalchemy.String(256))
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
    data = Column(sqlalchemy.TEXT())
    
    def create_email(self,session,source,email):
        r_status = ["",""]
        t_status = ["",""]
        """
        Функция создания объекта Message типа Email.
        На вход получает dict - {Заголовок поля: значение поля,...}. Из 
        преобразованного в словарь email.
        
        1. Заполняет свойства объекта Message типа email. Данные сообщения
            пишуться в json формат для облегчения хранения.
        2. Создает Reference событие создания объекта(link = 1)

        """
        
        self.channel_type = 'email'
        self.data = json.dumps(email)
        
        #Записываем объект
        session.add(self)
        session.commit()
        try:
            session.commit()
        except RuntimeError:
            t_status[0] = 'ERROR'
            t_status[1] = 'Message object ID: ' + str(self.id) + ' NOT writed.'
        else:
            t_status[0] = 'OK'
            t_status[1] = 'Message object ID: ' + str(self.id) + ' writed.'

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
        

#test()



