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
import prototype1_type_classifiers as rwLearn
from kombu import Exchange, Queue
from configurations import *

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

celery.Celery.CELERY_QUEUES = (Queue(QUEUE_NAME, Exchange(QUEUE_NAME), routing_key=QUEUE_NAME))
celery.Celery.CELERY_DEFAULT_QUEUE = QUEUE_NAME
celery.Celery.CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'
celery.Celery.CELERY_DEFAULT_ROUTING_KEY = QUEUE_NAME
celery.Celery.CELERY_ACCEPT_CONTENT = ['json', 'msgpack', 'yaml']
app = celery.Celery('tasks_' + QUEUE_NAME, backend=QUEUE_BROKER_BACKEND, broker=QUEUE_BROKER)


@app.task(queue=QUEUE_NAME)
def msg_delivery_for_user(uuid):
    session = rwObjects.Session()
    user = rwObjects.get_by_uuid(uuid)[0]
    if user.disabled != 0:
        print "Пользователь %s отключен." % user.uuid
        return "Disabled."
    else:
        refs = session.query(rwObjects.Reference). \
            filter(rwObjects.and_(rwObjects.Reference.source_uuid == uuid,
                                  rwObjects.Reference.target_type == "accounts",
                                  rwObjects.Reference.link == 0)).all()

        for acc in refs:
            # print type(acc)
            get_messages_for_account.delay(acc.target_uuid)
        return "OK"


@app.task(queue=QUEUE_NAME)
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
    if account.acc_type == 'email' and account.disabled == 0:
        print "Подключаюсь к " + str(account.login) + "..."
        try:
            emails, status = rwEmail.get_emails(account)
            # print emails
        except Exception as e:
            status = [False, 'Ошибка получения сообщений.\n' + str(e)]
            print status[1]
            return status[1]
        else:
            pass
            print "Сообщения получены."

        """
        Запись сообщения в SQL и МонгоДБ
        """
        for email in emails.values():
            do = rwObjects.DynamicObject()
            email['channel_type'] = rwObjects.rwChannel_type[0]
            email['obj_type'] = do.obj_type = do.collection = 'messages'

            if 'message-id' not in email.keys():
                print "Сообщение без Message-ID. Не записано."
            elif not do.check({"message-id": email['message-id']}):
                print "----------Начало записи в Монго------------------"
                s = do.write(session, email)

                print "---------- Окончание записи в Монго------------------"

                if s[0]:
                    print "Создаем Reference на новый объект "
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

    else:
        print "Аккаунт %s отключен." % account_uuid

    account.last_check = datetime.now()
    session.add(account)
    session.commit()

    print "Время последней проверки : %s" % account.last_check

    session.close()

    return "OK."


@app.task(queue=QUEUE_NAME)
def apply_rules_for_1(source_uuid, source_type, target_uuid, target_type):
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

        """
        Objects Rule #1
        Acc создает Msg
        Если S = Account и T = Messages, то связываем Сотрудника владеющего аккаунтом и сообщение.
        Владелец аккаунта всегда один и связан с ним связью весом 0.
         """
    if st == "accounts" and tt == "messages":
        try:
            response = session.query(rwObjects.Reference). \
                filter(rwObjects.and_(0 == rwObjects.Reference.link,\
                                      rwObjects.Reference.target_uuid == source_uuid,\
                                      rwObjects.Reference.source_type == 'employees')).one()
        except Exception as e:
            raise Exception(str(e))
        else:
            owner_uuid = response.source_uuid
            print "Objects Rule #1"
            print "Линкуем %s с %s " % (owner_uuid, target_uuid)
            """Делаем линкование объектов """
            rwObjects.link_objects(session, owner_uuid, target_uuid)

        """
        Objects Rule #1.1
        Acc создает Msg
        Если S = Account и T = Messages, то ищем о полю References в новом сообщении, существующие сообщения
        с входящими в него message-id. Если находим линкуем.
         """
        # Получаем новый объект класса DO
        try:
            new_msg = rwObjects.get_by_uuid(target_uuid)[0]
        except Exception as e:
            raise Exception(str(e))
        all = dict()

        # Получаем все сообщения и записываем их id и uuid
        try:
            resp = session.query(rwObjects.DynamicObject).all()
        except Exception as e:
            raise Exception(str(e))

        for msg in resp:
            try:
                obj = rwObjects.get_by_uuid(msg.uuid)[0]
            except Exception as e:
                raise Exception(str(e))
            all[obj.__dict__['message-id'].strip("[ |<|>]")] = msg.uuid

        # Если есть поле References, то работаем по нему, иначе ничего не делаем
        if 'references' in new_msg.__dict__.keys():
            refs = list()
            for r in new_msg.__dict__['references'].split(" "):
                refs.append(r.strip("[ |<|>]"))

            links = list()
            for r in refs:
                if r in all.keys():
                    links.append([all[r],new_msg.uuid])
            print links
            for l in links:
                rwObjects.link_objects(session, l[0], l[1])


        """
        Objects Rule #2
        Правило 2. Empl создает Empl
        Если S = Employee и T = Employee, то связываем нового пользователя с Компанией.
            Пользователя создает суперюзер, он связан со своей компанией линком весом 0.
        """
    elif st == "" and tt == "":
        # 1. Находим компанию
        pass

        """
        Objects Rule #3
        Правило 3. Empl создает Acc
        Если S = Employee и T = Account, то связываем новый Аккаунт с Пользователем.
        """
    elif st == "" and tt == "":
        # 1.
        pass

    """
    Knowledge Rule #1
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

    #print classes.keys()
    #print standard
    print "Проверка Knowledge Rule #1 для :",tt
    if tt in standard and tt in classes.keys():
        print "Выполняем Knowledge Rule #1"
        rwObjects.link_objects(session, classes[tt], target_uuid)
        pass


    """
    Knowledge Rule #2
    Класифицируем объекты типы которых указаны в константе FOR_CLASSIFY.
    """
    print "Проверка Knowledge Rule #2 для : %s" % tt
    status = rwLearn.check_conditions_for_classify()
    if not status[0]:
        raise Exception("Не соблюдены условия для тренировки." + status[1])

    if tt in rwObjects.FOR_CLASSIFY:
        print "-------- Классифицируем объект : %s ---------" % target_uuid
        obj = rwObjects.get_by_uuid(target_uuid)[0]
        clf_uuid = rwObjects.default_classifier
        obj.clear_text()
        print str(obj.text_plain)
        probe, Z = rwLearn.predict(clf_uuid, [obj.text_plain])
        print 'Вероятности : %s' % probe
        categories = rwObjects.get_ktree_custom(session)
        print 'Категория : %s' % categories[Z[0]].name
        print "--------------Классификация закончена.------------------"

        # Сохраняем результаты классификации
        status = rwLearn.save_classification_result(session,target_uuid,clf_uuid,probe)
        if status[0]:
            print "Данные классификации сохранены."
        else:
            print "Данные классификации НЕ сохранены."

    session.close()
    return "OK"


@app.task(queue=QUEUE_NAME)
def apply_rules_for_0(source_uuid, source_type, target_uuid, target_type):
    """
    В момент появления связи между объектами проходит проверка правил.
    Эта функция вызывается автоматически при вызове функции Reference.create() когда link = 0.

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

    """
    Rule #1
     При связывании ветки Навигатора Знаний и DO, проверяем какую операцию надо выполнить согласно настройкам ветки.
     Если не no, то выполняем операцию.
    """
    if st == 'knowledge_tree' and target_type == 'dynamic_object':
        source_obj = rwObjects.get_by_uuid(source_uuid)[0]
        if source_obj.__class__.__name__ != 'KnowledgeTree' and source_obj.action == 'no':
            print "\n ----- Rule #1. Ничего не делаем -----\n"
            return "OK."

        print source_obj.action
        if source_obj.action == 'create_case':
            print "\nСоздаем кейс\n"
        else:
            pass



