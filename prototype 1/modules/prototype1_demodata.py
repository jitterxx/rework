# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 15:47:43 2015

@author: sergey

Загрузка демо данных.
"""

from bs4 import BeautifulSoup
from urllib2 import urlopen
import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_type_classifiers as rwLearn


import sys
reload(sys)
sys.setdefaultencoding("utf-8")


SITE_URL = "http://toster.ru/questions/latest?page=%s"
#SITE_URL = "https://toster.ru/tag/javascript/questions?page=%s"
tags = dict()
session = rwObjects.Session()
account = rwObjects.get_by_uuid("4b0b843e-5546-11e5-a199-f46d04d35cbd")[0]

"""
Что надо сделать чтобы работало демо:
1. Создать аккаунт demo_toster
2. Привязать его к пользователю в References связью 0.
3. Создать отдельную ветку в Навигаторе Знаний внутри Сообщений, с названием Демо
4. Привязать к ней сообщения с Тостера

print "Создаем демо раздел Дерева Знаний: Тостер"
params = {'parent_id': 1, 'name': 'Тостер', 'description': 'Демонстрационные сообщения с сайта toster.ru',
          'tags': 'demo',
          'expert': account.login, 'type': 'custom'}
try:
    status, obj = rwObjects.create_new_object(session, "knowledge_tree", params, account)
except Exception as e:
    raise (e)
else:
    print status

raise Exception("СОздан раздел.")
"""

for j in range(10,15):
    print "Обработка старницы %s" % j
    html_doc = urlopen(SITE_URL % j).read()
    soup = BeautifulSoup(html_doc)

    i = 0
    for a in soup.find_all('a', {'class': 'question__title-link'}):
        message = dict()
        message['href'] = a['href']
        message['message-id'] = a['href'].rsplit('/',1)[1]

        do = rwObjects.DynamicObject()
        do.obj_type = do.collection = 'messages'
        if not do.check({"message-id": message['message-id']}):
            try:
                html_question = urlopen(a['href']).read()
                page = BeautifulSoup(html_question)
                page_body = page.find('div', {'class': 'question_full'})
                message['tags'] = list()
                for tag in page_body.find_all('li', {'class': 'tags-list__item'}):
                    t = tag.find('a').text.strip()
                    if t:
                        message['tags'].append(t)
                    if t not in tags.keys():
                        tags[t] = list()
                        tags[t].append(do.uuid)
                    else:
                        tags[t].append(do.uuid)
                message['title'] = page_body.find('h1', {'class':'question__title'}).text
                message['raw_text_plain'] = page_body.find('div', {'class':'question__text'}).text
                message['raw_text_html'] = message['raw_text_plain']
                message['channel_type'] = rwObjects.rwChannel_type[1]
                message['obj_type'] = 'messages'
            except Exception as e:
                print "Ошибка парсинга: %s" % str(e)
            else:
                print "----------Начало записи в Монго------------------"
                s = do.write(session, message)

                print "---------- Окончание записи в Монго------------------"

                if s[0]:
                    print "Создаем Reference на новый объект "
                    ref = rwObjects.Reference(source_uuid="demo_toster_uuid",
                                              source_type="accounts",
                                              source_id="0",
                                              target_uuid=do.uuid,
                                              target_type=do.__tablename__,
                                              target_id=do.id,
                                              link=1)
                    # Записываем объект
                    r_status = ref.create(session)
        else:
            print "Такое сообщение уже существует."

        i += 1
        if i == 10:
            break


def get_demo_and_prepare_for_classification(session, tags, account):
    demo_ktree = rwObjects.get_demo_ktree(session)
    demo_all = rwObjects.KnowledgeTree.ktree_return_childs(session,demo_ktree.id)
    already_tags = dict()
    for leaf in demo_all:
        if leaf.id != demo_ktree.id:
            already_tags[leaf.name] = leaf.uuid

    created = already_tags.keys()

    for key in tags.keys():
        if key not in created:
            # Добавляем новый узел
            print "Создаем демо раздел Дерева Знаний: %s" % key
            params = {'parent_id': demo_ktree.id, 'name': key, 'description': key,
                      'tags': 'demo',
                      'expert': account.login, 'type': 'custom'}
            try:
                status, obj = rwObjects.create_new_object(session, "knowledge_tree", params, account)
            except Exception as e:
                raise e
            else:
                already_tags[key] = obj.uuid
                print status[0]
                print status[1]
        else:
            print "Такой раздел уже существует в демо."

    for key in tags.keys():
        for msg in tags[key]:
            rwObjects.link_objects(session, already_tags[key], msg)

# Получить новые данные, добавить в систему и создать разделы Навигатора
get_demo_and_prepare_for_classification(session, tags, account)
rwLearn.retrain_classifier(session, rwObjects.default_classifier)

session.close()
