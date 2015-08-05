# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""

import datetime
import prototype1_objects_and_orm_mappings as rwObjects
import json
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


l = [['name','Имя'],['surname','Фамилия'],['login','Имя пользователя'],['password','Пароль']]


session = rwObjects.Session()

t = rwObjects.get_by_uuid('c34519e0-39e1-11e5-9c9e-f46d04d35cbd')[0]

print t.VIEW_FIELDS[:]
print t.__dict__['surname']

print t.get_attrs()


