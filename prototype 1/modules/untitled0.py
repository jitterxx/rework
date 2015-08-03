# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""

import datetime
import prototype1_objects_and_orm_mappings as rw
import json
import sys
reload(sys)
sys.setdefaultencoding("utf-8")


cc = rw.get_by_uuid('beae5a9a-39e1-11e5-9c9e-f46d04d35cbd')[0]


for a in cc.get_attrs():
    print "a,b : ",a
    
    
print type(cc)
for i in cc.get_attrs():
    print i,cc.__dict__[i]