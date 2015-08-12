# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""

import datetime
import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_queue_module as rwQueue
import prototype1_email_module as rwEmail
import json
import sys
import time
import base64
import pymongo
import networkx as nx
import matplotlib.pyplot as plt

reload(sys)
sys.setdefaultencoding("utf-8")



session = rwObjects.Session()
#m = rwObjects.get_email_message(session,['af3f1230-3f71-11e5-be81-f46d04d35cbd'])
#obj = rwObjects.get_by_uuid('b1c4a3e2-3c58-11e5-b1af-f46d04d35cbd')[0]





client = pymongo.MongoClient()
db = client['test']
emails = db.test

#emails.drop()
#msg = rwObjects.Message()
#email_id = emails.insert_one({'name':'type'}).inserted_id

#print type(str(email_id))
#print str(email_id)

#print db.collection_names()
#print emails.find()
"""
for e in emails.find():
    print e.keys()
    print type(e['_id'])
    do = rwObjects.DynamicObject()
    e['obj_type'] = 'message'
    s = do.write(session,e)
    print s

    #Создаем Reference на новый объект
    ref = rwObjects.Reference(source_uuid=obj.uuid,
                    source_type=obj.__tablename__,
                    source_id=obj.id,
                    target_uuid=do.uuid,
                    target_type=do.__tablename__,
                    target_id=do.id,
                    link=1)


    # Записываем объект
    r_status = ref.create(session)

session.close()
"""


session = rwObjects.Session()

tt = 'message'
target_uuid = '80fe9474-4014-11e5-953b-f46d04d35cbd'

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
