# -*- coding: utf-8 -*-
"""
Created on Thu Jul 30 15:47:43 2015

@author: sergey

Дерево знаний и тегирование объектов.
"""

import pandas as pd
import prototype1_objects_and_orm_mappings as rwObjects
import datetime
import json
import re
import pymorphy2
from time import time
import chardet


import base64
from sklearn.externals import joblib
import sqlalchemy


import sys
reload(sys)
sys.setdefaultencoding("utf-8")


def test():
    
    kt =  rwObjects.KnowledgeTree()   
    s,o = kt.return_full_tree('string')
    print s
    print o

    
test()