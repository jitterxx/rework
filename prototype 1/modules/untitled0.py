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

reload(sys)
sys.setdefaultencoding("utf-8")



account = rwObjects.get_by_uuid("f4efd818-3c52-11e5-bbe0-f46d04d35cbd")[0]

emails = rwEmail.get_emails(account)[0]
print emails.keys()

for email in emails.values():
    pass
    #print "Text : \n",email['text']
    #print "Raw text : \n",email['raw_text']
    #print "To : ",email['to']
    #print "From : ",email['from']
