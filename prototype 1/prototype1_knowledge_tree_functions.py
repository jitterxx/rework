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
import inspect    

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


def get_edges_for_object(uuid):
    """
    Возращает связи указанного объекта с другими.
    """
    edges = []
    
    session = rwObjects.Session()
    
    try:
        query = session.query(rwObjects.Reference).\
                filter(rwObjects.Reference.source_uuid == uuid)
    except :
        print "Нет связей."
    else:
        for each in query.all():
            edges.append({'uuid':each.target_uuid,'type':each.target_type})
    
    try:
        query = session.query(rwObjects.Reference).\
                filter(rwObjects.Reference.target_uuid == uuid)
    except :
        print "Нет связей."
    else:
        for each in query.all():
            edges.append({'uuid':each.source_uuid,'type':each.source_type})
    
    
    return edges
    
    
def test():
    
    kt =  rwObjects.KnowledgeTree()   
    s,o = kt.return_full_tree('string')
    #print s
    #print o

    
    #print get_edges_for_object('d004073c-31fc-11e5-9635-f46d04')

    print rwObjects.get_by_uuid('e9fa9342-3614-11e5-b267-f46d04d35cbd')[0].uuid
    
    
test()