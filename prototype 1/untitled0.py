# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""

import datetime

tt = datetime.datetime.now()
st = tt.strftime("%d-%b-%Y")
#25-may-2015

print tt
print type(st)