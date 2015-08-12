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
from sqlalchemy import or_,and_,desc
import uuid
import datetime
import json
import base64
from sklearn.externals import joblib
import inspect
import prototype1_queue_module as rwQueue
import pymongo
import re

import sys

reload(sys)
sys.setdefaultencoding("utf-8")


"""
Constants
"""
# Каналы взаимодействия reWork с внешним миром
rwChannel_type = ["email", "facebook", "phone", "vk"]
LEARN_PATH = "learn_machine/"
mongo_uri = 'mongodb://localhost/rsa'
sql_uri = 'mysql://rework:HtdjhR123@localhost/rework?charset=utf8'
STANDARD_OBJECTS_TYPES = ['accounts','employees','message']

"""
Подключение БД и MongoDB
"""
Base = sqlalchemy.ext.declarative.declarative_base()
Engine = sqlalchemy.create_engine(sql_uri)
Session = sqlalchemy.orm.sessionmaker(bind=Engine)


Mongo_client = pymongo.MongoClient(mongo_uri)
Mongo_db = Mongo_client.get_default_database()



"""
reWork classes
"""


def create_tables():
    # Пересоздание таблиц
    Base.metadata.create_all(Engine)


def create_company():
    """
    Служебная функция для создания новой компании и суперпользователя 
    (администратора) всех настроек для этой компании.
    
    """

    session = Session()

    company_name = unicode(raw_input("Введите название компании: "))
    company_prefix = unicode(raw_input("Введите префикс (до 3-х символов): "))

    new_company = Company()
    new_company.name = str(company_name)
    new_company.prefix = str(company_prefix)

    # Проверить веденные данные
    s = new_company.check()

    if not s[0]:
        raise Exception(s[1])
    else:
        session.add(new_company)

    try:
        session.commit()
    except RuntimeError:
        print "Ошибка создания компании."
    else:
        print "Компания \"" + str(new_company.name) + "\" внесена в базу."

    # Записываем событие создания Компании
    ref = Reference(source_uuid="reWork",
                    source_type="companies",
                    source_id=1,
                    target_uuid=new_company.uuid,
                    target_type=new_company.__tablename__,
                    target_id=new_company.id,
                    link=1)
    ref.create(session)

    # Создаем суперпользователя для компании
    user_login = "superuser@" + new_company.prefix
    print "Создаем администратора Компании \"" + new_company.name + "\" :"
    user_name = unicode(raw_input("Введите Имя []: "))
    user_surname = unicode(raw_input("Введите Фамилию []: "))
    login = unicode(raw_input("Введите login[" + user_login + "]: "))
    if login:
        user_login = login
    user_pass = unicode(raw_input("Введите пароль: "))

    superuser = Employee()
    superuser.login = user_login
    superuser.name = user_name
    superuser.password = user_pass
    superuser.surname = user_surname
    superuser.comp_id = new_company.id

    # Проверить введенные данные. Проверяется логин
    s = superuser.check()

    if not s[0]:
        raise Exception(s[1])
    else:
        session.add(superuser)

    try:
        session.commit()
    except RuntimeError:
        print "Ошибка создания пользователя."
    else:
        print "Пользователь \"" + str(superuser.login) + "\" внесен в базу."

    # Записываем событие создания Компании
    ref = Reference(source_uuid="reWork",
                    source_type="companies",
                    source_id=1,
                    target_uuid=superuser.uuid,
                    target_type=superuser.__tablename__,
                    target_id=superuser.id,
                    link=1)
    ref.create(session)

    ref = Reference(source_uuid=new_company.uuid,
                    source_type=new_company.__tablename__,
                    source_id=new_company.id,
                    target_uuid=superuser.uuid,
                    target_type=superuser.__tablename__,
                    target_id=superuser.id,
                    link=0)
    ref.create(session)


class rw_parent():
    NAME = ""

    EDIT_FIELDS = []
    ALL_FIELDS = {}
    VIEW_FIELDS = []
    ADD_FIELDS = []
    SHORT_VIEW_FIELDS = []

    def get_attrs(self):
        attrs = [name for name in self.__dict__ if not name.startswith('_')]

        return attrs

    def get_fields(self):
        """
        Возвращает три структуры из констант READONLY_FIELDS, VIEW_FIELDS.
        -- Первая view -- словарь (Dict) содержит название поля объекта, 
            подписей к полю для отображения.
        -- Втоорая view_keys -- список (List) содержит названия полей объекта, 
            определяет порядок отображения полей из словаря полей view.
        -- Третий readonly - список (List) полей объекта недоступных для 
            редактирования.
        """

        return [self.ALL_FIELDS, self.VIEW_FIELDS, self.EDIT_FIELDS, self.ADD_FIELDS]

    def read(self):
        """
        Заглушка для чтения динамических объектов.
        :return: самого себя
        """
        self.__dict__['obj_type'] = self.__tablename__

    def check(self):
        """
        Проверка на существование объекта. Это заглушка в родительском классе.
        В классе при необходимости должна быть переписана на реальную проверку.
        :return : Всегда возвращает список -- [True,"OK"]
        """
        return [True,"OK"]




class Company(Base, rw_parent):
    __tablename__ = 'companies'
    NAME = "Компания"

    EDIT_FIELDS = ['name', 'prefix']
    ALL_FIELDS = {'name': 'Имя', 'prefix': 'домен', 'uuid': 'Идентификатор',
                  'id': 'id'}
    VIEW_FIELDS = ['name', 'prefix']
    ADD_FIELDS = ['name', 'prefix']

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50))
    name = sqlalchemy.Column(sqlalchemy.String(256))
    prefix = sqlalchemy.Column(sqlalchemy.String(10))
    employees = relationship("Employee", backref="companies")

    def __init__(self):
        self.uuid = uuid.uuid1()

    def check(self):
        """
       Проверка на существование компании с таким именем или префиксом.
       Если не найдено совпадений возвращает в первом элементе True, иначе False.
       Второй элемент содержит описание ошибки.
       """

        status = [True, "Совпадений не найдено."]

        print self.name
        print self.prefix

        session = Session()

        try:
            session.query(Company.prefix).filter(Company.prefix == self.prefix).one()
        except sqlalchemy.orm.exc.NoResultFound:
            print "Перфикс не найден."

        except sqlalchemy.orm.exc.MultipleResultsFound:
            status = [False, "Такой префикс существует. Задайте другой."]
            print "Перфикс найден."
        else:
            status = [False, "Такой префикс существует. Задайте другой."]

        session.close()

        return status


def get_company_by_id(cid):
    """
    Возвращает объект Компания по его id
    """
    session = Session()
    company = session.query(Company).filter_by(id=cid).first()
    session.close()
    return company


class Employee(Base, rw_parent):
    EDIT_FIELDS = ['name', 'surname', 'password']
    ALL_FIELDS = {'name': 'Имя', 'surname': 'Фамилия',
                  'login': 'Логин', 'password': 'Пароль',
                  'comp_id': 'Компания', 'id': 'id', 'uuid': 'uuid'}
    VIEW_FIELDS = ['name', 'surname', 'login', 'password']
    ADD_FIELDS = ['name', 'surname', 'login', 'password']
    NAME = "Сотрудник"

    __tablename__ = 'employees'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50), default=uuid.uuid1())
    name = sqlalchemy.Column(sqlalchemy.String(256))
    surname = sqlalchemy.Column(sqlalchemy.String(256))
    login = sqlalchemy.Column(sqlalchemy.String(50))
    password = sqlalchemy.Column(sqlalchemy.String(20))
    comp_id = Column(Integer, ForeignKey('companies.id'))
    accounts = relationship("Account", backref="employees")

    def __init__(self):
        self.uuid = uuid.uuid1()

    def check(self):
        """
       Проверка на существование пользователь с таким login.
       Если не найдено совпадений возвращает в первом элементе True, иначе False.
       Второй элемент содержит описание ошибки.
       """

        status = [True, "Совпадений не найдено."]

        session = Session()
        try:
            session.query(Employee.login).filter(Employee.login == self.login).one()

        except sqlalchemy.orm.exc.NoResultFound:
            print "Логин не найден."

        except sqlalchemy.orm.exc.MultipleResultsFound:
            status = [False, "Такой логин существует. Задайте другой."]
            print "Логин найден."
        else:
            status = [False, "Такой логин существует. Задайте другой."]

        session.close()

        return status


def get_employee_by_login(login):
    """
    Получить данные пользователя по логину.
    
    """

    session = Session()

    try:
        user = session.query(Employee).filter(Employee.login == login).one()
    except  sqlalchemy.orm.exc.NoResultFound:
        print "Пользователь не найден"
        return None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        # status = [False,"Такой логин существует. Задайте другой."]
        print "Найдено множество пользователей."
    else:
        print "Пользователь найден"
        return user

    session.close()


class Account(Base, rw_parent):
    """
        Объект для работы с аккаунтами Employees.
        Записи необходимы для получения сообщений.
        -- Электронная почта. Acc_type = email
        -- Facebook. Acc_type = facebook
        
    """

    __tablename__ = 'accounts'
    DIRS = {'Yandex':'{"inbox": "INBOX", "sent": "&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"}',
                     'Gmail':'{"inbox":"INBOX","sent":"[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"}'}

    ALL_FIELDS = {
    "id":"id",
    "uuid":"Идентификатор",
    "acc_type":"Тип аккаунта",
    "description":"Описание",
    "server":"Имя сервера",
    "port":"Порт",
    "login":"Логин",
    "password":"Пароль",
    "dirs":"Каталоги для проверки",
    "last_check":"Дата и время последней проверки",
    "employee_id":"Связан с сотрудником"
    }
    VIEW_FIELDS = ['acc_type', 'description','server','port','dirs','login', 'password','last_check']
    ADD_FIELDS = ['acc_type', 'description','server','port','dirs','login', 'password']
    EDIT_FIELDS = ['description','server','port','dirs','login', 'password']
    SHORT_VIEW_FIELDS = ['login','acc_type', 'description']
    NAME = "Аккаунт"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50))
    acc_type = Column(sqlalchemy.String(256), default=rwChannel_type[0])
    description = sqlalchemy.Column(sqlalchemy.String(256))
    server = sqlalchemy.Column(sqlalchemy.String(256))
    port = sqlalchemy.Column(sqlalchemy.String(6))
    login = sqlalchemy.Column(sqlalchemy.String(50))
    password = sqlalchemy.Column(sqlalchemy.String(20))
    dirs = Column(sqlalchemy.String(256),default=DIRS["Gmail"])
    last_check = Column(sqlalchemy.DATETIME(), default=datetime.datetime.now())
    employee_id = Column(Integer, ForeignKey('employees.id'))

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.acc_type = rwChannel_type[0]
        self.description = ""
        self.server = ""
        self.port = ""
        self.login = ""
        self.password = ""
        self.dirs = self.DIRS["Gmail"]
        self.last_check = datetime.datetime.now()

    def check(self):

        return [True,""]


class Client(Base, rw_parent):
    __tablename__ = 'clients'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50), default=uuid.uuid1())
    name = sqlalchemy.Column(sqlalchemy.String(256))
    contacts = relationship("Contact", backref="clients")


class Contact(Base, rw_parent):
    __tablename__ = 'contacts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50), default=uuid.uuid1())
    name = sqlalchemy.Column(sqlalchemy.String(256))
    channels = relationship("Channel", backref="contacts")
    client_id = Column(Integer, ForeignKey('clients.id'))


class Channel(Base, rw_parent):
    __tablename__ = 'channels'

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    channel_type = Column(sqlalchemy.String(256), default=rwChannel_type[0])
    address = Column(sqlalchemy.String(256))
    contact_id = Column(Integer, ForeignKey('contacts.id'))


class Reference(Base, rw_parent):
    """
    Класс хранит данные о связях между объектами. 
    Значение аттрибута link равно 0, если это ребро между source и target.
    Заначение аттрибута link равно 1, если это событие создания target объекта.
    Source/target_type - содержат название таблицы __tablename__ хранения объекта.
    """

    NAME = "Событие"

    EDIT_FIELDS = []
    ALL_FIELDS = {'id': 'id',
                  'source_uuid': 'Кто',
                  'source_type': 'Тип',
                  'source_id': 'id',
                  'target_uuid': 'С чем',
                  'target_type': 'Тип',
                  'target_id': 'id',
                  'link': 'Связь',
                  'timestamp': 'Время'}
    VIEW_FIELDS = ['timestamp', 'source_uuid', 'link', 'target_uuid']
    ADD_FIELDS = []

    __tablename__ = 'references'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    source_uuid = sqlalchemy.Column(sqlalchemy.String(50))
    source_type = sqlalchemy.Column(sqlalchemy.String(30))
    source_id = sqlalchemy.Column(Integer)
    target_uuid = sqlalchemy.Column(sqlalchemy.String(50))
    target_type = sqlalchemy.Column(sqlalchemy.String(30))
    target_id = sqlalchemy.Column(Integer)
    link = Column(Integer, default=0)
    timestamp = Column(sqlalchemy.DATETIME(), default=datetime.datetime.now())

    def create(self, session):
        r_status = [True, ""]
        # Записываем объект
        session.add(self)
        try:
            session.commit()
        except RuntimeError:
            r_status[0] = False
            r_status[1] = 'Reference object ID: ' + str(self.id) + ' NOT writed.'
        else:
            r_status[0] = True
            r_status[1] = 'Reference object ID: ' + str(self.id) + ' writed.'
            if self.link == 1:
                """ Вызываем функцию проверки автоматических правил при появлении нового объекта"""
                rwQueue.apply_rules.delay(self.source_uuid,self.source_type,self.target_uuid,self.target_type)

        return r_status


class Event():
    """
    Класс аналогичен классу Reference, но значение аттрибута link равно 1.
    """


""" 
Бизнес объекты
"""


class Request(Base, rw_parent):
    __tablename__ = 'requests'

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    subject = Column(sqlalchemy.String(256))
    content = Column(sqlalchemy.TEXT())
    status = Column(sqlalchemy.String(30))
    authors = Column(sqlalchemy.String(256))
    responsibles = Column(sqlalchemy.String(256))
    must_case = Column(sqlalchemy.String(256))
    content_sources = Column(sqlalchemy.String(256))
    parent = Column(sqlalchemy.String(256))
    childs = Column(sqlalchemy.String(256))


class Response(Base, rw_parent):
    __tablename__ = 'responses'

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    subject = Column(sqlalchemy.String(256))
    content = Column(sqlalchemy.TEXT())
    authors = Column(sqlalchemy.String(256))
    responsibles = Column(sqlalchemy.String(256))
    content_sources = Column(sqlalchemy.String(256))
    parent = Column(sqlalchemy.String(256))
    childs = Column(sqlalchemy.String(256))


class Case(Base, rw_parent):
    __tablename__ = 'cases'

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    category = Column(sqlalchemy.String(256))
    subject = Column(sqlalchemy.String(256))
    query = Column(sqlalchemy.TEXT())
    solve = Column(sqlalchemy.TEXT())
    algorithm = Column(sqlalchemy.TEXT())


class Used_case(Base, rw_parent):
    __tablename__ = 'used_cases'

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    used_case = Column(sqlalchemy.String(256))
    rating = Column(sqlalchemy.String(256))
    used_for = Column(sqlalchemy.String(256))


class DynamicObject(Base,rw_parent):
    """
    Динамические объекты.
    В SQL базе только параметры, остальное в mongodb.
    Доступ к объектам через встроенные функции класс read, write, они дополняют существующий экземпляр свойствами из
    MongoDB.
    """

    __tablename__ = 'dynamic_object'
    NAME = "Бизнес объекты"

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    obj_type = Column(sqlalchemy.String(256))
    collection = Column(sqlalchemy.String(256))
    timestamp = Column(sqlalchemy.DATETIME(), default=datetime.datetime.now())

    def __init__(self):
        """
        Инициализация объекта происходит с одновременным заполнением свойств.
        :param data: словарь со значениями для свойств класса.
        :return: возвращает объект типа DynamicObject
        """
        self.uuid = uuid.uuid1()

    def write(self,session,obj):
        session_flag = False

        if not session:
            session = Session()
            session_flag = True

        try:
            self.obj_type = obj['obj_type']
        except Exception as e:
            raise("Не указан тип объекта в свойстве obj_type. " + str(e))
        else:
            pass

        collection = Mongo_db[obj['obj_type']]
        obj['uuid'] = self.uuid.__str__()
        obj['_id'] = self.uuid.__str__()
        self.collection = obj['obj_type']

        try:
            record_id = collection.insert_one(obj).inserted_id
        except Exception as e:
            raise("Не удалось сохранить объект в базе MongoDB. " + str(e))
        else:
            print "Объект сохранен " + str(record_id)

            """
            Записываем в sql базу данные о DynamicObject
            """
            # Записываем DynamicObject
            session.add(self)
            status = [True,""]
            try:
                session.commit()
            except Exception:
                raise([False,"Message object ID: " + str(self.id) + " NOT writed."])
            else:
                status[0] = True
                status[1] = 'Message object ID: ' + str(self.id) + ' writed.'

        if session_flag:
            session.close()

        return status

    def read(self):
        """
        Прочитать объект из базы.
        :param uuid: глобальный идентификатор объекта в системе. Равен _id в mongoDB.
        :param obj_type: указывает на коллекцию в которой находится объект
        :return: возвращает объект типа DynamicObject с заполненными полями. Если не найден, возвращает в None.
        """
        self.VIEW_FIELDS = []
        #Определяем название коллекции в которой находиться объект
        collection = Mongo_db[self.collection]
        query = {'uuid':str(self.uuid)}

        try:
            obj = collection.find_one(query)
        except Exception as e:
            raise([False,"Ошибка чтения объекта. " + str(e)])
        else:
            #Заполняем параметры
            #print "\nVIEW FIELDS ",self.VIEW_FIELDS
            #Собираем в объект все ключи и их значения
            for key in obj.keys():
                self.__dict__[key] = obj[key]
                self.ALL_FIELDS[key] = key
            #print "\nВсе ключи ",self.__dict__.keys()

            if self.obj_type == 'message':
                view_f = ['from','to','cc','bcc', 'subject', 'raw_text_html']
                self.NAME = 'Сообщение'
                self.ALL_FIELDS['from'] = 'От кого'
                self.ALL_FIELDS['to'] = 'Кому'
                self.ALL_FIELDS['cc'] = 'Копия'
                self.ALL_FIELDS['bcc'] = 'Скрытая копия'
                self.ALL_FIELDS['subject'] = 'Тема'
                self.ALL_FIELDS['raw_text_html'] = 'Текст'
                self.SHORT_VIEW_FIELDS = ['from','to','subject']


            #Удаляем ключи не присутствующие в данном объекте
            for key in view_f:
                if key in self.__dict__.keys():
                    self.VIEW_FIELDS.append(key)

            #print "\n NEW VIEW FIELDS ",self.VIEW_FIELDS


    def check(self,query):
        """
        Проверяем наличие записей в базе с указанными параметрами.
        :param query: Параметры в виде словаря.
        :return True, если что-то нашлось, False - если совпадений не найдено.
        """
        collection = Mongo_db[self.collection]
        response = collection.find_one(query)
        if response:
            return True
        else:
            return False



class UnstructuredObject(rw_parent):
    """
    Класс для работы с объектами из MongoDB
    """

    def read(self,uuid,collection):
        """
        Прочитать объект из базы.
        :param uuid: глобальный идентификатор объекта в системе. Равен _id в mongoDB.
        :param obj_type: указывает на коллекцию в которой находится объект
        :return: возвращает объект типа DynamicObject с заполненными полями. Если не найден, возвращает в None.
        """
        #Определяем название коллекции в которой находиться объект

        #Читаем объект
        #Заполняем параметры
        return None

    def write(self):
        """
        Записать объект в mongo.
        Записывает в базу объект, со всеми значениями свойств.
        :return: Возвращает статус операции.
        """


class Message(Base, rw_parent):
    __tablename__ = 'messages'
    NAME = "Сообщение"
    EDIT_FIELDS = ['viewed','category']
    ALL_FIELDS = {'id': 'id',
                  'uuid': 'Идентификатор',
                  'channel_type': 'Тип',
                  'message_id': 'Идентификатор',
                  'viewed': 'Просмотрено',
                  'category': 'Категория',
                  'data': 'Сообщение'}
    VIEW_FIELDS = ['message_id','viewed','category','data']
    ADD_FIELDS = []


    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    channel_type = Column(sqlalchemy.String(256))
    message_id = Column(sqlalchemy.String(256))
    viewed = Column(Integer, default=0)
    category = Column(Integer, default=0)
    data = Column(sqlalchemy.TEXT())

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.category = 0
        self.viewed = 0

    def is_exist_msg(self, session, msg_id):
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

    def create_email(self, session, source, data_link, msg_id):
        """
        Функция создания объекта Message типа Email.
        На вход получает:
        :param session: -- текущйи объект Session для работы с БД.
        :param Source: -- объект Account через который было получено
        сообщение.
        :param data_link: -- ссылка на коллекцию mongoDB, где храниться содержимое объекта.
        :param msg_id: -- идентификатор сообщения.
        
        Выполняет действия:
        -- Заполняет свойство data объекта Message типа email ссылкой на коллецию. Данные сообщения пишуться в mongoDB.
        -- Создает объект Reference - событие создания объекта(link = 1)

        """

        r_status = [None, ""]
        t_status = [None, ""]

        self.channel_type = rwChannel_type[0]
        # self.data = json.dumps(email)
        # print type(email)
        # self.data = str(email)

        self.data = data_link


        # print self.data
        # print type(self.data)

        self.message_id = msg_id

        # Записываем объект
        session.add(self)

        try:
            session.commit()
        except RuntimeError:
            t_status[0] = False
            t_status[1] = 'Message object ID: ' + str(self.id) + ' NOT writed.'
            return t_status, r_status
        else:
            t_status[1] = True
            t_status[1] = 'Message object ID: ' + str(self.id) + ' writed.'
            t_status[1] = t_status[1] + '\n ' + str(self.uuid)

        """ Создаем Reference на новый объект """
        ref = Reference(source_uuid=source.uuid,
                        source_type=source.__tablename__,
                        source_id=source.id,
                        target_uuid=self.uuid,
                        target_type=self.__tablename__,
                        target_id=self.id,
                        link=1)


        # Записываем объект
        r_status = ref.create(session)

        return t_status, r_status

    def get_message_body(self):
        """
        Вызывается в шаблоне для распоковки поля data в сообщении.
        Распаковывает только указаыннве поля: to,from,subject,message-id,raw_text_html, text_html
        """
        body = dict()
        client = pymongo.MongoClient()
        conn = re.split("\.",str(self.data))
        db = client[conn[0]]
        msg = db[conn[1]]

        tt = msg.find_one({"uuid": self.uuid})
        if tt:
            body['to'] = tt['to']
            body['from'] = tt['from']
            body['subject'] = tt['subject']
            body['text_html'] = tt['text_html']
            body['raw_text_html'] = tt['raw_text_html']
            body['message-id'] = self.message_id
        return body


def get_email_message(session, uuid):
    """
    Возвращает распакованные email сообщения по списку переданных UUID.
    Параметр uuid -- список (List) uuid сообщений которые необходимо распаковать.
    """
    messages = {}

    if uuid == None:
        # Получить все сообщения
        pass
    else:
        # Получить сообщения по списку UUID
        try:
            query = session.query(Message).filter(Message.uuid.in_(uuid))
        except sqlalchemy.orm.exc.NoResultFound:
            print 'No emails.'
        else:
            client = pymongo.MongoClient()
            db = client.messages
            dbe = db.emails

            for email in query.all():
                messages[email.uuid] = dbe.find_one({"uuid": email.uuid})
        finally:
            session.close()

    return messages


class Classifier(Base, rw_parent):
    """
    Хранит список классификаторов.
    """

    __tablename__ = "classifiers"

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    description = Column(sqlalchemy.String(256))
    clf_path = Column(sqlalchemy.String(256))
    clf_type = Column(sqlalchemy.String(256))
    vec_path = Column(sqlalchemy.String(256))

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.clf_path = LEARN_PATH + str(self.uuid) + str("_classifier.joblib.pkl")
        self.vec_path = LEARN_PATH + str(self.uuid) + str("_vectorizer.joblib.pkl")


class MessageCategory(Base, rw_parent):
    """
    Типы сообщений. Используется для классификации.
    """

    __tablename__ = "message_category"

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    name = Column(sqlalchemy.String(256))
    description = Column(sqlalchemy.String(256))

    def __init__(self):
        self.uuid = uuid.uuid1()


class KnowledgeTree(Base, rw_parent):
    """
    Иерархическая структура знаний.
    Каждый узел представляет собой описание темы с параметрами.
    
    """

    __tablename__ = "knowledge_tree"
    childs = []
    parent = []

    NAME = "Знания"
    EDIT_FIELDS = ['name', 'description', 'tags', 'expert']
    ALL_FIELDS = {'name': 'Название', 'description': 'Описание',
                  'tags': 'Теги', 'expert': 'Ответственный',
                  'id': 'id', 'uuid': 'Идентификатор',
                  'parent_id': 'Родительский раздел', 'tags_clf': 'tags_clf'}
    VIEW_FIELDS = ['name', 'description', 'tags', 'expert']
    ADD_FIELDS = ['parent_id','name', 'description', 'tags', 'expert']

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    parent_id = Column(sqlalchemy.String(50))
    name = Column(sqlalchemy.String(256))
    tags = Column(sqlalchemy.String(256))
    description = Column(sqlalchemy.String(256))
    expert = Column(sqlalchemy.String(256))
    tags_clf = Column(sqlalchemy.String(256), default="")
    objects_class = Column(sqlalchemy.String(256), default="")

    def __init__(self):
        self.uuid = uuid.uuid1()

    def get_objects_classes(self):
        """
        Возвращает распакованные классы объектов которые надо показать в этом узле.
        :return: список
        """
        resp = list()
        if not self.objects_class:
            return resp
        for cl in re.split(",",self.objects_class):
            i = re.split("\.",cl)
            if len(i) == 1:
                resp.append(i[0])
            else:
                resp.append(i[1])

        return resp

    def return_full_tree(self, session, outformat):
        """
        Возвращает дерево в виде строки или словаря, согласно формату.
        -- string -- строка, только названия узлов.
        -- dict -- словарь, все свойства.
        -- session -- использует существующую сессию SQL. Если None, создает свою.
        
        
        """

        if not session:
            session = Session()

        if outformat == "string":
            s = ""
            ss, obj = self.return_childs(session, 0, 0)
            s = s + ss
        else:
            s = ""
            obj = None

        return s, obj
        print "Данные из запроса : "
        print params
        print "\nКонтекст :"
        print session_context
        print "Переадресация на show_object... ",url


    @staticmethod
    def ktree_return_childs(session, parent_id):
        """
        :param session: Объект SQLAlchemy Session.
        :param parent_id: узел для которого ищутся дочение узлы.
        :return obj: Возвращает на первом месте сам родительский узел. Список дочерних узлов идет после родительского,
        если их нет, то только родительский.
        то возвращается сам узел.
         список.
        """
        obj = list()
        if parent_id == 0:
            raise Exception("Нельзя указывать parent_id = 0.")
        try:
            query = session.query(KnowledgeTree).\
                filter(KnowledgeTree.id == parent_id).one()
        except sqlalchemy.orm.exc.NoResultFound as e:
            raise e
            #"Родительский узел не найден."+str(e))
        else:
            obj.append(query)


        try:
            query = session.query(KnowledgeTree).\
                filter(KnowledgeTree.parent_id == parent_id).all()
        except sqlalchemy.orm.exc.NoResultFound:
            print "Больше нет дочерних узлов."
            return obj
        except Exception as e:
            raise e
                #("Ошибка при чтении дерева из базы. "+str(e))
        else:
            for each in query:
                obj.append(each)

        return obj

    @staticmethod
    def get_root(session):
        try:
            query = session.query(KnowledgeTree).\
                filter(KnowledgeTree.parent_id == 0).one()
        except sqlalchemy.orm.exc.NoResultFound as e:
            raise e
                #("Родительский узел не найден."+str(e))
        else:
            return query.id

class Question(Base, rw_parent):
    __doc__ = """
    Вопросы которые задаются пользователю.
    Стурктура:
    -- *target_uuid* -- UUID целевого объекта
    -- *target_type* -- тип объекта
    -- *target_attr* -- Название атрибута который надо определить
    -- *Text - Текст вопроса
    -- *Answer - Ответ от пользователя
    -- *ans_var - Варианты ответов
    -- *type - Тип вопроса: ДА-НЕТ или выбор из доступных вариантов ответов
    -- *do_true - Что выполнять при положительном ответе
    -- *do_false - Что выполнять при отрицательном ответе
    -- *is_answered - индикатор наличия ответа
    -- *user - UUID пользователя системы которому адресован вопрос
    """

    __tablename__ = "questions_queue"

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    target_uuid = Column(sqlalchemy.String(50))
    target_type = Column(sqlalchemy.String(256))
    target_attr = Column(sqlalchemy.String(256))
    text = Column(sqlalchemy.String(256))
    answer = Column(sqlalchemy.String(256))
    ans_var = Column(sqlalchemy.String(256))
    ans_type = Column(sqlalchemy.String(256))
    do_true = Column(sqlalchemy.String(256))
    do_false = Column(sqlalchemy.String(256))
    is_answered = Column(sqlalchemy.Integer, default=0)
    user = Column(sqlalchemy.String(50))

    def __init__(self):
        self.uuid = uuid.uuid1()


def test():
    session = Session()

    try:
        company1 = Company(uuid=str(uuid.uuid1()), name='Test company', prefix='tc_')

    except RuntimeError:
        print sys.exc_info()
        session.close()

    else:
        company1.employees = [Employee(name='Второй ', surname='Сотрудник')]
        company1.employees.append(Employee(name='Третий ', surname='Сотрудник'))

        session.add(company1)
        session.commit()

        company1 = Company(uuid=str(uuid.uuid1()), name='2 Test company', prefix='2tc_')
        session.add(company1)

        session.commit()

        for inst in session.query(Company).all():
            print inst.id, inst.name, inst.uuid

        for inst in session.query(Employee).all():
            print inst.id, inst.name, inst.uuid, inst.comp_id

        email_data = {'From': 'sergey@reshim.com', 'Subj': 'Проверка', 'Text': 'Я хочу все знать!\
                        "Но не все", а только часть.?%%№;!'}

        source = {'uuid': '0000', 'source_type': 'system', 'id': 0}

        msg = Message()
        msg.create_email(session, source, email_data)

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
    
    :rtype : Возвращает объект которому принадлежит указанный UUID.
    Возвращает:
    -- сам объект 
    -- статус в виде списка. Первый элемент True/False в зависимости от итога
    операций и сообщение во втором элемента (пустой если прошло успешно).
    
    """

    session = Session()
    obj_class = {}
    status = [True, ""]
    # print sys.modules[__name__]
    # print inspect.getmembers(sys.modules[__name__], inspect.isclass)

    for name, obj in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        try:
            obj.__tablename__
        except AttributeError as e:
            pass
        else:
            obj_class[obj.__tablename__] = name
            # print name,type(name)
            # print obj,type(obj)
            # print obj.__tablename__

    if not status[0] and not bool(obj_class):
        status[0] = False
        status[1] = "Нет класса для этого объекта. " + str(e)
        raise Exception(status[0], status[1])

    #print "obj_class :",obj_class

    # Ищем объект
    try:
        query = session.query(Reference). \
            filter(sqlalchemy.and_(Reference.target_uuid == uuid, \
                                   Reference.link == 1)).one()
    except sqlalchemy.orm.exc.NoResultFound as e:
        # print e
        status[0] = False
        status[1] = "Нет объекта в References." + str(e)
        raise Exception(status[0], status[1])
        # print "нет объекта"
    else:
        # print query
        t = query.target_type

        #print "type(query) :",type(query)
        #print "query type : ",t
        #print "obj_class[t] :",obj_class[t]

        kk = globals()[obj_class[t]]
        #print kk,type(kk)

    try:
        obj = session.query(kk).filter_by(uuid=uuid).one()
    except sqlalchemy.orm.exc.NoResultFound as e:
        status[0] = False
        status[1] = "Не могу найти объект в базе." + str(e)
        raise Exception(status[0], status[1])
    else:
        pass
        obj.read()
        #print type(obj)
        #print obj

    session.close()
    return obj,status


def set_by_uuid(uuid, data):
    """

    Записывает объект любого типа по его uuid.
    
    В качестве параметров ждет поля объекта объекта,в формате Dict.
    
    Возвращает:
    -- статус в виде списка. Первый элемент True/False в зависимости от итога
    операций и сообщение во втором элемента (пустой если прошло успешно).
    
    """

    session = Session()
    status = [True, ""]

    s = "set_by_uuid : " + str(data)

    # Определяем класс объекта
    try:
        obj_class = get_by_uuid(uuid)[0].__class__
    except Exception as e:
        print e[0]
        print e[1]
        raise Exception(e[0], e[1])
    else:
        pass

    # Получаем сам объект
    obj = session.query(obj_class).filter_by(uuid=uuid).one()

    print obj_class
    print obj

    keys = data.keys()

    s = s + "\n set_by_uuid KEYS: " + str(keys)

    try:
        data.pop("id")
    except KeyError:
        s = s + "\n нет ключа."
    else:
        s = s + "\n Ключ ID удален."

    try:
        data.pop("uuid")
    except KeyError:
        s = s + "\n нет ключа."
    else:
        s = s + "\n Ключ UUID удален."

    keys = data.keys()

    s = s + "\n set_by_uuid KEYS: " + str(keys)

    changed = False

    for key in keys:
        if obj.__dict__[key] != data[key]:
            s = s + "\n значение изменилось:"
            s = s + "\n " + str(obj.__dict__[key]) + " != " + str(data[key])
            obj.__dict__[key] = data[key]
            # Объявляем о модификации аттирибута объекта
            sqlalchemy.orm.attributes.flag_modified(obj, key)
            changed = True
        else:
            s = s + "\n значение не изменилось:"
            s = s + "\n " + str(obj.__dict__[key]) + " == " + str(data[key])

    if changed:
        print "Session dirty : ", session.dirty
        try:
            session.commit()
        except RuntimeError:
            status[0] = False
            s = s + "\n Ошибка записи объекта."
        else:
            s = s + "\n Запись объекта успешна."
        finally:
            session.close()
    else:
        s = s + "\n Объект не изменялся. Не записан."

    status[1] = s

    return status


def create_new_object(session, object_type,params, source):
    """
    :param session: Session()
    Идентификатор сессии ORM. Если не передается, то ожидается None и создается новый. Если передан, то используется он.
    :param object_type: string
     Тип нового объекта. Совпадает со свойством  __tablename__ объектов.
    :param params: dict
    Набор значений свойств нового ообъекта.
    :param source: Любой объект имеющий UUID из модуля rwObjects
    :return: list Список из статуса и сам объект.
    """
    status = [True,""]
    session_flag = False
    new_obj = None

    """Если сессия не передана, то создаем свою."""
    if not session:
        session = Session()
        session_flag = True

    """Создаем требуемый объект. """
    if object_type == "employees":
        new_obj = Employee()
        new_obj.login = params['login'] + "@" + params['company_prefix']
        new_obj.name = params['name']
        new_obj.password = params['password']
        new_obj.surname = params['surname']
        new_obj.comp_id = params['comp_id']
    elif object_type == "accounts":
        new_obj = Account()
        for f in new_obj.ADD_FIELDS:
            if params[f] != "":
                new_obj.__dict__[f] = params[f]
    elif object_type == "knowledge_tree":
        new_obj = KnowledgeTree()
        for f in new_obj.ADD_FIELDS:
            if f in params.keys() and params[f] != "":
                new_obj.__dict__[f] = params[f]

    else:
        status[False,"Объект типа " + object_type + " создать нельзя."]
        return status,None

    """
    Проверяем существование объекта с такими параметрами. Если существует, возвращает статус операции и None.
    Если нет, то сохраняем.
    """
    status = new_obj.check()
    if not status[0]:
        return status,None

    try:
        session.add(new_obj)
        session.commit()
    except Exception as e:
        return [False,"Ошибка записи в базу."+str(e)],None
    else:
        # Записываем событие создания объекта
        ref = Reference(source_uuid=source.uuid,
                        source_type=source.__tablename__,
                        source_id=source.id,
                        target_uuid=new_obj.uuid,
                        target_type=new_obj.__tablename__,
                        target_id=new_obj.id,
                        link=1)
        status = ref.create(session)
    finally:
        if session_flag:
            session.close()

    return status,new_obj


def link_objects(session,source_uuid,target_uuid):
    """
    :param session: Session ORM. Если не передаеться, то поставить None.
    :param source: UUID исходного объекта.
    :param target: UUID целевого объекта.
    :return: тестовая строка со статусом операции.
    """
    session_flag = False
    if not session:
        session = Session()
        session_flag = True
    """Получаем объекты для связи """
    source = get_by_uuid(source_uuid)[0]
    target = get_by_uuid(target_uuid)[0]

    """Проверяем наличие связи """
    try:
        response = session.query(Reference).\
            filter(and_(Reference.source_uuid == source.uuid,\
                        Reference.source_type == source.__tablename__,\
                        Reference.source_id == source.id,\
                        Reference.target_uuid == target.uuid,\
                        Reference.target_type == target.__tablename__)).all()
    except Exception as e:
        raise Exception("Ошибка чтения базы связей. " + str(e))
    else:
        pass
    if not response:
        """ Создаем связь """
        ref = Reference(source_uuid = source.uuid,
                                  source_type = source.__tablename__,
                                  source_id = source.id,
                                  target_uuid = target.uuid,
                                  target_type= target.__tablename__,
                                  target_id = target.id,
                                  link=0)
        status = ref.create(session)
    else:
        raise Exception("Такая связь уже существует.")

    if session_flag:
        session.close()

    return status