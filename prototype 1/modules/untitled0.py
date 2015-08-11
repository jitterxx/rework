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

obj = rwObjects.get_by_uuid('0b22ec78-4014-11e5-9245-f46d04d35cbd')[0]
obj.read()


obj1 = rwObjects.get_by_uuid('0a2ae668-4014-11e5-9245-f46d04d35cbd')[0]
obj1.read()

print obj
print obj1

G = nx.Graph()
G.add_node(str(obj.uuid),comment = obj)
G.add_node(str(obj1.uuid))
G.add_node(str(obj.uuid),comment = obj)
G.add_node(str(obj1.uuid))

G.add_edge(str(obj.uuid),str(obj1.uuid))
#G[str(obj.uuid)]['comment'] = 'comment'


print G.number_of_nodes()
print G.number_of_edges()
print G.nodes()
print G.edges()




G.clear()
response = session.query(rwObjects.Reference).filter(rwObjects.Reference.link == 0).all()

labels = {}
for line in response:
    G.add_node(str(line.source_uuid),obj = line.source_type)
    G.add_node(str(line.target_uuid),obj = line.target_type)
    G.add_edge(str(line.source_uuid),str(line.target_uuid), comment = 'создан')

for node in G.nodes():
    obj = rwObjects.get_by_uuid(node)[0]
    labels[node]=obj.NAME


#print G.number_of_nodes()
#print G.number_of_edges()
#print G.nodes()
#print G.edges()
#print G.node[str(obj.uuid)]


from matplotlib import rc
rc('font',**{'family':'serif'})
rc('text', usetex=True)
rc('text.latex',unicode=True)
rc('text.latex',preamble='\usepackage[utf8]{inputenc}')
rc('text.latex',preamble='\usepackage[russian]{babel}')

pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G,pos)
nx.draw_networkx_labels(G,pos,labels=labels, font_size=10)
nx.draw_networkx_edges(G,pos)
nx.draw
