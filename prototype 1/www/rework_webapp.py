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
from mako.lookup import TemplateLookup
lookup = TemplateLookup(directories=["./templates"],output_encoding="utf-8",
                        input_encoding="utf-8",encoding_errors="replace")

class edit_object():
    @cherrypy.expose
    def edit(self,uuid):        

        try:        
            obj = rwObjects.get_by_uuid(uuid)[0]
        except Exception as e:
            print e[0]
            print e[1]
            raise cherrypy.HTTPRedirect("/")
        else:
            tmpl = lookup.get_template("edit_object.html")                    
            obj_keys = obj.get_attrs()
            f = obj.get_fields()
    
            
            return tmpl.render(obj = obj,keys = obj_keys,
                               session_context = cherrypy.session.get('session_context'),
                                all_f = f[0],
                                view_f = f[1],
                                edit_f = f[2])

    
class show_object():
    @cherrypy.expose
    def index(self,uuid):
        
        tmpl = lookup.get_template("show_object.html")
        try:        
            obj = rwObjects.get_by_uuid(uuid)[0]
        except Exception as e:
            print e[0]
            print e[1]
            raise cherrypy.HTTPRedirect("/")
        else:
            print "OK"
            obj_keys = obj.get_attrs()
            f = obj.get_fields()
            
            return tmpl.render(obj = obj,keys = obj_keys, 
                               session_context = cherrypy.session.get('session_context'),
                                all_f = f[0],
                                view_f = f[1])
        

class save_object():
 
    @cherrypy.expose    
    def save(self, **kwargs):
        data = cherrypy.request.params

        session_context = cherrypy.session.get('session_context')
        url = session_context['back_ref']
        print "Данные из запроса : "
        print data
        print "\nСохраняем объект...\n"        
        
        try:        
            status = rwObjects.set_by_uuid(data['uuid'],data)
        except Exception as e:
            print e[0]
            print e[1]
            raise cherrypy.HTTPRedirect(url)
        else:
        
        
            print "\n SAVE."
            print status[0]
            print status[1]
        
            print "Переадресация на show_object... ",url
            #print cherrypy.request.__dict__
            raise cherrypy.HTTPRedirect(url)

         




class Employee(object):
    """
    Работа с отображением объектов Employee
    """
    
    _cp_config = {
        'auth.require': [member_of('users')]
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
        elif len(vpath) == 2 and vpath[1] == 'save':
            return save_object()
            
        elif len(vpath) == 0:
            return self
            
        return vpath

    @cherrypy.expose
    def index(self):
        
        tmpl = lookup.get_template("employee.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/employee'
        session = rwObjects.Session()
        users = session.query(rwObjects.Employee).\
                filter_by(comp_id = session_context['comp_id']).all()
        obj_keys = users[0].get_attrs()
        f = users[0].get_fields()
        session.close()
            
        return tmpl.render(obj = users,keys = obj_keys, 
                           session_context = session_context,
                           view_f = f[1],
                           all_f = f[0])


    @cherrypy.expose
    def add(self):
        
        tmpl = lookup.get_template("add.html")
        session_context = cherrypy.session.get('session_context')
        session = rwObjects.Session()
        obj = session.query(rwObjects.Employee).\
                filter_by(uuid = session_context['uuid']).one()
        obj_keys = obj.get_attrs()
        f = obj.get_fields()
            
        return tmpl.render(obj = obj,keys = obj_keys, name = obj.NAME,
                           session_context = session_context,
                           all_f = f[0],
                           create_f = f[3])

    @cherrypy.expose
    def create_new(self,**kwargs):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        url = session_context['back_ref']

        params = {}
        params['login'] = data['login']
        params['company_prefix'] = data['company_prefix']
        params['name'] = data['name']
        params['password'] = data['password']
        params['surname'] = data['surname']
        params['comp_id'] = session_context['comp_id']

        source = rwObjects.get_by_uuid(session_context['uuid'])[0]
        print "Данные из запроса : "
        print params
        print "\nКонтекст :"        
        print session_context
        print "Переадресация на show_object... ",url
        print source
        
        try:
            rwObjects.create_new_employee(None,params,source)
        except Exception as e:
            print e
        else:
            print "Создан."

        raise cherrypy.HTTPRedirect(url)

class Clients(object):
    """
    Работа с отображением объектов Клиент
    """
    
    _cp_config = {
        'auth.require': [member_of('users')]
    }
    
    @cherrypy.expose
    def index(self):
        
        tmpl = lookup.get_template("clients.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/clients'
        session = rwObjects.Session()
        objs = session.query(rwObjects.Client).all()
        obj_keys = []
        session.close()
        
        if objs:        
            obj_keys = objs[0].get_attrs()
            f = objs[0].get_fields()
            
            return tmpl.render(obj = objs,keys = obj_keys, 
                           session_context = session_context,
                           all_f = f[0],
                           view_f = f[1])
        else:
            return tmpl.render(obj = objs,keys = obj_keys, 
                           session_context = session_context,
                           all_f = {"":""},
                           view_f = [""])
            


class Timeline(object):
    """
    Работа с отображением объектов Reference
    """

    _cp_config = {
        'auth.require': [member_of('users')]
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
        

        tmpl = lookup.get_template("timeline.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/timeline'
        session = rwObjects.Session()
        events = session.query(rwObjects.Reference).\
                    order_by(rwObjects.Reference.timestamp).all()
        obj_keys = events[0].get_attrs()
        f = events[0].get_fields()
        actors = {}
        
        for event in events:
            print event.source_uuid
            print event.target_uuid
            try:        
                obj = rwObjects.get_by_uuid(event.source_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                raise cherrypy.HTTPRedirect(session_context['back_ref'])
            else:
                if event.source_uuid not in actors.keys():
                    actors[event.source_uuid] = [obj.NAME]
                    actors[event.source_uuid].append(obj.__dict__[obj.VIEW_FIELDS[0]])
                    actors[event.source_uuid].append(obj.__dict__[obj.VIEW_FIELDS[1]])

            try:        
                obj = rwObjects.get_by_uuid(event.target_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                raise cherrypy.HTTPRedirect(session_context['back_ref'])
            else:
                if event.target_uuid not in actors.keys():
                    actors[event.target_uuid] = [obj.NAME]
                    actors[event.target_uuid].append(obj.__dict__[obj.VIEW_FIELDS[0]])
                    actors[event.target_uuid].append(obj.__dict__[obj.VIEW_FIELDS[1]])
            
            
        return tmpl.render(obj = events,keys = obj_keys, 
                           session_context = session_context,
                           all_f = f[0],
                           view_f = f[1],
                           actors = actors)


class KTree(object):
    """
    Работа с отображением Дерева Знаний
    """

    _cp_config = {
        'auth.require': [member_of('users')]
    }
    
    @cherrypy.expose
    def index(self):
        
        tmpl = lookup.get_template("ktree.html")
        session = rwObjects.Session()
        t = rwObjects.KnowledgeTree()
        tree = t.return_full_tree(session,'string')
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/ktree'

        return tmpl.render(obj = tree, 
                           session_context = session_context)

class Any_object(object):
    """
    Работа любыми объектами
    """

    _cp_config = {
        'auth.require': [member_of('users')]
    }
    
    def _cp_dispatch(self, vpath):
        """
        Обработка REST URL
        """
        
        if len(vpath) == 1:
            cherrypy.request.params['uuid'] = vpath[0]
            print "Показываем объект : ",vpath
            return show_object()
        elif len(vpath) == 2 and vpath[1] == 'edit':
            cherrypy.request.params['uuid'] = vpath[0]            
            print "редактируем объект : ",vpath
            return edit_object()
        elif len(vpath) == 2 and vpath[1] == 'save':
            print "Сохраняем объект : ",vpath
            return save_object()
       
        elif len(vpath) == 0:
            print "Вывод переадресации : ",vpath
            return self
            
        return vpath

    @cherrypy.expose
    def index(self):
        
        print "Переадресация на : / "
        #print cherrypy.request.__dict__
        raise cherrypy.HTTPRedirect("/")



    

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
    
    object = Any_object()
    employee = Employee()
    timeline = Timeline()
    clients = Clients()
    ktree = KTree()


    @cherrypy.expose
    @require()
    def index(self):
        tmpl = lookup.get_template("dashboard.html")
        c = get_session_context(cherrypy.request.login)
        params = cherrypy.request.headers
        return tmpl.render(params = params, session_context = c)
    
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


def get_session_context(login):
    context = cherrypy.session.get('session_context')
    user = rwObjects.get_employee_by_login(login)
    for key in user.get_attrs():
        context[key] = user.__dict__[key]
    
    context['company'] = rwObjects.get_company_by_id(user.comp_id).name
    context['company_uuid'] = rwObjects.get_company_by_id(user.comp_id).uuid
    context['company_prefix'] = rwObjects.get_company_by_id(user.comp_id).prefix    
    context['groups'] = None
    context['back_ref'] = "/"
    context['username'] = context['login'].split("@",1)[0]

    
    
    for group in ['admin','users']:
        if member_of(group):
            if context['groups']:
                context['groups'] = context['groups'] + "," + group
            else:
                context['groups'] = group                
    
    cherrypy.session['session_context'] = context

    return context
        
    


cherrypy.config.update("server.config")
cherrypy.config.update({ 
    'tools.gzip.on': True,
    'tools.sessions.on': True,
    'tools.auth.on': True
    })


if __name__ == '__main__':
   cherrypy.quickstart(Root(),'/', "app.config")
