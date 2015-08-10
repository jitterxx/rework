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

reload(sys)
sys.setdefaultencoding("utf-8")



session = rwObjects.Session()
m = rwObjects.get_email_message(session,['af3f1230-3f71-11e5-be81-f46d04d35cbd'])
obj = rwObjects.get_by_uuid('af3f1230-3f71-11e5-be81-f46d04d35cbd')[0]

print obj.get_message_body()

print m['af3f1230-3f71-11e5-be81-f46d04d35cbd']['from']




#client = pymongo.MongoClient()
#db = client['test']
#emails = db.test

#emails.drop()
#msg = rwObjects.Message()
#email_id = emails.insert_one(['name','type']).inserted_id

##print db.collection_names()
#print emails.find()
#for e in emails.find():
#    print e['_id']
#    print type(e['_id'])
#    pass

