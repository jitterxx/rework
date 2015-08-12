# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:11:50 2015

@author: sergey

Воркеры для очереди задач.

"""

import celery
import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_email_module as rwEmail
from datetime import timedelta, datetime

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

app = celery.Celery('tasks', backend='rpc://', broker='amqp://guest@localhost//')


@app.task()
def msg_delivery_for_user(uuid):
    session = rwObjects.Session()
    refs = session.query(rwObjects.Reference). \
        filter(rwObjects.and_(rwObjects.Reference.source_uuid == uuid,
                              rwObjects.Reference.target_type == "accounts",
                              rwObjects.Reference.link == 0)).all()

    for acc in refs:
        # print type(acc)
        get_messages_for_account.delay(acc.target_uuid)
    return "OK"


@app.task()
def get_messages_for_account(account_uuid):
    """
    Функция получает и записывает в базу сообщения по указанному аккаунту.
    Используется для всех типов сообщений и каналов.
    :param account_uuid: UUID аккаунта для подключения.
    :return: Статус операции (строка)
    """

    session = rwObjects.Session()
    status = [True, "OK"]

    try:
        account = rwObjects.get_by_uuid(account_uuid)[0]
    except Exception as e:
        status = [False, "Указанный аккаунт не найден.\n" + account_uuid + str(e)]
        return status[1]
    else:
        pass

    """Получаем сообщения"""
    if account.acc_type == 'email':
        print "Подключаюсь к " + str(account.login) + "..."
        try:
            emails, status = rwEmail.get_emails(account)
            # print emails
        except Exception as e:
            status = [False, 'Ошибка получения сообщений.\n' + str(e)]
            return status[1]
        else:
            pass

        """
        Запись сообщения в SQL и МонгоДБ
        """
        for email in emails.values():
            do = rwObjects.DynamicObject()
            email['channel_type'] = rwObjects.rwChannel_type[0]
            email['obj_type'] = do.obj_type = do.collection = 'message'

            if not do.check({"message-id": email['message-id']}):
                print "----------Начало записи в Монго------------------"
                s = do.write(session, email)

                print "---------- Окончание записи в Монго------------------"

                if s[0]:
                    """ Создаем Reference на новый объект """
                    ref = rwObjects.Reference(source_uuid=account.uuid,
                                              source_type=account.__tablename__,
                                              source_id=account.id,
                                              target_uuid=do.uuid,
                                              target_type=do.__tablename__,
                                              target_id=do.id,
                                              link=1)
                    # Записываем объект
                    r_status = ref.create(session)
            else:
                print "Такое сообщение уже существует."

    account.last_check = datetime.now()
    session.commit()
    session.close()

    return "OK."


@app.task()
def apply_rules(source_uuid, source_type, target_uuid, target_type):
    """
    В момент появления связи "создания" между объектами проходит проверка автоматических правил.
    Эта функция вызывается автоматически при вызове функции Reference.create()
    :param source_uuid: UUID объекта источника
    :param source_type: тип объекта источника
    :param target_uuid: UUID объекта цели
    :param target_type: тип объекта цели
    :return string: OK, в случае успеха.
    :exception e: Ошибка в случае исключения.
    """
    session = rwObjects.Session()
    """
    Если среди участников проверки есть DynamicObject, то ищем его внутренний тип.
    """
    tt = target_type
    st = source_type
    if target_type == "dynamic_object":
        response = session.query(rwObjects.DynamicObject). \
            filter(rwObjects.DynamicObject.uuid == target_uuid).one()
        tt = response.obj_type

    elif source_type == "dynamic_object":
        response = session.query(rwObjects.DynamicObject). \
            filter(rwObjects.DynamicObject.uuid == source_uuid).one()
        tt = response.obj_type

        """Правило 1. Acc создает Msg
            Если S = Account и T = Message, то связываем Сотрудника владеющего аккаунтом и сообщение.
                Владелец аккаунта всегда один и связан с ним связью весом 0.
         """
    if st == "accounts" and tt == "message":
        try:
            response = session.query(rwObjects.Reference). \
                filter(rwObjects.and_(0 == rwObjects.Reference.link,
                                      rwObjects.Reference.target_uuid == source_uuid)).one()
        except Exception as e:
            raise Exception(str(e))
        else:
            owner_uuid = response.source_uuid
            print "Линкуем %s с %s " % (owner_uuid, target_uuid)
        """Делаем линкование объектов """
        rwObjects.link_objects(session, owner_uuid, target_uuid)

        """
        Правило 2. Empl создает Empl
        Если S = Employee и T = Employee, то связываем нового пользователя с Компанией.
            Пользователя создает суперюзер, он связан со своей компанией линком весом 0.
        """
    elif st == "" and tt == "":
        # 1. Находим компанию
        pass

        """
        Правило 3. Empl создает Acc
        Если S = Employee и T = Account, то связываем новый Аккаунт с Пользователем.
        """
    elif st == "" and tt == "":
        # 1.
        pass

    """
    Линкуем стандартные объекты в момент создания со стандартными ветками дерева знаний.
    Стандартные типы объектов перечисленны в STANDARD_OBJECT_TYPES.
    Если ветки в ДЗ нет, то она создается в корне дерева.
    """
    standard = rwObjects.STANDARD_OBJECTS_TYPES
    classes = dict()
    try:
        response = session.query(rwObjects.KnowledgeTree).all()
    except Exception as e:
        raise Exception("Ошибка чтения ДЗ." + str(e))
    else:
        pass
    for leaf in response:
        cls = leaf.get_objects_classes()
        for c in cls:
            if c not in classes.keys():
                classes[c] = leaf.uuid

    print classes.keys()
    print standard
    print tt
    if tt in standard and tt in classes.keys():
        rwObjects.link_objects(session, classes[tt], target_uuid)
        pass

    session.close()
    return "OK"
