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

l = [['name', 'Имя'], ['surname', 'Фамилия'], ['login', 'Имя пользователя'], ['password', 'Пароль']]


result = rwQueue.get_messages_for_account.delay("b1c4a3e2-3c58-11e5-b1af-f46d04d35cbd")

print result



