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
from sqlalchemy import or_, and_, desc
import uuid
import datetime
import json
import base64
from bs4 import BeautifulSoup
from sklearn.externals import joblib
import inspect
import prototype1_queue_module as rwQueue
import prototype1_type_classifiers as rwLearn
import pymongo
import re
import operator
from configurations import *
import networkx as nx

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

"""
Constants
"""

# rwChannel_type = ["email", "facebook", "phone", "vk"]
rwChannel_type = ["email"]

"""
Константа описывающая возможные типы каналов получения сообщений.

Используется в классах:

* DynamicObject
* Account

"""

STANDARD_OBJECTS_TYPES = ['accounts', 'employees', 'messages', 'cases']

"""
Константа содержит список типов объектов (для всех классов кроме DynamicObjects это свойство __tablename__,
для DynamicObjects - значение свойства objects_class)
которые автоматически линкуются к стандартным веткам ДЗ.

Стандартные ветки ДЗ, в базе имеют заполненное поле
objects_class содержащее список типов объектов, которые автоматически с ними линкуются.
"""

FOR_CLASSIFY = ['messages']

"""
Cписок типов объектов к которым применяются классификаторы.

Классификаторы определяют кастомный узел в ДЗ знаний к которому можно отнести данный объект.
Кастомный узел ДЗ - это создаваемый пользователями узлы по определенной тематике.
"""

"""
Подключение БД и MongoDB
"""
Base = sqlalchemy.ext.declarative.declarative_base()
Engine = sqlalchemy.create_engine(sql_uri, pool_size=20)
Session = sqlalchemy.orm.sessionmaker(bind=Engine)

Mongo_client = pymongo.MongoClient(mongo_uri)
Mongo_db = Mongo_client.get_default_database()

"""
reWork classes
"""


def create_tables():
    """
    Функция пересоздания таблиц  базе данных MySQL.

    Все таблицы пересоздаются согласно объявлению классов наследованных от Base. Если таблица в БД существует,
    то ничего не происходит.

    :return: нет
    """

    Base.metadata.create_all(Engine)


def create_company():
    """
    Служебная функция для создания новой компании. Запускается при инициализации системы для новой компании.

    Все данные будут запрошены функцией самостоятельно при запуске из консоли.

     Создает:

     * прародителя всех компаний -- reWork (необходимо для корректного построения графа)
     * новую компанию и префикс (аналогично домену), следует после имен пользователей. Необходимо для совместимости.
     * суперпользователя компании (администратора) -- имя по-умолчанию: superuser@<prefix>.
     * начальную структуру Навигатора Знаний, разделы:

       * Все
       * Сообщения
       * Аккаунты

     * Инициализирует базовый классификатор для кастомных разделов Навигатора Знаний.
    
    """

    session = Session()
    rework = Company()
    rework.name = "reWork"
    rework.prefix = "_re"
    session.add(rework)
    session.commit()

    ref = Reference(source_uuid=rework.uuid,
                    source_type=rework.__tablename__,
                    source_id=rework.id,
                    target_uuid=rework.uuid,
                    target_type=rework.__tablename__,
                    target_id=rework.id,
                    link=1)
    ref.create(session)

    company_name = unicode(raw_input("Введите название компании: "))
    company_prefix = unicode(raw_input("Введите префикс (до 3-х символов): "))

    new_company = Company()
    new_company.name = str(company_name)
    new_company.prefix = str(company_prefix)

    # Проверить веденные данные
    s = new_company.check()

    if not s[0]:
        print s[1]
        return
    else:
        session.add(new_company)

    try:
        session.commit()
    except RuntimeError:
        print "Ошибка создания компании."
    else:
        print "Компания \"" + str(new_company.name) + "\" внесена в базу."

    # Записываем событие создания Компании
    ref = Reference(source_uuid=rework.uuid,
                    source_type=rework.__tablename__,
                    source_id=rework.id,
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
        create_access_rights_record(session, superuser, ['admin', 'users'])

    # Записываем событие создания Компании
    ref = Reference(source_uuid=new_company.uuid,
                    source_type=new_company.__tablename__,
                    source_id=new_company.id,
                    target_uuid=superuser.uuid,
                    target_type=superuser.__tablename__,
                    target_id=superuser.id,
                    link=1)
    ref.create(session)

    """
    Создаем структуру навигатора знаний.
    """
    print "Создаем корневой раздел Дерева Знаний: Все"
    params = {'parent_id': 0, 'name': 'Все', 'description': 'Все', 'tags': '', 'expert': superuser.login,
              'type': 'system'}
    try:
        status, obj = create_new_object(session, "knowledge_tree", params, superuser)
    except Exception as e:
        raise (e)
    else:
        print status
        parent_id = obj.id

    print "Создаем системный раздел Дерева Знаний: Сообщения"
    params = {'parent_id': parent_id, 'name': 'Сообщения', 'description': 'Сообщения', 'tags': '',
              'expert': superuser.login, 'type': 'system', 'objects_class': 'messages'}
    try:
        status, obj = create_new_object(session, "knowledge_tree", params, superuser)
    except Exception as e:
        raise (e)
    else:
        print status

    print "Создаем системный раздел Дерева Знаний: Аккануты"
    params = {'parent_id': parent_id, 'name': 'Аккаунты', 'description': 'Аккаунты', 'tags': '',
              'expert': superuser.login, 'type': 'system'}
    try:
        status, obj = create_new_object(session, "knowledge_tree", params, superuser)
    except Exception as e:
        raise (e)
    else:
        print status

    print "Создаем базовый классификатор для кастомных разделов Дерева Знаний."
    try:
        status, obj = create_new_object(session, "classifiers", {'clf_type': 'svc'}, superuser)
    except Exception as e:
        raise (e)
    else:
        print status
        print "\nЗапишите UUID классификатора в файл modules/configurations.py  в переменную default_classifier"
        print "\n %s \n" % str(obj.uuid)

    print "Создаем базовый классификатор для вычисления расстояний Навигатора Знаний."
    try:
        status, obj = create_new_object(session, "classifiers", {'clf_type': 'nbrs'}, superuser)
    except Exception as e:
        raise (e)
    else:
        print status
        print """\nЗапишите UUID классификатора в файл modules/configurations.py  в переменную
                    default_neighbors_classifier"""
        print "\n %s \n" % str(obj.uuid)

    session.close()


class rw_parent():
    """
    Класс предок для всех остальных класов.

    Используется для задания констант и базовых функций.

    Свойства класса:

    * NAME -- имя объекта экземпляра класса. Содержит человеческое имя для вывода на пользователям. По-умолчанию: ""
    * EDIT_FIELDS -- список, перечисляет поля которые можно редактировать пользователю через интерфейс.
    * ALL_FIELDS -- словарь, содержит все поля объекта с их названиями. Формат элемента: key -- свойство, \
    value -- название.
    * VIEW_FIELDS -- список, перечисляет поля которые будут показаны через интерфейс при стадартном выводе.
    * ADD_FIELDS -- список, перечисляет поля которым можно присвоить значение через интерфейс при создании нового \
    объекта.
    * SHORT_VIEW_FIELDS -- список, перечисляет поля которые будут показаны через интерфейс при коротком выводе.
    * ACCESS_GROUPS -- словарь групп доступа с названиями.

    """

    NAME = ""
    EDIT_FIELDS = []
    ALL_FIELDS = {'uuid':'uuid'}
    VIEW_FIELDS = ['uuid']
    ADD_FIELDS = []
    SHORT_VIEW_FIELDS = ['uuid']
    ACCESS_GROUPS = {'admin': 'Администраторы', 'users': 'Пользователи', 'expert': 'Эксперт Навигатора Знаний'}

    def get_attrs(self):
        """
        Возвращает список всех полей объекта искючая служебные начинающиеся на _
        :return: список полей объекта.
        """
        attrs = [name for name in self.__dict__ if not name.startswith('_')]

        return attrs

    def get_fields(self):
        """
        Возвращает 4 структуры из констант self.ALL_FIELDS, self.VIEW_FIELDS, self.EDIT_FIELDS, self.ADD_FIELDS.

        :return: [self.ALL_FIELDS, self.VIEW_FIELDS, self.EDIT_FIELDS, self.ADD_FIELDS]
        """

        return [self.ALL_FIELDS, self.VIEW_FIELDS, self.EDIT_FIELDS, self.ADD_FIELDS]

    def read(self, session):
        """
        Заглушка в стандатных типах для чтения динамических объектов.

        Для обычных объектов производит:

        * заполнение свойства -- self.__dict__['obj_type'] = self.__tablename__
        * заполнение свойства -- self.__dict__['custom_category'] = list()
        * заполнение свойства -- self.__dict__['system_category'] = list()

        """
        self.__dict__['obj_type'] = self.__tablename__

        # Ищем Custom узлы ДЗ к которым относиться объект
        self.__dict__['custom_category'] = list()
        self.__dict__['system_category'] = list()

    def check(self):
        """
        Проверка на существование объекта. Это заглушка в родительском классе.

        В классе при необходимости должна быть переписана на реальную проверку.

        :return: Всегда возвращает список -- [True,"OK"]
        """
        return [True, "OK"]


class AccessRights(Base,rw_parent):
    """
    Хранит права доступа для пользователей системы.

    На текущий момент права доступа жестко присвоены соответствующей группе. Поэтому в таблице храниться связь \
    пользователя с группой.

    """

    __tablename__ = 'access_rights'
    NAME = "Права доступа"

    ALL_FIELDS = {'group': 'Группа', 'user_uuid': 'Пользователь', 'uuid': 'Идентификатор',
                  'id': 'id'}
    EDIT_FIELDS = ['group', 'user_uuid']
    VIEW_FIELDS = ['group', 'user_uuid']
    ADD_FIELDS = ['group', 'user_uuid']
    SHORT_VIEW_FIELDS = ['group', 'user_uuid']

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50))
    group = sqlalchemy.Column(sqlalchemy.String(256))
    user_uuid = sqlalchemy.Column(sqlalchemy.String(256))

    def __init__(self):
        self.uuid = uuid.uuid1()

    def check(self,session):
        """
        Проверяем наличие записи о вхождении в группу для пользователя. Выполняется перед записью.
        """

        resp = session.query(AccessRights).filter(and_(AccessRights.group == self.group,\
                                                       AccessRights.user_uuid == self.user_uuid)).count()
        if resp == 0:
            return True
        else:
            return False


def create_access_rights_record(session,obj,groups):
    """
    Функция создания записей о вхождении объекта в группу.
    """

    if obj.__class__.__name__ != "Employee":
        return [False,"Неверный тип объекта. Ожидался Employee, был получен %s" % obj.__class__]
    for group in groups:
        if group not in obj.ACCESS_GROUPS.keys():
            return [False,"Неверно указана группа: %s. Все группы должны входить в ACCESS_GROUPS." % group]
    try:
        resp = session.query(AccessRights).filter(AccessRights.user_uuid == obj.uuid).all()
    except Exception as e:
        pass
    else:
        # Если в уже существующих записях есть группы которые не попадают в новый список, то удаляем их.
        for r in resp:
            if r.group not in groups:
                session.delete(r)
        session.commit()

    for group in groups:
        access = AccessRights()
        access.group = group
        access.user_uuid = obj.uuid
        if access.check(session):
            session.add(access)
            try:
                session.commit()
            except Exception as e:
                return [False,str(e)]
            else:
                print "Execution rwObjects.create_access_rights_record for %s : Successed." % obj.uuid
        else:
            print "Пользователь %s уже входит в группу %s" % (obj.uuid,group)

    return [True, "OK"]


def get_access_rights_record(session,obj):
    """
    Функция посика записей о вхождении объекта в группу.
    """

    access_records = list()

    try:
        resp = session.query(AccessRights.group).filter(AccessRights.user_uuid == obj.uuid).all()
    except Exception as e:
        print [False,"Функция def get_access_rights_record(session,obj). Ошибка доступа к БД. %s " % str(e)]
    else:
        for g in resp:
            access_records.append(g[0])

    return access_records


def get_userlist_in_group(session,group):
    """
    Возвращает список объектов класса Employee входящих в указанную группу.

    :param session: сессия ORM
    :param group: название группы
    :return: Tuple состоящий из: статуса -- список из двух элементов: True/False и описание; Набора объектов -- \
    список объектов класса Employee входящих в запрошенную группу
    """

    userlist = list()

    try:
        resp = session.query(AccessRights).filter(AccessRights.group == group).all()
    except Exception as e:
        [False,"Функция get_userlist_in_group(session,group). Ошибка: "+str(e)],userlist
    else:
        for u in resp:
            user = get_by_uuid(u.user_uuid)[0]
            print user
            userlist.append(user)

    return [True,"OK"],userlist

class Company(Base, rw_parent):
    """
    Класс объектов для хранения данных о Компании.

    **На текущий момент, каждая компания использует свой экземпляр базы MySQL для хранения данных, \
    поэтому класс используется только при инциализации системы для новой компании.**

    Список свойств класса:

    :parameter id: sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    :parameter uuid: идентификатор (sqlalchemy.Column(sqlalchemy.String(50)))
    :parameter name: название компании (sqlalchemy.Column(sqlalchemy.String(256)))
    :parameter prefix: префикс компании (sqlalchemy.Column(sqlalchemy.String(10))).
    :parameter employees: связь с полем comp_id  в класе Employee (relationship("Employee", backref="companies"))

    """
    __tablename__ = 'companies'
    NAME = "Компания"

    EDIT_FIELDS = ['name', 'prefix']
    ALL_FIELDS = {'name': 'Имя', 'prefix': 'домен', 'uuid': 'Идентификатор',
                  'id': 'id'}
    VIEW_FIELDS = ['name', 'prefix']
    ADD_FIELDS = ['name', 'prefix']

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50))
    name = sqlalchemy.Column(sqlalchemy.String(256), default="")
    prefix = sqlalchemy.Column(sqlalchemy.String(10), default="")
    employees = relationship("Employee", backref="companies")

    def __init__(self):
        self.uuid = uuid.uuid1()

    def read(self, session):
        """

        :param session:
        :return:
        """

        self.NAME = "Компания"
        self.EDIT_FIELDS = ['name', 'prefix']
        self.ALL_FIELDS = {'name': 'Имя', 'prefix': 'домен', 'uuid': 'Идентификатор', 'id': 'id'}
        self.VIEW_FIELDS = ['name', 'prefix']
        self.SHORT_VIEW_FIELDS = ['name']
        self.ADD_FIELDS = ['name', 'prefix']

    def check(self):
        """
        Проверка на существование компании с таким именем или префиксом.

        :returns: status -- список из двух элементов. В первом True/False -- статус операции проверки, если совпадения \
        найдены **False**, если не найдены - **True**. Второй элемент содержит описание ошибки.
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
    Возвращает объект класса Company по его id.

    :return: company -- объект класса Company.
    """

    session = Session()
    company = session.query(Company).filter_by(id=cid).first()
    company.read(session)
    session.close()
    return company


class Employee(Base, rw_parent):
    """
    Класс для работы с объектами Пользователей системы.

    Список свойств класса:

    :parameter id: sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    :parameter uuid: идентифкатор (sqlalchemy.Column(sqlalchemy.String(50), default=uuid.uuid1()))
    :parameter name: имя пользователя (sqlalchemy.Column(sqlalchemy.String(256)))
    :parameter surname: фамилия пользователя (sqlalchemy.Column(sqlalchemy.String(256)))
    :parameter login: логин пользователя в формате: **<логин>@<префикс компании>** (sqlalchemy.Column( \
    sqlalchemy.String(50)))
    :parameter password: пароль пользователя (sqlalchemy.Column(sqlalchemy.String(20)))
    :parameter comp_id: ид компании (Column(Integer, ForeignKey('companies.id')))
    :parameter accounts: связь с полем employee_id в классе Account (relationship("Account", backref="employees"))
    :parameter disabled: индикатор использования аккаунта пользователя(0 - используется, 1 - отключен \
    (sqlalchemy.Column(sqlalchemy.Integer))
    """

    EDIT_FIELDS = ['name', 'surname', 'password']
    ALL_FIELDS = {'name': 'Имя', 'surname': 'Фамилия',
                  'login': 'Логин', 'password': 'Пароль',
                  'comp_id': 'Компания', 'id': 'id', 'uuid': 'uuid',
                  'access_groups': 'Группы доступа'}
    VIEW_FIELDS = ['name', 'surname', 'login', 'password', 'access_groups']
    ADD_FIELDS = ['name', 'surname', 'login', 'password', 'access_groups']
    NAME = "Сотрудник"

    STATUS = {0: 'Используется', 1: 'Не используется'}

    __tablename__ = 'employees'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50), default=uuid.uuid1())
    name = sqlalchemy.Column(sqlalchemy.String(256), default="")
    surname = sqlalchemy.Column(sqlalchemy.String(256), default="")
    login = sqlalchemy.Column(sqlalchemy.String(50))
    password = sqlalchemy.Column(sqlalchemy.String(20))
    comp_id = Column(Integer, ForeignKey('companies.id'))
    accounts = relationship("Account", backref="employees")
    disabled = Column(Integer, default=0)

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.access_groups = list()

    def read(self,session=None):

        self.EDIT_FIELDS = ['name', 'surname', 'password', 'access_groups', 'disabled']
        self.ALL_FIELDS = {'name': 'Имя', 'surname': 'Фамилия',
                           'login': 'Логин', 'password': 'Пароль',
                           'comp_id': 'Компания', 'id': 'id', 'uuid': 'uuid',
                           'disabled':'Статус', 'access_groups': 'Группы доступа'}
        self.VIEW_FIELDS = ['name', 'surname', 'login', 'password', 'access_groups', 'disabled']
        self.SHORT_VIEW_FIELDS = ['name', 'surname']
        self.ADD_FIELDS = ['name', 'surname', 'login', 'password', 'access_groups']
        self.NAME = "Сотрудник"
        self.access_groups = get_access_rights_record(session,self)


    def check(self):
        """
        Проверка на существование пользователя с таким login.

        :return: status -- список из двух элементов. В первом True/False -- статус операции проверки, если совпадения \
        найдены **False**, если не найдены - **True**. Второй элемент содержит описание ошибки.
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

    :return: объект класса Employee.
    :exception: None, если объект не найден или найдено несколько.
    """

    session = Session()

    try:
        user = session.query(Employee).filter(Employee.login == login).one()
    except sqlalchemy.orm.exc.NoResultFound:
        print "Пользователь не найден"
        return None
    except sqlalchemy.orm.exc.MultipleResultsFound:
        # status = [False,"Такой логин существует. Задайте другой."]
        print "Найдено множество пользователей."
        return None
    else:
        print "Пользователь найден"
        user.read(session)
        return user

    session.close()


class Account(Base, rw_parent):
    """
    Объект для работы с объектами класса Account.

    Список свойств класса в ORM:

    :parameter id: sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    :parameter uuid: идентификатор (sqlalchemy.Column(sqlalchemy.String(50)))
    :parameter acc_type: тип аккаунта принимает одно из значений константы rwChannel_type (Column(sqlalchemy.String(\
    256),default=rwChannel_type[0]))). По-умолчанию равен: rwChannel_typ[0] = email.
    :parameter description: Описание аккаунта (sqlalchemy.Column(sqlalchemy.String(256)))
    :parameter server: имя сервера для подключения по IMAP (sqlalchemy.Column(sqlalchemy.String(256)))
    :parameter port: порт сервера для подключения по IMAP (sqlalchemy.Column(sqlalchemy.String(6)))
    :parameter login: имя пользователя для подключения (sqlalchemy.Column(sqlalchemy.String(50)))
    :parameter password: пароль пользователя (sqlalchemy.Column(sqlalchemy.String(20)))
    :parameter dirs: каталоги которые будут проверяться системой при подключении (Column(sqlalchemy.String(256), \
    default=DIRS["Gmail"])). По-умолчанию, проверяются "Входящие" и "Отправленные". На текущий момент реализована \
    поддржка сервисов Gmail, Yandex.
    :parameter last_check: время последней проверки (Column(sqlalchemy.DATETIME(), default=datetime.datetime.now()))
    :parameter employee_id: ссылка на ИД сотрудника, владельца ящика (Column(Integer, ForeignKey('employees.id')))
    :parameter disabled: индикатор использования аккаунта (0 - используется, 1 - отключен, 2 - архивный) \
    (sqlalchemy.Column(sqlalchemy.Integer))

    Список постоянных свойств класса:

    :parameter dict DIRS: словарь содержит закодированные названия проверяемых каталогов для разных сервисов. Формат: \
    ключ - название сервиса, значение - JSON закодированная последовательность описывающая каталоги.

    """

    __tablename__ = 'accounts'
    DIRS = {'Yandex': '{"inbox": "INBOX", "sent": "&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-", "drafts": '
                      '"&BCcENQRABD0EPgQyBDgEOgQ4-"}',
            'Gmail': '{"inbox":"INBOX","sent":"[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-", "drafts": "['
                     'Gmail]/&BCcENQRABD0EPgQyBDgEOgQ4-"}'}

    STATUS = {0: 'Используется', 1: 'Не используется', 2: 'Архивный'}

    ALL_FIELDS = {
        "id": "id",
        "uuid": "Идентификатор",
        "acc_type": "Тип аккаунта",
        "description": "Описание",
        "server": "Имя сервера",
        "port": "Порт",
        "login": "Логин",
        "password": "Пароль",
        "dirs": "Каталоги для проверки",
        "last_check": "Дата и время последней проверки",
        "employee_id": "Связан с сотрудником",
        "disabled": "Статус"
    }
    VIEW_FIELDS = ['acc_type', 'description', 'server', 'port', 'dirs', 'login', 'password', 'last_check','disabled']
    ADD_FIELDS = ['acc_type', 'description', 'server', 'port', 'dirs', 'login', 'password']
    EDIT_FIELDS = ['description', 'server', 'port', 'dirs', 'login', 'password','disabled']
    SHORT_VIEW_FIELDS = ['login', 'acc_type', 'description']
    NAME = "Аккаунт"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uuid = sqlalchemy.Column(sqlalchemy.String(50))
    acc_type = Column(sqlalchemy.String(256), default=rwChannel_type[0])
    description = sqlalchemy.Column(sqlalchemy.String(256), default="")
    server = sqlalchemy.Column(sqlalchemy.String(256))
    port = sqlalchemy.Column(sqlalchemy.String(6))
    login = sqlalchemy.Column(sqlalchemy.String(50))
    password = sqlalchemy.Column(sqlalchemy.String(20))
    dirs = Column(sqlalchemy.String(256), default=DIRS["Gmail"])
    last_check = Column(sqlalchemy.DATETIME(), default=datetime.datetime.now())
    employee_id = Column(Integer, ForeignKey('employees.id'))
    disabled = Column(Integer, default=0)

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

    """
    def read(self,session):

        self.DIRS = {'Yandex': '{"inbox": "INBOX", "sent": "&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"}',
                     'Gmail': '{"inbox":"INBOX","sent":"[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"}'}

        self.ALL_FIELDS = {"id": "id",
                           "uuid": "Идентификатор",
                           "acc_type": "Тип аккаунта",
                           "description": "Описание",
                           "server": "Имя сервера",
                           "port": "Порт",
                           "login": "Логин",
                           "password": "Пароль",
                           "dirs": "Каталоги для проверки",
                           "last_check": "Дата и время последней проверки",
                           "employee_id": "Связан с сотрудником"}
        self.VIEW_FIELDS = ['acc_type', 'description', 'server', 'port', 'dirs', 'login', 'password', 'last_check']
        self.ADD_FIELDS = ['acc_type', 'description', 'server', 'port', 'dirs', 'login', 'password']
        self.EDIT_FIELDS = ['description', 'server', 'port', 'dirs', 'login', 'password']
        self.SHORT_VIEW_FIELDS = ['login', 'acc_type', 'description']
        self.NAME = "Аккаунт"
"""

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

    :parameter id: sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    :parameter source_uuid: идентификатор (UUID) объекта источника связи (sqlalchemy.Column(sqlalchemy.String(50)))
    :parameter source_type: тип объекта источника, равен свойству __tablename__ объекта ((sqlalchemy.Column( \
    sqlalchemy.String(30))).
    :parameter source_id: ид в талице (sqlalchemy.Column(Integer))
    :parameter target_uuid: идентификатор (UUID) объекта цели связи (sqlalchemy.Column(sqlalchemy.String(50)))
    :parameter target_type: тип объекта цели, равен свойству __tablename__ объекта (sqlalchemy.Column( \
    sqlalchemy.String(30)))
    :parameter target_id: ид в талице (sqlalchemy.Column(Integer))
    :parameter link: вес связи между объектами (Column(Integer, default=0))
    :parameter timestamp: метка времени создания связи (Column(sqlalchemy.DATETIME(), default=datetime.datetime.now()))

    Значение аттрибута **link** равно **0**, если это связь между source и target.
    Заначение аттрибута **link** равно **1**, если это событие создания target объекта объектом источником.

    :parameter __tablename__: равен 'references'

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
        """
        Функция записи связи между объектами в БД.

        :param session: параметр сессии ORM.
        :return: status -- список из двух элементов. В первом True/False -- статус операции, если ошибка **False**, \
        если все было записано - **True**. Второй элемент содержит описание.
        """

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
                rwQueue.apply_rules_for_1.delay(self.source_uuid, self.source_type, self.target_uuid, self.target_type)
            elif self.link == 0:
                """ Вызываем функцию проверки правил при связывании объектов"""
                rwQueue.apply_rules_for_0.delay(self.source_uuid, self.source_type, self.target_uuid, self.target_type)

        return r_status

    def read(self, session):
        """

        """

        self.__dict__['obj_type'] = self.__tablename__

        # Ищем Custom узлы ДЗ к которым относиться объект
        self.__dict__['custom_category'] = list()
        self.__dict__['system_category'] = list()

        self.NAME = "Событие"

        self.EDIT_FIELDS = []
        self.ALL_FIELDS = {'id': 'id',
                            'source_uuid': 'Кто',
                            'source_type': 'Тип',
                            'source_id': 'id',
                            'target_uuid': 'С чем',
                            'target_type': 'Тип',
                            'target_id': 'id',
                            'link': 'Связь',
                            'timestamp': 'Время'}
        self.VIEW_FIELDS = ['timestamp', 'source_uuid', 'link', 'target_uuid']
        self.ADD_FIELDS = []
        self.SHORT_VIEW_FIELDS = ['timestamp', 'source_uuid', 'link', 'target_uuid']

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
#    category = Column(sqlalchemy.String(256))
    subject = Column(sqlalchemy.String(256), default="")
    query = Column(sqlalchemy.TEXT(), default="")
    solve = Column(sqlalchemy.TEXT(), default="")
    algorithm = Column(sqlalchemy.TEXT(), default="")

    def __init__(self):
        self.uuid=uuid.uuid1()
        self.read()

    def read(self, session=None):
        """

        """

        session_flag = False
        if not session:
            session = Session()
            session_flag = True

        self.NAME = "Кейс"

        self.EDIT_FIELDS = ['subject', 'query', 'solve', 'algorithm']
        self.ALL_FIELDS = {'id': 'id',
                            'uuid': 'Идентификатор',
                            'subject': 'Тема',
                            'query': 'Запрос',
                            'solve': 'Ответ',
                            'algorithm': 'Алгоритм'}
        self.VIEW_FIELDS = ['subject', 'query', 'solve', 'algorithm']
        self.ADD_FIELDS = ['subject', 'query', 'solve', 'algorithm']
        self.SHORT_VIEW_FIELDS = ['subject']
        cats = get_ktree_for_object(session,self.uuid)
        #print cats[0]
        #print cats[1]
        self.__dict__['custom_category'] = cats[0].values()
        self.__dict__['system_category'] = cats[1].values()
        if session_flag:
            session.close()


class Used_case(Base, rw_parent):
    __tablename__ = 'used_cases'

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    used_case = Column(sqlalchemy.String(256))
    rating = Column(sqlalchemy.String(256))
    used_for = Column(sqlalchemy.String(256))


class DynamicObject(Base, rw_parent):
    """
    Класс для работы с динамическими объектами.

    Динамические объекты это структуры содержащие основной смысловой материал компании:

    * сообщения (электронные письма, сообщения в соц сетях и т.д.)
    * документы присланные по почте, находящиеся в облачных файловых сервисах и т.д.

    Т.к. структура объектов может отличаться даже внутри одной категории, то все хранение содежимого перенесено в \
    MongoDB, в MySQL базе храняться только служебные параметры объектов. UUID объектов в обеих базах совпадают для \
    облегчения
    доступа и поиска.

    Доступ к объектам происходит только через встроенные функции класса: read, write. Они дополняют созданный \
    экземпляр класса свойствами объекта хранящимися в MongoDB.

    Свойства класса в ORM:

    :parameter id: ид (Column(sqlalchemy.Integer, primary_key=True))
    :parameter uuid: идентификатор (Column(sqlalchemy.String(50), default=uuid.uuid1()))
    :parameter obj_type: тип самого объекта хранящегося в MongoDB. Тип не может пересекаться с типами стандартных \
    объектов в ORM (теми значениями что храняться в __tablename__) (Column(sqlalchemy.String(256))).
    :parameter collection: коллекция в которой объект храниться в MongoDB (Column(sqlalchemy.String(256)))
    :parameter timestamp: время создания (Column(sqlalchemy.DATETIME(), default=datetime.datetime.now()))

    Список постоянных свойств класса:

    :parameter __tablename__: по-умолчанию равно 'dynamic_object'

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
        Инициализация объекта происходит с одновременным заполнением свойства uuid.
        """
        self.uuid = uuid.uuid1()

    def write(self, session, obj):
        """
        Функция производит запись самого объекта в MongoDB и служебной информации в MySQL.

        Объект должен обязательно содержать поле **obj_type** которое определяет его тип и используется для \
        дальнейшей работы с объектом.

        :param session: параметр сессии ORM.
        :param obj: сам объект содержащий данные. Представляет собой набор полей и их значений (словарь).

        :return: status -- список из двух элементов. В первом True/False -- статус операции, если ошибка **False**, \
        если все было записано - **True**. Второй элемент содержит описание.
        """
        session_flag = False

        if not session:
            session = Session()
            session_flag = True

        try:
            self.obj_type = obj['obj_type']
        except Exception as e:
            raise ("Не указан тип объекта в свойстве obj_type. " + str(e))
        else:
            pass

        collection = Mongo_db[obj['obj_type']]
        obj['uuid'] = self.uuid.__str__()
        obj['_id'] = self.uuid.__str__()
        self.collection = obj['obj_type']

        try:
            record_id = collection.insert_one(obj).inserted_id
        except Exception as e:
            raise ("Не удалось сохранить объект в базе MongoDB. " + str(e))
        else:
            print "Объект сохранен " + str(record_id)

            """
            Записываем в sql базу данные о DynamicObject
            """
            # Записываем DynamicObject
            session.add(self)
            status = [True, ""]
            try:
                session.commit()
            except Exception:
                raise ([False, "Message object ID: " + str(self.id) + " NOT writed."])
            else:
                status[0] = True
                status[1] = 'Message object ID: ' + str(self.id) + ' writed.'

        if session_flag:
            session.close()

        return status

    def read(self, session):
        """
        Читает объект из базы MongoDB. Заполняет свойства:

        * VIEW_FIELDS
        * ALL_FIELDS
        * SHORT_VIEW_FIELDS
        * NAME
        * self.__dict__['custom_category'] -- какие custom объекты Навигатора Знаний связаны с ним
        * self.__dict__['system_category'] -- какие system объекты Навигатора Знаний связаны с ним

        :param session: параметр сессии ORM.
        """

        self.VIEW_FIELDS = []
        # Определяем название коллекции в которой находиться объект
        collection = Mongo_db[self.collection]
        query = {'uuid': str(self.uuid)}

        try:
            obj = collection.find_one(query)
        except Exception as e:
            raise ([False, "Ошибка чтения объекта. " + str(e)])
        else:
            # Заполняем параметры
            # print "\nVIEW FIELDS ",self.VIEW_FIELDS
            # Собираем в объект все ключи и их значения
            for key in obj.keys():
                self.__dict__[key] = obj[key]
                self.ALL_FIELDS[key] = key
            # print "\nВсе ключи ",self.__dict__.keys()

            if self.obj_type == 'messages':
                view_f = ['from', 'to', 'cc', 'bcc', 'subject', 'raw_text_html']
                self.NAME = 'Сообщение'
                self.ALL_FIELDS['from'] = 'От кого'
                self.ALL_FIELDS['to'] = 'Кому'
                self.ALL_FIELDS['cc'] = 'Копия'
                self.ALL_FIELDS['bcc'] = 'Скрытая копия'
                self.ALL_FIELDS['subject'] = 'Тема'
                self.ALL_FIELDS['raw_text_html'] = 'Текст'
                self.SHORT_VIEW_FIELDS = ['from', 'to', 'subject']

            # Удаляем ключи не присутствующие в данном объекте
            for key in view_f:
                if key in self.__dict__.keys():
                    self.VIEW_FIELDS.append(key)

        # Ищем Custom узлы ДЗ к которым относиться объект
        self.__dict__['custom_category'] = list()
        self.__dict__['system_category'] = list()

        try:
            response = session.query(Reference). \
                filter(and_(Reference.source_type == 'knowledge_tree', \
                            Reference.target_uuid == self.uuid, \
                            Reference.link == 0)).all()
        except Exception as e:
            pass
        else:
            custom_obj = get_ktree_custom(session)
            for ref in response:
                if ref.source_uuid in custom_obj.keys():
                    self.__dict__['custom_category'].append(custom_obj[ref.source_uuid])

    def clear_text(self):
        """
        Производит очистку текста в объекте.

        **Должна вызываться только после read(), иначе некоторые свойства объекта не будут еще определены.**

        Формирует новое свойство **self.__dict__['text_clear']** которе заполняется очищенным от html тегов и ссылок\
         текстом.

        """
        if 'raw_text_plain' in self.__dict__.keys():
            data = self.__dict__['raw_text_plain']
            # print "plain\n",data
        elif 'raw_text_html' in self.__dict__.keys():
            data = self.__dict__['raw_text_html']
            data = get_text_from_html(self.__dict__['raw_text_html'])
            # print "html\n",data

        data = re.sub(u"<?[http]\S+>?", u'LINK1', data, re.I | re.U | re.M)

        self.__dict__['text_clear'] = data

    def check(self, query):
        """
        Проверяем наличие записей в базе с указанными параметрами.

        :param query: Параметры в виде словаря.
        :return: **True**, если что-то нашлось, **False** - если совпадений не найдено.
        """
        collection = Mongo_db[self.collection]
        response = collection.find_one(query)
        if response:
            return True
        else:
            return False


def get_text_from_html(data):
    """
    Извлекаем из html сообщения только текст. Ссылки заменяются ключевым словом **LINK**.

    :param data: html сообщение
    :return: plain текст
    """

    soup = BeautifulSoup(data, from_encoding="utf8")

    # Содержимое ссылок заменяем на LINK
    tag = soup.new_tag(soup, "b")
    tag.string = 'LINK'
    for link in soup.find_all('a'):
        link.replaceWith(tag)
    for link in soup.find_all('script'):
        link.replaceWith(tag)
    for link in soup.find_all(''):
        link.replaceWith(tag)

    return soup.get_text()


"""
class Message(Base, rw_parent):
    __tablename__ = 'messages'
    NAME = "Сообщение"
    EDIT_FIELDS = ['viewed', 'category']
    ALL_FIELDS = {'id': 'id',
                  'uuid': 'Идентификатор',
                  'channel_type': 'Тип',
                  'message_id': 'Идентификатор',
                  'viewed': 'Просмотрено',
                  'category': 'Категория',
                  'data': 'Сообщение'}
    VIEW_FIELDS = ['message_id', 'viewed', 'category', 'data']
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
        ""
        Проверяет есть ли в базе сообщение с таким же идентификатором.
        Если есть, возвращает True, если нет False.
        ""
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
        ""
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

        ""

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

        "" Создаем Reference на новый объект ""
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
        ""
        Вызывается в шаблоне для распоковки поля data в сообщении.
        Распаковывает только указаыннве поля: to,from,subject,message-id,raw_text_html, text_html
        ""
        body = dict()
        client = pymongo.MongoClient()
        conn = re.split("\.", str(self.data))
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
    ""
    Возвращает распакованные email сообщения по списку переданных UUID.
    Параметр uuid -- список (List) uuid сообщений которые необходимо распаковать.
    ""
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
"""


class Classifier(Base, rw_parent):
    """
    Хранит список классификаторов.

    Классификаторы нужны для автоматического определения принадлежности к ветке типа custom Навигатора Знаний.
    Классификаторы используются для классификации всех типов объектов входящих в FOR_CLASSSIFY.

    Свойства класса в ORM:

    :parameter id: ид (Column(sqlalchemy.Integer, primary_key=True))
    :parameter uuid: идентификатор (Column(sqlalchemy.String(50), default=uuid.uuid1()))
    :parameter description: описание классфикатора (Column(sqlalchemy.String(256)))
    :parameter clf_path: пусть к файлу хранящему сериализованный объект классификатора, необходим для хранения \
    обученного классификатора (Column(sqlalchemy.String(256)))
    :parameter clf_type: тип используемого алгоритма (Column(sqlalchemy.String(256)))
    :parameter vec_path: путь к файлу хранящему сериализованный объект векторизатора Column(sqlalchemy.String(256))
    :parameter targets: хранит список категорий которым был обучен классификатор (Column(sqlalchemy.TEXT())). \
    Позиция вероятности в ответе соответствует категории в этом списке.

    Постоянные свойства класса:

    :parameter __tablename__: равен "classifiers"

    """

    __tablename__ = "classifiers"

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    description = Column(sqlalchemy.String(256), default="")
    clf_path = Column(sqlalchemy.String(256))
    clf_type = Column(sqlalchemy.String(256))
    vec_path = Column(sqlalchemy.String(256))
    targets = Column(sqlalchemy.TEXT())

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.clf_path = LEARN_PATH + str(self.uuid) + str("_classifier.joblib.pkl")
        self.vec_path = LEARN_PATH + str(self.uuid) + str("_vectorizer.joblib.pkl")

    def read(self, session):
        self.NAME = "Классификатор"
        self.ALL_FIELDS = {'description': 'Описание',
                           'id': 'id', 'uuid': 'Идентификатор'}
        self.VIEW_FIELDS = ['description']
        self.SHORT_VIEW_FIELDS = ['description']

class ClassificationResult(Base, rw_parent):
    """
    Хранит результаты автоматической классфикации объектов.
    """

    __tablename__ = "classification_result"

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    clf_uuid = Column(sqlalchemy.String(256))
    target_uuid = Column(sqlalchemy.String(256))
    probe = Column(sqlalchemy.String(256))
    categories = Column(sqlalchemy.TEXT())
    status = Column(sqlalchemy.String(256))

    def __init__(self):
        self.uuid = uuid.uuid1()

    def get_probe_and_category(self):
        """
        Возвращает отсортированный по уменьшению вероятности список, каждый элемент которого это список из двух \
        частей. Первый элемент - вероятность, второй - UUID категории.
        """

        result = list()
        probes = re.split(',',self.probe)
        cats = re.split(',',self.categories)

        for i in xrange(len(probes)):
            result.append([probes[i],cats[i]])

        print "Before sort : %s" % result
        sort = sorted(result,key=operator.itemgetter(0),reverse=True)

        return sort


def get_classification_results(session, object_uuid):
    """
    Функция возвращает для указанного UUID объекта все результаты автоматической классификации со статусом **'new'**.

    :param session: сессия ORM
    :param object_uuid: идентификатор объекта для которого нужен результат
    :return: список объектов класса ClassificationResult
    """

    try:
        resp = session.query(ClassificationResult).filter(and_(ClassificationResult.status == 'new',\
                                                                 ClassificationResult.target_uuid == object_uuid)).one()
    except Exception:
        return []
    else:
        return resp.get_probe_and_category()


class KnowledgeTree(Base, rw_parent):
    """
    Иерархическая структура знаний.
    Каждый узел представляет собой описание темы с параметрами.

    Свойства класса в ORM:

    :parameter id: ид (Column(sqlalchemy.Integer, primary_key=True))
    :parameter uuid: идентификатор (Column(sqlalchemy.String(50), default=uuid.uuid1())
    :parameter parent_id: ид родительского узла (Column(sqlalchemy.String(50))
    :parameter name: название (Column(sqlalchemy.String(256))
    :parameter tags: теги узла(ключевые слова) (Column(sqlalchemy.String(256))
    :parameter description: описание (Column(sqlalchemy.String(256))
    :parameter expert: ответственный эксперт (его логин) (Column(sqlalchemy.String(256))
    :parameter tags_clf: теги классификатора (Column(sqlalchemy.String(256), default="")
    :parameter objects_class: типы объектов которые автоматически будут привязаны к этому узлу Навигатора Знаний при \
    их появлении в системе. Обычно относиться к system узлам. (Column(sqlalchemy.String(256),default=""))
    :parameter type: тип узла (Column(sqlalchemy.String(256), default="")), бывают двух типов: **system** -- \
    системный, не подлежит изменению пользователями и к нему могут быть привязаны автоматические типы. \
    **custom** -- пользовательский, может быть создан и изменен в настройках. Для таких узлов проводятся процедуры \
    распознавания и классификации объектов системы с помощью классификаторов.
    :parameter action: действие (пока это закодированные функции) которое будут выполнено при появлении в этом узле
    объекта определенного класса (DO).

    Постоянные свойства класса:

    :parameter __tablename__: равно "knowledge_tree"
    :parameter NAME: равно "Знания"
    """

    __tablename__ = "knowledge_tree"
    childs = []
    parent = []

    NAME = "Раздел Навигатора Знаний"

    """
    EDIT_FIELDS = ['name', 'description', 'tags', 'expert', 'action']
    ALL_FIELDS = {'name': 'Название раздела', 'description': 'Описание',
                  'tags': 'Теги', 'expert': 'Ответственный',
                  'id': 'id', 'uuid': 'Идентификатор',
                  'parent_id': 'Родительский раздел', 'tags_clf': 'tags_clf',
                  'objects_class': 'Автоматически привязываются', 'type': 'Тип узла',
                  'action': 'Что делать при появлении нового объекта'}
    VIEW_FIELDS = ['name', 'description', 'tags', 'expert', 'action']
    ADD_FIELDS = ['type', 'parent_id', 'name', 'description', 'tags', 'expert', 'action', 'objects_class']
    ACTION_LIST = {'no': 'ничего', 'create_case': 'создавать Кейс'}
    """

    id = Column(sqlalchemy.Integer, primary_key=True)
    uuid = Column(sqlalchemy.String(50), default=uuid.uuid1())
    parent_id = Column(sqlalchemy.String(50))
    name = Column(sqlalchemy.String(256), default="")
    tags = Column(sqlalchemy.String(256), default="")
    description = Column(sqlalchemy.String(256), default="")
    expert = Column(sqlalchemy.String(256), default="")
    tags_clf = Column(sqlalchemy.String(256), default="")
    objects_class = Column(sqlalchemy.String(256), default="")
    type = Column(sqlalchemy.String(256), default="")
    action = Column(sqlalchemy.String(256), default="no")

    def __init__(self):
        self.uuid = uuid.uuid1()
        self.read()

    def read(self, session=None):
        self.NAME = "Тема Навигатора Знаний"
        self.EDIT_FIELDS = ['parent_id', 'name', 'description', 'tags', 'expert', 'action']
        self.ALL_FIELDS = {'name': 'Название', 'description': 'Описание',
                           'tags': 'Теги', 'expert': 'Ответственный эксперт',
                           'id': 'id', 'uuid': 'Идентификатор',
                           'parent_id': 'Родительский раздел', 'tags_clf': 'tags_clf',
                           'objects_class': 'Автоматически привязываются', 'type': 'Тип узла',
                           'action': 'Что делать при появлении нового объекта'}
        self.VIEW_FIELDS = ['parent_id', 'name', 'description', 'tags', 'expert', 'action']
        self.SHORT_VIEW_FIELDS = ['name', 'description', 'expert']
        self.ADD_FIELDS = ['type', 'parent_id', 'name', 'description', 'tags', 'expert', 'action', 'objects_class']
        self.ACTION_LIST = {'no': 'ничего', 'create_case': 'создавать Кейс'}

    def get_objects_classes(self):
        """
        Возвращает распакованные классы объектов которые надо показать в этом узле. Значения ищутся в свойстве \
        objects_class.

        :return: список типов классов в виде строк
        """

        resp = list()
        if not self.objects_class:
            return resp
        for cl in re.split(",", self.objects_class):
            i = re.split("\.", cl)
            if len(i) == 1:
                resp.append(i[0])
            else:
                resp.append(i[1])

        return resp

    @staticmethod
    def ktree_return_childs(session, parent_id):
        """
        Функция возвращает дочерние узлы для указанного родительского.

        :param session: Объект SQLAlchemy Session.
        :param parent_id: узел для которого ищутся дочение узлы.

        :return: спсиок, на первом месте сам родительский узел. Список дочерних узлов идет после \
        родительского,если их нет, то только родительский.
        """

        obj = list()
        if parent_id == 0:
            raise Exception("Нельзя указывать parent_id = 0.")
        try:
            query = session.query(KnowledgeTree). \
                filter(KnowledgeTree.id == parent_id).one()
        except sqlalchemy.orm.exc.NoResultFound as e:
            raise e
            # "Родительский узел не найден."+str(e))
        else:
            obj.append(query)

        try:
            query = session.query(KnowledgeTree). \
                filter(KnowledgeTree.parent_id == parent_id).all()
        except sqlalchemy.orm.exc.NoResultFound:
            print "Больше нет дочерних узлов."
            return obj
        except Exception as e:
            raise e
            # ("Ошибка при чтении дерева из базы. "+str(e))
        else:
            for each in query:
                obj.append(each)

        return obj

    def get_category_objects_count(self, session):
        """
        Возвращает количество объектов привязанных к узлу Навигатора Знаний UUID которого указан в self.uuid.

        :parameter session: сессия ORM

        :return: если не было ошибок, то возвращает количество. Если были ошибки, то вернет 0.
        """

        try:
            count = session.query(Reference). \
                filter(and_(Reference.link == 0, Reference.source_uuid == self.uuid)).count()
        except Exception:
            return 0
        else:
            return count

    @staticmethod
    def get_root(session):
        """
        Возвращает id корневого узла Навигатора Знаний.

        :parameter session: сессия ORM

        :return: id корневого узла Навигатора Знаний
        """

        try:
            query = session.query(KnowledgeTree). \
                filter(KnowledgeTree.parent_id == 0).one()
        except sqlalchemy.orm.exc.NoResultFound as e:
            raise e
            # ("Родительский узел не найден."+str(e))
        else:
            return query.id

    def get_all(self,session):
        """
        Возвращает все узлы Навигатора Знаний за исключением самого себя.

        :parameter session: сессия ORM

        :return: список всех узлов Навигатора Знаний за исключением самого себя.
        """

        try:
            query = session.query(KnowledgeTree). \
                filter(KnowledgeTree.uuid != self.uuid).all()
        except Exception as e:
            raise e
        else:
            pass

        return query


def get_ktree_custom(session):
    """
    Возвращает список custom узлов Навигатора Знаний и сами узлы в него входящие.

    :param session: Сессия ORM

    :return: словарь custom узлов, где ключи это UUID узлов, а значения объекты узлов.
    """

    custom = dict()
    try:
        res = session.query(KnowledgeTree). \
            filter(KnowledgeTree.type == 'custom').all()
    except Exception as e:
        raise ("Ошибка доступа к базе узлов Навигатора Знаний. Ошибка :  %s" % str(e))
    else:
        for r in res:
            custom[r.uuid] = r
    return custom


def get_ktree_for_object(session,obj_uuid=None):
    """
    Возвращает списоки узлов Навигатора Знаний к которым привязан объект.

    :param session: Сессия ORM
    :param obj_uuid: UUID объекта для которого ищем узлы.

    :return: список из двух элементов. Первый словарь custom узлов, где ключи это UUID узлов, а значения объекты \
    узлов. Второй sysytem узлов, где ключи это UUID узлов, а значения объекты.
    """

    custom_leafs = dict()
    system_leafs = dict()
    try:
        res = session.query(Reference).\
            filter(and_(Reference.source_type == 'knowledge_tree',
                        Reference.target_uuid == obj_uuid)).all()
    except Exception as e:
        raise e
    else:
        pass

    try:
        for r in res:
            leaf = get_by_uuid(r.source_uuid)[0]
            if leaf.type == 'custom':
                custom_leafs[r.source_uuid] = leaf
            elif leaf.type == 'system':
                system_leafs[r.source_uuid] = leaf
            else:
                pass
    except Exception as e:
        raise e
    else:
        pass

    return [custom_leafs,system_leafs]


class Question(Base, rw_parent):
    """
    Вопросы которые задаются пользователю.

    Структура:

    :parameter target_uuid: UUID целевого объекта
    :parameter target_type: тип объекта
    :parameter target_attr: Название атрибута который надо определить
    :parameter Text: Текст вопроса
    :parameter Answer: Ответ от пользователя
    :parameter ans_var: Варианты ответов
    :parameter type: Тип вопроса: ДА-НЕТ или выбор из доступных вариантов ответов
    :parameter do_true: Что выполнять при положительном ответе
    :parameter do_false: Что выполнять при отрицательном ответе
    :parameter is_answered: индикатор наличия ответа
    :parameter user: UUID пользователя системы которому адресован вопрос

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


class AccessGraph(object):
    """
    Граф для определения прав доступа к объектам.
    """

    def __init__(self):
        session = Session()
        response = session.query(Reference).all()

        G = nx.Graph()
        labels = {}
        for line in response:
            if line.link == 0:
                s_obj = get_by_uuid(line.source_uuid)[0]
                t_obj = get_by_uuid(line.target_uuid)[0]
                G.add_node(str(line.source_uuid), obj=s_obj)
                G.add_node(str(line.target_uuid), obj=t_obj)
                G.add_edge(str(line.source_uuid), str(line.target_uuid), weight=int(line.link), timestamp=line.timestamp)
                # print G.node[str(line.source_uuid)]

        self.graph = G
        session.close()

    def reload(self):
        """
        Функция перезагружает граф из базы.

        :return:
        """

        self.__init__()

    def neighbors(self, uuid=None):

        if uuid:
            try:
                self.graph.neighbors(uuid)
            except:
                return [uuid]
            else:
                return self.graph.neighbors(uuid) + [uuid]
        else:
            return None


def test():
    pass


def get_by_uuid(uuid):
    """
    Возвращает объект любого типа по его uuid.
    
    Существование объекта определяется по наличию связи в References со статусом 1.
    Параметры объекта определяются через его тип (обычно указан в __tablename__).

    :parameter uuid: UUID объекта

    :return: сам объект, которому принадлежит указанный UUID. Cтатус в виде списка. Первый элемент True/False в \
    зависимости от итога операций и сообщение во втором элемента (пустой если прошло успешно).
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

    # print "obj_class :",obj_class

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

        # print "type(query) :",type(query)
        # print "query type : ",t
        # print "obj_class[t] :",obj_class[t]

        kk = globals()[obj_class[t]]
        # print kk,type(kk)

    try:
        obj = session.query(kk).filter_by(uuid=uuid).one()
    except sqlalchemy.orm.exc.NoResultFound as e:
        status[0] = False
        status[1] = "Не могу найти объект в базе." + str(e)
        raise Exception(status[0], status[1])
    else:
        pass
        obj.read(session)
        # print type(obj)
        # print obj

    session.close()
    return obj, status


def set_by_uuid(uuid, data):
    """
    Записывает объект любого типа по его uuid. Проверяет список полей на изменения, если их не было ничего не делает. \
    Если изменения были, то ставит бит принудительного сохранения объекта для ORM и проводит commit.
    
    :parameter uuid: идентификатор
    :parameter data: поля объекта объекта,в формате Dict.
    
    :return: Возвращает статус в виде списка. Первый элемент **True/False** в зависимости от итога \
    операций и сообщение во втором элемента (пустой если прошло успешно).
    
    """

    session = Session()
    status = [True, ""]

    s = "set_by_uuid : " + str(data)

    # Определяем класс объекта
    try:
        obj_class = get_by_uuid(uuid)[0].__class__
    except Exception as e:
        print str(e)
        raise Exception(e)
    else:
        pass

    # Получаем сам объект
    obj = session.query(obj_class).filter_by(uuid=uuid).one()

    print obj_class
    print obj
    print obj.__class__.__name__

    keys = data.keys()
    print keys

    """
    Если во время сохранения изменений надо проверить, заменить или раскрыть поля объекта, это делается тут.
    """
    if obj.__class__.__name__ == 'Account':
        if 'dirs' in keys:
            data['dirs'] = obj.DIRS[data['dirs']]

    if obj.__class__.__name__ == 'Employee':
        if 'groups' in keys:
            if not isinstance(data['groups'], list):
                data['groups'] = [data['groups']]
            create_access_rights_record(session, obj, data['groups'])
            try:
                data.pop('groups')
            except KeyError:
                s = s + "\n нет ключа."
            else:
                s = s + "\n Ключ ID удален."

    s = s + "\n set_by_uuid KEYS: " + str(keys)

    try:
        data.pop("id")
    except KeyError as e:
        s = s + "\n нет ключа."
    else:
        s = s + "\n Ключ ID удален."

    try:
        data.pop("uuid")
    except KeyError as e:
        s = s + "\n нет ключа."
        raise Exception("set_bu_uuid(). Не указан UUID. Ошибка : %s"%str(e))
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


def create_new_object(session, object_type, params, source):
    """
    Создает новый объект и записывает его. Перед создание проверяет наличие обязательных полей  и существование \
    объекта с указанными свойствами.

    :param session: Идентификатор сессии ORM. Если не передается, то ожидается None и создается новый. Если передан, \
    то используется он.
    :param object_type: строка с типом нового объекта. Совпадает со свойством  __tablename__ объектов.
    :param params: словарь значений свойств нового ообъекта.
    :param source: Любой объект имеющий UUID, являющийся создателем нового объекта. Будет записан как объект источник \
    в таблицу Reference.
    :return: список из статуса операции и сам объект. Если прошло неудачно, вместо объекта возвращается None.
    """

    status = [True, ""]
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

        if not isinstance(params['groups'], list):
            params['groups'] = [params['groups']]

        """Создание прав доступа для нового объекта"""
        create_access_rights_record(session, new_obj, params['groups'])

    elif object_type == "accounts":
        new_obj = Account()
        params['dirs'] = new_obj.DIRS[params['dirs']]
        for f in new_obj.ADD_FIELDS:
            if params[f] != "":
                new_obj.__dict__[f] = params[f]

    elif object_type == "knowledge_tree":
        new_obj = KnowledgeTree()
        # создаем классификатор
        # clf = rwLearn.init_classifier('svc')
        for f in new_obj.ADD_FIELDS:
            if f in params.keys() and params[f] != "":
                new_obj.__dict__[f] = params[f]

    elif object_type == "classifiers":
        CL = Classifier()
        st, new_obj = rwLearn.init_classifier(session, CL, params['clf_type'])

    elif object_type == "cases":
        new_obj = Case()
        for f in new_obj.ADD_FIELDS:
            if f in params.keys() and params[f] != "":
                new_obj.__dict__[f] = params[f]

    else:
        status[False, "Объект типа " + object_type + " создать нельзя."]
        return status, None

    """
    Проверяем существование объекта с такими параметрами. Если существует, возвращает статус операции и None.
    Если нет, то сохраняем.
    """
    status = new_obj.check()
    if not status[0]:
        return status, None

    try:
        session.add(new_obj)
        session.commit()
    except Exception as e:
        return [False, "Ошибка записи в базу." + str(e)], None
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

    return status, new_obj


def link_objects(session, source_uuid, target_uuid):
    """
    Создает связь между объектами.

    :param session: Session ORM. Если не передаеться, то поставить None.
    :param source: UUID исходного объекта.
    :param target: UUID целевого объекта.

    :return: список со статусом операции и комментариями.
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
        response = session.query(Reference). \
            filter(and_(Reference.source_uuid == source.uuid, \
                        Reference.source_type == source.__tablename__, \
                        Reference.source_id == source.id, \
                        Reference.target_uuid == target.uuid, \
                        Reference.target_type == target.__tablename__, \
                        Reference.link == 0)).all()
    except Exception as e:
        raise Exception("Ошибка чтения базы связей. " + str(e))
    else:
        pass
    if not response:
        """ Создаем связь """
        ref = Reference(source_uuid=source.uuid,
                        source_type=source.__tablename__,
                        source_id=source.id,
                        target_uuid=target.uuid,
                        target_type=target.__tablename__,
                        target_id=target.id,
                        link=0)
        status = ref.create(session)
    else:
        raise Exception("Такая связь уже существует.")

    if session_flag:
        session.close()

    return status
