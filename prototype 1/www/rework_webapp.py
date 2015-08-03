# -*- coding: utf-8 -*-


"""

"""

import sys
reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append('/home/sergey/test/rework/prototype 1/modules')


import prototype1_objects_and_orm_mappings as rwObjects
import cherrypy
from auth import AuthController, require, member_of, name_is
from mako.template import Template
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=["./html"])


class Company(object):
    """
    Работа с отображением объектов Companies
    """

    _cp_config = {
        'auth.require': [member_of('admin')]
    }
    
    def _cp_dispatch(self, vpath):
        """
        Обаработка REST URL
        """
        
        if len(vpath) == 1:
            cherrypy.request.params['uuid'] = vpath[0]
            return show_object()
        elif len(vpath) == 2 and vpath[1] == 'edit':
            cherrypy.request.params['uuid'] = vpath[0]            
            return edit_object()
        elif len(vpath) == 0:
            return self
            
        return vpath

    @cherrypy.expose
    def index(self):
        
        tmpl = lookup.get_template("index.html")
        session = rwObjects.Session()
        companies = session.query(rwObjects.Company).all()
        s = ""
        for k in companies:
            s = s + k.name + " : " + k.uuid + "<br>"
        
        return  tmpl.render(obj = companies,string = s)


class Employee(object):
    """
    Работа с отображением объектов Employee
    """

    _cp_config = {
        'auth.require': [member_of('admin')]
    }
    
    def _cp_dispatch(self, vpath):
        """
        Обаработка REST URL
        """
        
        if len(vpath) == 1:
            cherrypy.request.params['uuid'] = vpath[0]
            return show_object()
        elif len(vpath) == 2 and vpath[1] == 'edit':
            cherrypy.request.params['uuid'] = vpath[0]            
            return edit_object()
        elif len(vpath) == 0:
            return self
            
        return vpath

    @cherrypy.expose
    def index(self):
        
        session = rwObjects.Session()
        users = session.query(rwObjects.Employee).all()
        s = ""
        for k in users:
            s = s + k.name + " : " + k.uuid + "<br>"
        
        return s


class Timeline(object):
    """
    Работа с отображением объектов Reference
    """

    _cp_config = {
        'auth.require': [member_of('admin')]
    }
    
    def _cp_dispatch(self, vpath):
        """
        Обаработка REST URL
        """
        
        if len(vpath) == 1:
            cherrypy.request.params['uuid'] = vpath[0]
            return show_object()
        elif len(vpath) == 2 and vpath[1] == 'edit':
            cherrypy.request.params['uuid'] = vpath[0]            
            return edit_object()
        elif len(vpath) == 0:
            return self
            
        return vpath

    @cherrypy.expose
    def index(self):
        
        tmpl = lookup.get_template("employee.tpl")
        session = rwObjects.Session()
        users = session.query(rwObjects.Reference).all()
        keys = users[0].get_attrs()

        print "Ключи объекта: ",keys
        
        return  tmpl.render(obj = users,keys = keys)



class edit_object():
    @cherrypy.expose
    def edit(self,uuid):        
        obj = rwObjects.get_by_uuid(uuid)[0]
        return "Редактирование %s : %s" % obj.__tablename__,obj.name

    
class show_object():
    @cherrypy.expose
    def index(self,uuid):
        obj = rwObjects.get_by_uuid(uuid)[0]
        print obj.__tablename__,obj.name
        return "Вывод данных %s : %s" % obj.__tablename__,obj.name
        
        

class RestrictedArea:
    
    # all methods in this controller (and subcontrollers) is
    # open only to members of the admin group
    
    _cp_config = {
        'auth.require': [member_of('admin')]
    }
    
    @cherrypy.expose
    def index(self):
        return """This is the admin only area."""


class Root(object):
    
    _cp_config = {
        'tools.sessions.on': True,
        'tools.auth.on': True
    }
    
    auth = AuthController()
    
    restricted = RestrictedArea()
    
    company = Company()
    employee = Employee()
    timeline = Timeline()

    @cherrypy.expose
    @require()
    def index(self):
        ss = cherrypy.request.config
        return """This page only requires a valid login.""" + str(ss)
    
    @cherrypy.expose
    def open(self):
        return """This page is open to everyone"""
    
    @cherrypy.expose
    @require(name_is("joe"))
    def only_for_joe(self):
        return """Hello Joe - this page is available to you only"""

    # This is only available if the user name is joe _and_ he's in group admin
    @cherrypy.expose
    @require(name_is("joe"))
    @require(member_of("admin"))
    # equivalent: @require(name_is("joe"), member_of("admin"))
    def only_for_joe_admin(self):
        return """Hello Joe Admin - this page is available to you only"""        



        
    


cherrypy.config.update("server.config")
cherrypy.config.update({ 
    'tools.gzip.on': True,
    'tools.sessions.on': True,
    'tools.auth.on': True
    })


if __name__ == '__main__':
   cherrypy.quickstart(Root())
