# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""

import datetime
import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_queue_module as rwQueue
import prototype1_email_module as rwEmail
import prototype1_type_classifiers as rwLearn
import json
import sys
import time
import base64
import pymongo
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rc
rc('font',**{'family':'serif'})
rc('text', usetex=True)
rc('text.latex',unicode=True)
rc('text.latex',preamble='\usepackage[utf8]{inputenc}')
rc('text.latex',preamble='\usepackage[russian]{babel}')
import re

reload(sys)
sys.setdefaultencoding("utf-8")

session = rwObjects.Session()
# m = rwObjects.get_email_message(session,['af3f1230-3f71-11e5-be81-f46d04d35cbd'])
# obj = rwObjects.get_by_uuid('b1c4a3e2-3c58-11e5-b1af-f46d04d35cbd')[0]



"""

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

#text = rwObjects.get_by_uuid('b1b90f50-42b1-11e5-b537-f46d04d35cbd')[0]
#print str(text.text_plain)


#probe,Z = rwLearn.predict('ed38261a-41cb-11e5-aae5-f46d04d35cbd',[text.text_plain])

#print 'Вероятности : %s' % probe
#print 'UUID категори : %s' % Z

## t = rwObjects.get_by_uuid('ed38261a-41cb-11e5-aae5-f46d04d35cbd')[0].targets
#print t

#rwLearn.autoclassify_all_notlinked_objects()

#s = rwLearn.retrain_classifier(session,'ed38261a-41cb-11e5-aae5-f46d04d35cbd')
#print s[0]
#print s[1]

#obj = rwObjects.get_by_uuid('536c5204-41c1-11e5-8564-f46d04d35cbd')[0]
#obj.clear_text()
#fd,fl= rwLearn.email_specfeatures(obj,{})

#for i in fl:
#    print i


#print len(fd.keys())
#print len(fl)

#print obj.__dict__['text_clear']


custom = rwObjects.get_by_uuid('374e6f1e-42b4-11e5-9881-f46d04d35cbd')[0]
print custom.__dict__['custom_category']
print custom.__dict__['system_category']
print custom.__dict__['custom_category'][0].name

session.close()
