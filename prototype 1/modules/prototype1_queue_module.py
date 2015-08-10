# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:11:50 2015

@author: sergey

Воркеры для очереди задач.

"""



import celery
import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_email_module as rwEmail
from datetime import timedelta,datetime





import sys
reload(sys)
sys.setdefaultencoding("utf-8")


app = celery.Celery('tasks', backend='rpc://', broker='amqp://guest@localhost//')





@app.task()
def msg_delivery_for_user(uuid):

    session = rwObjects.Session()
    refs = session.query(rwObjects.Reference).\
                filter(rwObjects.and_(rwObjects.Reference.source_uuid == uuid,
                                                 rwObjects.Reference.target_type == "accounts",
                                                 rwObjects.Reference.link == 0)).all()

    for acc in refs:
        print type(acc)
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
    status = [True,"OK"]

    try:
        account = rwObjects.get_by_uuid(account_uuid)[0]
    except Exception as e:
        status = [False,"Указанный аккаунт не найден.\n"+account_uuid+str(e)]
        return status[1]
    else:
        pass

    """Получаем сообщения"""
    if account.acc_type == 'email':
        print "Подключаюсь к " + str(account.login) + "..."
        try:
            emails,status = rwEmail.get_emails(account)
            #print emails
        except Exception as e:
            status = [False,'Ошибка получения сообщений.\n' + str(e)]
            return status[1]
        else:
            pass

        """
        Запись сообщения в МонгоДБ
        """
        import pymongo
        client = pymongo.MongoClient()
        db = client.messages
        mongo_msg = db.emails

        for email in emails.values():
            msg = rwObjects.Message()

            print "----------Начало записи в Монго------------------"
            email['_id'] = str(msg.uuid)
            email['uuid'] = email['_id']
            email['channel_type'] = account.acc_type
            try:
                tt = mongo_msg.find_one({"message-id": email['message-id']})
            except Exception as e:
                print "Ошибка...",e
                raise Exception(e)

            if not tt:
                print "----------Начало записи объекта " + email['_id'] + "------------------"
                msg_id = mongo_msg.insert_one(email).inserted_id
                print "----------Конец записи объекта" + msg_id + " ------------------"
            else:
                print "Такой email уже существует msg_id: %s" % email['message-id']

            print "---------- Окончание записи в Монго------------------"

            """
            В ситуации когда письма отправляются внутри организации, т.е. между суотрудниками,
            проверяем существование сообщения в базе.
            Одно и тоже сообщение будет записано один раз.
            В дальнейшем может быть связано с двумя сотрудниками.
            """
            if not msg.is_exist_msg(session,email['message-id']):
                print email['message-id']
                print "Сообщение добавлено."
                print "----------------------------------------------"
                msg_status = msg.create_email(session,account,mongo_msg._Collection__full_name,email['message-id'])

                print msg_status[0][1]
                print msg_status[1][1]
            else:
                print email['message-id']
                print "Сообщение уже существует. Не добавлено."
                print "----------------------------------------------"

    account.last_check = datetime.now()
    session.commit()
    session.close()

    return "OK."


@app.task()
def apply_rules(source_uuid,source_type,target_uuid,target_type):
    """
    В момент создания связи между объектами проходит проверка Бизнес правил.
    Эта функция вызывается автоматически при вызове функции Reference.create()
    :param ref: объект класса Reference()
    """
    session = rwObjects.Session()
    """Правило 1.
        Если S = Account и T = Message, то связываем Сотрудника владеющего аккаунтом и сообщение.
            Владелец аккаунта всегда один и связан с ним связью весом 0.
     """
    if target_type == "messages" and source_type == "accounts":
        try:
            response = session.query(rwObjects.Reference).\
                filter(rwObjects.and_(0 == rwObjects.Reference.link,
                                      rwObjects.Reference.target_uuid == source_uuid)).one()
        except Exception as e:
            raise Exception(str(e))
        else:
            owner_uuid = response.source_uuid
            print owner_uuid
        """Ставим в очередь линкование объектов """
        rwObjects.link_objects(session,owner_uuid,target_uuid)

    session.close()
    return "OK"
