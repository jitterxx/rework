# -*- coding: utf-8 -*-


"""

"""

import sys

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append('/home/sergey/test/rework/prototype 1/modules')

import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_queue_module as rwQueue
import prototype1_type_classifiers as rwLearn
import cherrypy
from auth import AuthController, require, member_of, name_is
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rc

rc('font', **{'family': 'serif'})
rc('text', usetex=True)
rc('text.latex', unicode=True)
rc('text.latex', preamble='\usepackage[utf8]{inputenc}')
rc('text.latex', preamble='\usepackage[russian]{babel}')

from mako.lookup import TemplateLookup

lookup = TemplateLookup(directories=["./templates"], output_encoding="utf-8",
                        input_encoding="utf-8", encoding_errors="replace")


def ShowError(error):
    return str(error)


class EditObject():
    def __init__(self):
        pass

    @cherrypy.expose
    def edit(self, uuid):

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
            session_context = cherrypy.session.get('session_context')
            neighbors = G.neighbors(session_context['uuid'])

            print "session_context['menu'] : %s " % session_context['menu']

            if session_context['menu'] in ['accounts', 'employee', 'ktree']:
                session_context['back_ref'] = "/settings/?menu=" + session_context['menu']
            if session_context['menu'] == 'settings':
                session_context['back_ref'] = "/settings"

            session_context['menu'] = "edit_object"

            return tmpl.render(obj=obj, keys=obj_keys,
                               session_context=session_context,
                               all_f=f[0], view_f=f[1], edit_f=f[2],
                               neighbors=neighbors)


class ShowObject():
    def __init__(self):
        pass

    @cherrypy.expose
    def index(self, uuid):

        tmpl = lookup.get_template("show_object.html")
        try:
            obj = rwObjects.get_by_uuid(uuid)[0]
        except Exception as e:
            print e[0]
            print e[1]
            raise cherrypy.HTTPRedirect("/")
        else:
            obj_keys = obj.get_attrs()
            f = obj.get_fields()
            session_context = cherrypy.session.get('session_context')
            neighbors = G.neighbors(session_context['uuid'])

            print "session_context['menu'] : %s " % session_context['menu']

            if session_context['menu'] in ['accounts', 'employee']:
                session_context['back_ref'] = "/settings/?menu=" + session_context['menu']
            if session_context['menu'] == 'settings':
                session_context['back_ref'] = "/settings"

            session_context['menu'] = "show_object"
            return tmpl.render(obj=obj, keys=obj_keys,
                               session_context=session_context,
                               all_f=f[0], view_f=f[1],neighbors=neighbors)


class SaveObject():
    def __init__(self):
        pass

    @cherrypy.expose
    def save(self, **kwargs):
        data = cherrypy.request.params

        session_context = cherrypy.session.get('session_context')
        url = session_context['back_ref']
        print "Данные из запроса : "
        print data
        print "\nСохраняем объект...\n"

        try:
            status = rwObjects.set_by_uuid(data['uuid'], data)
        except Exception as e:
            print "SaveObject. Ошибка в rwObjects.set_by_uuid(data['uuid'],data) :", str(e)
            raise cherrypy.HTTPRedirect(url)
        else:
            print "\n SAVE."
            print status[0]
            print status[1]

            print "Переадресация на show_object... ", url
            # print cherrypy.request.__dict__
            raise cherrypy.HTTPRedirect(url)


class LinkObject(object):
    def __init__(self):
        pass

    @cherrypy.expose
    def addlink(self, uuid):
        data = cherrypy.request.params
        print uuid
        session = rwObjects.Session()
        tmpl = lookup.get_template("add_link_to_ktree.html")
        obj = rwObjects.get_by_uuid(uuid)[0]
        custom = rwObjects.get_ktree_custom(session)
        #print custom.keys()

        return tmpl.render(obj=obj, category=custom,
                           session_context=cherrypy.session.get('session_context'))

    @cherrypy.expose
    def savelink(self, object_uuid, object_type, category_type, category_uuid=None):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        url = session_context['back_ref']

        if not category_uuid:
            print "Не указана категория."
            raise cherrypy.HTTPRedirect(url)

        if not isinstance(category_uuid, list):
            category_uuid = [category_uuid]

        print "Obj UUID: ", object_uuid
        print "Obj type: ", object_type
        print "Category uuid:", category_uuid
        print "Category type:", category_type

        session = rwObjects.Session()
        for category in category_uuid:
            try:
                st = rwObjects.link_objects(session, category, object_uuid)
            except Exception as e:
                print "Проблемы при связывании..."
                print e
                pass
            else:
                print "Связывание прошло успешно."
                print st[0]
                print st[1]

        try:
            st = rwLearn.clear_autoclassify(session, object_uuid)
        except Exception as e:
            print "Проблемы удалении автоклассфиикации.."
            print e
        else:
            print "Удаление автоклассификации успешно."
            print st[0]
            print st[1]

        print "Переадресация на : ", url
        G.reload()
        session.close()
        raise cherrypy.HTTPRedirect(url)


class Account(object):
    """

    """
    _cp_config = {
        'auth.require': [member_of('users')]
    }

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def add(self, employee_uuid):
        """
        Ожидает в параметрах  UUID сотрудника к которому аккаунт будет привязан.
        """

        tmpl = lookup.get_template("add.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = "/settings?menu=accounts"
        session_context['employee_uuid'] = employee_uuid
        cherrypy.session['session_context'] = session_context
        obj = rwObjects.Account()
        obj_keys = obj.get_attrs()
        f = obj.get_fields()

        return tmpl.render(obj=obj, keys=obj_keys, name=obj.NAME,
                           session_context=session_context,
                           all_f=f[0], create_f=f[3], acc_type=rwObjects.rwChannel_type)

    @cherrypy.expose
    def create_new(self, **kwargs):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        employee_uuid = session_context.pop('employee_uuid')
        print employee_uuid
        print "Данные из запроса : "
        print data
        print "\nКонтекст :"
        print session_context

        params = {}

        for p in data.keys():
            params[p] = data[p]

        """
        Проверка параметров тут.
        """

        """ Извлекаем создателя и Создаем новый объект """
        source = rwObjects.get_by_uuid(session_context['uuid'])[0]
        session = rwObjects.Session()

        try:
            print "Создаем новый аккаунт."
            status, obj = rwObjects.create_new_object(session, "accounts", params, source)
        except Exception as e:
            print e
        else:
            print status

        """
        Если возвращен объект, выполняем бизнес логику.
        Если None, значит ошибка.
        """
        if obj:
            """
            Бизнес логика.
            Связываем новый аккаунт с его пользователем.
            Пользователь передается в session_context['employee_uuid']
            """
            print "Делаем линкование с пользователем при создании аккаунта."
            rwObjects.link_objects(session, employee_uuid, obj.uuid)

        session.close()

        cherrypy.session['session_context'] = session_context
        print "Переадресация на  ", session_context['back_ref']
        raise cherrypy.HTTPRedirect(session_context['back_ref'])


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
            return ShowObject()
        elif len(vpath) == 2 and vpath[1] == 'edit':
            cherrypy.request.params['uuid'] = vpath[0]
            return EditObject()
        elif len(vpath) == 2 and vpath[1] == 'add_account':
            cherrypy.request.params['employee_uuid'] = vpath[0]
            return ()

        elif len(vpath) == 0:
            return self

        return vpath

    @cherrypy.expose
    def index(self):

        tmpl = lookup.get_template("employee.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/employee'
        session = rwObjects.Session()
        users = session.query(rwObjects.Employee). \
            filter_by(comp_id=session_context['comp_id']).all()
        obj_keys = users[0].get_attrs()
        f = users[0].get_fields()
        linked_objects = dict()
        for user in users:
            refs = session.query(rwObjects.Reference). \
                filter(rwObjects.sqlalchemy.and_(rwObjects.Reference.source_uuid == user.uuid,
                                                 rwObjects.Reference.target_type == "accounts",
                                                 rwObjects.Reference.link == 0)).all()
            linked_objects[user.uuid] = []

            for ref in refs:
                linked_objects[user.uuid].append(rwObjects.get_by_uuid(ref.target_uuid)[0])

        session.close()

        return tmpl.render(obj=users, keys=obj_keys,
                           session_context=session_context,
                           view_f=f[1],
                           all_f=f[0],
                           linked=linked_objects)

    @cherrypy.expose
    def add(self):

        tmpl = lookup.get_template("add_employee.html")
        session_context = cherrypy.session.get('session_context')
        session = rwObjects.Session()
        obj = session.query(rwObjects.Employee). \
            filter_by(uuid=session_context['uuid']).one()
        obj_keys = obj.get_attrs()
        f = obj.get_fields()

        return tmpl.render(obj=obj, keys=obj_keys, name=obj.NAME,
                           session_context=session_context,
                           all_f=f[0], create_f=f[3],
                           access_groups=rwObjects.ACCESS_GROUPS)

    @cherrypy.expose
    def create_new(self, **kwargs):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        url = session_context['back_ref']

        print "Данные запроса: %s" % data

        params = dict()
        try:
            params['login'] = data['login']
            params['company_prefix'] = session_context['company_prefix']
            params['name'] = data['name']
            params['password'] = data['password']
            params['surname'] = data['surname']
            params['comp_id'] = session_context['comp_id']
            params['groups'] = data['groups']
        except KeyError as e:
            return ShowError("Функция Employee.create_new(). Ошибка KeyError: %s" % str(e))
        else:
            pass

        # Проверяем что этот параметр список, иначе делаем из одного значения список
        if not isinstance(params['groups'], list):
            params['groups'] = [params['groups']]

        """
        Проверка параметров тут.
        """
        for k in params.keys():
            if params[k] == "" or not params[k]:
                print "Параметр %s незаполнен." % k
                return ShowError("Параметр %s незаполнен." % k)

        source = rwObjects.get_by_uuid(session_context['uuid'])[0]
        print "Данные из запроса : "
        print params
        print "\nКонтекст :"
        print session_context
        print "Переадресация на show_object... ", url
        print source

        session = rwObjects.Session()

        try:
            status, obj = rwObjects.create_new_object(session, "employees", params, source)
        except Exception as e:
            return ShowError("Ошибка создания объекта. " + str(e))
        else:
            pass

        if not status[0]:
            return ShowError(str(status[0]) + str(status[1]))

        """
        Если возвращен объект, проводим привязку согласно бизнес логики.
        Если None, значит ошибка.
        """
        if obj:
            """
            Бизнес логика.
            Связываем нового пользователя с Компанией.
            """
            company = rwObjects.get_company_by_id(params['comp_id'])
            ref = rwObjects.Reference(source_uuid=company.uuid,
                                      source_type=company.__tablename__,
                                      source_id=company.id,
                                      target_uuid=obj.uuid,
                                      target_type=obj.__tablename__,
                                      target_id=obj.id,
                                      link=0)
            ref.create(session)

        session.close()
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
        session_context['menu'] = 'clients'
        session = rwObjects.Session()
        objs = session.query(rwObjects.Client).all()
        obj_keys = []
        session.close()

        if objs:
            obj_keys = objs[0].get_attrs()
            f = objs[0].get_fields()

            return tmpl.render(obj=objs, keys=obj_keys,
                               session_context=session_context,
                               all_f=f[0],
                               view_f=f[1])
        else:
            return tmpl.render(obj=objs, keys=obj_keys,
                               session_context=session_context,
                               all_f={"": ""},
                               view_f=[""])


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

        if len(vpath) == 1 and vpath[0] == 'create':
            cherrypy.request.params['view_type'] = vpath[0]
            return self
        elif len(vpath) == 1 and vpath[0] == 'links':
            cherrypy.request.params['view_type'] = vpath[0]
            return self
        elif len(vpath) == 0:
            cherrypy.request.params['view_type'] = 'all'
            return self
        return vpath

    @cherrypy.expose
    def old_index(self, view_type=None, date=None):

        print "Тип отображения: %s" % view_type
        print "Дата %s" % date
        v = ["", "", ""]

        if view_type == "links":
            link = 0
            v[2] = "active"
        elif view_type == "create":
            link = 1
            v[1] = "active"
        else:
            link = 1
            v[0] = "active"

        tmpl = lookup.get_template("old_timeline.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/timeline'
        session_context['menu'] = 'timeline'
        cherrypy.session['session_context'] = session_context
        session = rwObjects.Session()
        events = session.query(rwObjects.Reference).filter(rwObjects.Reference.link == link). \
            order_by(rwObjects.desc(rwObjects.Reference.timestamp)).all()
        obj_keys = events[0].get_attrs()
        fields = events[0].get_fields()
        actors = {}

        for event in events:
            event.read(session)
            # print "Source UUID : %s" % event.source_uuid
            # print "Target UUID : %s" % event.target_uuid
            try:
                obj = rwObjects.get_by_uuid(event.source_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                raise cherrypy.HTTPRedirect(session_context['back_ref'])
            else:
                if event.source_uuid not in actors.keys():
                    actors[event.source_uuid] = obj
                    print actors[event.source_uuid]

            try:
                obj = rwObjects.get_by_uuid(event.target_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                raise cherrypy.HTTPRedirect(session_context['back_ref'])
            else:
                if event.target_uuid not in actors.keys():
                    actors[event.target_uuid] = obj
                    print actors[event.target_uuid]

        # print "events[0].get_fields() : %s" % fields
        # print "obj_keys : %s " % obj_keys

        return tmpl.render(obj=events, keys=obj_keys,
                           session_context=session_context,
                           all_f=fields[0], view_f=fields[1],
                           actors=actors, view_type=v)

    @cherrypy.expose
    def reload(self):
        print "webapp.Timeline.reload - RELOAD graph..."
        G.reload()
        raise cherrypy.HTTPRedirect("/timeline")

    @cherrypy.expose
    def index(self, view_type=None, date=None):

        print "Тип отображения: %s" % view_type
        print "Дата %s" % date
        v = ["", "", ""]

        if view_type == "links":
            link = 0
            v[2] = "active"
        elif view_type == "create":
            link = 1
            v[1] = "active"
        else:
            link = 1
            v[0] = "active"

        tmpl = lookup.get_template("timeline.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/timeline'
        session_context['menu'] = 'timeline'
        cherrypy.session['session_context'] = session_context
        session = rwObjects.Session()
        events = session.query(rwObjects.Reference).filter(rwObjects.Reference.link == link). \
            order_by(rwObjects.desc(rwObjects.Reference.timestamp)).all()
        obj_keys = events[0].get_attrs()
        fields = events[0].get_fields()
        actors = {}
        neighbors = G.graph.neighbors(session_context['uuid'])
        neighbors.append(session_context['uuid'])

        for event in events:
            event.read(session)
            # print "Source UUID : %s" % event.source_uuid
            # print "Target UUID : %s" % event.target_uuid
            try:
                obj = rwObjects.get_by_uuid(event.source_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                raise cherrypy.HTTPRedirect(session_context['back_ref'])
            else:
                if event.source_uuid not in actors.keys():
                    actors[event.source_uuid] = obj
                    #print actors[event.source_uuid]

            try:
                obj = rwObjects.get_by_uuid(event.target_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                raise cherrypy.HTTPRedirect(session_context['back_ref'])
            else:
                if event.target_uuid not in actors.keys():
                    actors[event.target_uuid] = obj
                    #print actors[event.target_uuid]

            # print "events[0].get_fields() : %s" % fields
            # print "obj_keys : %s " % obj_keys

        return tmpl.render(obj=events, keys=obj_keys,
                           session_context=session_context,
                           all_f=fields[0], view_f=fields[1],
                           actors=actors, view_type=v,
                           neighbors=neighbors)


class KTree(object):
    """
    Работа с отображением Дерева Знаний
    """

    _cp_config = {
        'auth.require': [member_of('users')],
        'tools.sessions.on': True
    }

    def _cp_dispatch(self, vpath):
        """
        Обаработка REST URL
        """

        if len(vpath) == 1:
            cherrypy.request.params['category_uuid'] = vpath[0]
            return ShowKTreeCategory()
        elif len(vpath) == 0:
            return self

        return vpath

    @cherrypy.expose
    def index(self):

        tmpl = lookup.get_template("ktree.html")
        session = rwObjects.Session()
        tree = rwObjects.KnowledgeTree()
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/ktree'
        session_context['menu'] = 'ktree'
        cherrypy.session['session_context'] = session_context

        return tmpl.render(obj=tree, session=session,
                           session_context=session_context)

    @cherrypy.expose
    def add(self, parent_id, name):

        tmpl = lookup.get_template("add_ktree.html")
        session_context = cherrypy.session.get('session_context')
        session_context['parent_id'] = parent_id
        session_context['parent_name'] = name
        session_context['type'] = "custom"
        session = rwObjects.Session()
        obj = rwObjects.KnowledgeTree()
        obj_keys = obj.get_attrs()
        f = obj.get_fields()

        return tmpl.render(obj=obj, keys=obj_keys, name="раздел Навигатора Знаний",
                           session_context=session_context,
                           all_f=f[0],
                           create_f=f[3])

    @cherrypy.expose
    def edit(self, uuid):
        print uuid
        tmpl = lookup.get_template("edit_ktree.html")
        session_context = cherrypy.session.get('session_context')
        session = rwObjects.Session()
        obj = rwObjects.get_by_uuid(uuid)[0]
        f = obj.get_fields()
        experts = rwObjects.get_userlist_in_group(session, 'expert')
        all_leafs = obj.get_all(session)

        # print "OBJ : %s" % obj
        # print "Status experts : %s" % experts[0]
        # print "Experts : %s" % experts[1]
        # print "All leafs : %s" % all_leafs
        session.close()
        return tmpl.render(obj=obj, experts=experts[1], all=all_leafs,
                           session_context=session_context,
                           all_f=f[0], edit_f=f[2])

    @cherrypy.expose
    def save(self, **kwargs):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        url = "/settings?menu=ktree"

        print "Данные из запроса : %s" % data
        print "\nКонтекст :" % session_context

        params = dict()

        try:
            params['parent_id'] = data['parent_id']
            params['name'] = data['name']
            params['description'] = data['description']
            params['tags'] = data['tags']
            params['expert'] = data['expert']
        except Exception as e:
            raise e
        else:
            pass

        """
        Проверка параметров тут.
        """
        session = rwObjects.Session()
        try:
            st = rwObjects.set_by_uuid(data['uuid'], data)
        except Exception as e:
            return ShowError("Функция Ktree.save операция rwObjects.set_by_uuid(data['uuid'],data)" + str(e))
        else:
            print st[0]
            print st[1]

        session.close()
        raise cherrypy.HTTPRedirect(url)

    @cherrypy.expose
    def create_new(self, **kwargs):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        url = session_context['back_ref'] = "/ktree"

        print "Данные из запроса : "
        print data
        print "\nКонтекст :"
        print session_context
        print "Переадресация на show_object... ", url

        params = dict()

        try:
            params['parent_id'] = data['parent_id']
            params['name'] = data['name']
            params['description'] = data['description']
            params['tags'] = data['tags']
            params['expert'] = session_context['login']
            params['type'] = data['type']
        except Exception as e:
            raise (e)
        else:
            pass

        """
        Проверка параметров тут.
        """
        session = rwObjects.Session()
        try:
            rwObjects.KnowledgeTree.ktree_return_childs(session, params['parent_id'])
        except Exception as e:
            raise (e)
        else:
            pass
            print

        source = rwObjects.get_by_uuid(session_context['uuid'])[0]

        """
        Создаем новый объект класса KnowledgeTree
        Для каждого нового типа необходимо добавить в  create_new_object условия.
        """
        try:
            status, obj = rwObjects.create_new_object(session, "knowledge_tree", params, source)
        except Exception as e:
            raise (e)
        else:
            print status

        session.close()
        raise cherrypy.HTTPRedirect(url)

    @cherrypy.expose
    def classify(self):

        if rwLearn.check_conditions_for_classify()[0]:
            session = rwObjects.Session()
            status = rwLearn.retrain_classifier(session, rwObjects.default_classifier)
            print status[0]
            print status[1]

        session.close()
        raise cherrypy.HTTPRedirect("/ktree")


class ShowKTreeCategory(object):
    @cherrypy.expose
    def index(self, category_uuid):

        tmpl = lookup.get_template("ktree_show_category.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/ktree'
        session_context['menu'] = 'ktree_category'
        if session_context['menu'] == 'ktree_category':
            session_context['back_ref'] = '/ktree/' + str(category_uuid)
            session_context['menu'] = 'ktree_category'

        if session_context['menu'] == 'ktree_settings':
            session_context['back_ref'] = '/settings?menu=ktree'
            session_context['menu'] = 'ktree_settings'

        cherrypy.session['session_context'] = session_context

        #print category_uuid

        session = rwObjects.Session()
        leaf = rwObjects.get_by_uuid(category_uuid)[0]
        nodes = list()
        neighbors = G.neighbors(session_context['uuid'])
        neighbors.append(session_context['uuid'])

        try:
            response = session.query(rwObjects.Reference). \
                filter(rwObjects.or_(rwObjects.Reference.source_uuid == leaf.uuid, \
                                     rwObjects.Reference.target_uuid == leaf.uuid)). \
                order_by(rwObjects.desc(rwObjects.Reference.timestamp)).all()
        except Exception as e:
            raise (e)
        else:
            pass
        for line in response:
            source = rwObjects.get_by_uuid(line.source_uuid)[0]
            target = rwObjects.get_by_uuid(line.target_uuid)[0]
            if line.link == 0 and source.uuid == category_uuid:
                nodes.append(target)
            elif line.link == 0 and target.uuid == category_uuid:
                nodes.append(source)

        #print nodes

        auto_cats = dict()
        for node in nodes:
            auto_cats[node.uuid] = rwObjects.get_classification_results(session, node.uuid)
            # print "Автоклассификация : %s" % auto_cats[node.uuid]

        return tmpl.render(obj=leaf, session=session, name=leaf.name,
                           nodes=nodes, session_context=session_context,
                           auto_cats=auto_cats, cats_name=rwObjects.get_ktree_custom(session),
                           neighbors=neighbors)


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
            print "Показываем объект : ", vpath
            return ShowObject()
        elif len(vpath) == 2 and vpath[1] == 'edit':
            cherrypy.request.params['uuid'] = vpath[0]
            print "Редактируем объект : ", vpath
            return EditObject()
        elif len(vpath) == 2 and vpath[1] == 'save':
            print "Сохраняем объект : ", vpath
            cherrypy.request.params['uuid'] = vpath[0]
            return SaveObject()
        elif len(vpath) == 2 and vpath[1] == 'addlink':
            cherrypy.request.params['uuid'] = vpath[0]
            print "Связываем объект : ", vpath
            return LinkObject()
        elif len(vpath) == 2 and vpath[1] == 'savelink':
            cherrypy.request.params['object_uuid'] = vpath[0]
            print "Сохраняем связь..."
            return LinkObject()

        elif len(vpath) == 0:
            print "Вывод переадресации : ", vpath
            return self

        return vpath

    @cherrypy.expose
    def index(self):

        print "Переадресация на : / "
        # print cherrypy.request.__dict__
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


class AccessGraph(object):
    """
    Граф для определения прав доступа к объектам.
    """

    def __init__(self):
        session = rwObjects.Session()
        response = session.query(rwObjects.Reference).all()

        G = nx.Graph()
        labels = {}
        for line in response:
            s_obj = rwObjects.get_by_uuid(line.source_uuid)[0]
            t_obj = rwObjects.get_by_uuid(line.target_uuid)[0]
            G.add_node(str(line.source_uuid), obj=s_obj)
            G.add_node(str(line.target_uuid), obj=t_obj)
            G.add_edge(str(line.source_uuid), str(line.target_uuid), weight=int(line.link), timestamp=line.timestamp)
            print G.node[str(line.source_uuid)]

        self.graph = G
        session.close()

    def reload(self):
        """
        Функция перезагружает граф из базы.

        :return:
        """

        self.__init__()

    def neighbors(self,uuid=None):

        if uuid:
            return self.graph.neighbors(uuid)+[uuid]
        else:
            return None

G = AccessGraph()


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
    account = Account()

    @cherrypy.expose
    @require(member_of("users"))
    def index(self):
        tmpl = lookup.get_template("dashboard.html")
        c = get_session_context(cherrypy.request.login)
        params = cherrypy.request.headers
        rwQueue.msg_delivery_for_user.delay(str(c['uuid']))
        return tmpl.render(params=params, session_context=c, G=G)

    @cherrypy.expose
    @require(member_of("admin"))
    def autoclassify_all_notlinked_objects(self):

        rwLearn.autoclassify_all_notlinked_objects()

        raise cherrypy.HTTPRedirect("/settings?menu=ktree")

    @cherrypy.expose
    @require(member_of("users"))
    def graph(self, link):
        tmpl = lookup.get_template("graph.html")
        c = get_session_context(cherrypy.request.login)
        params = cherrypy.request.headers
        session = rwObjects.Session()
        response = session.query(rwObjects.Reference).filter(rwObjects.Reference.link == int(link)).all()

        G = nx.Graph()
        labels = {}
        for line in response:
            G.add_node(str(line.source_uuid), obj=line.source_type)
            G.add_node(str(line.target_uuid), obj=line.target_type)
            G.add_edge(str(line.source_uuid), str(line.target_uuid), comment=link)

        for node in G.nodes():
            obj = rwObjects.get_by_uuid(node)[0]
            labels[node] = obj.NAME

        pos = nx.spring_layout(G)
        plt.figure(1, figsize=(10, 10))
        nx.draw_networkx_nodes(G, pos)
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=7)
        nx.draw_networkx_edges(G, pos)
        plt.savefig("static/img/draw.png")
        plt.close()

        return tmpl.render(params=params, session_context=c)

    @cherrypy.expose
    @require(member_of("users"))
    def settings(self, menu=None):
        session_context = cherrypy.session.get('session_context')
        if not menu or menu == "":
            tmpl = lookup.get_template("settings_dashboard.html")
            session_context['back_ref'] = '/'
            session_context['menu'] = "settings"
            params = cherrypy.request.headers
            cherrypy.session['session_context'] = session_context
            return tmpl.render(params=params, session_context=session_context)

        elif menu == 'company':
            tmpl = lookup.get_template("settings_dashboard.html")
            session_context['back_ref'] = '/settings'
            session_context['menu'] = "company"

        elif menu == 'employee' or menu == 'accounts':
            tmpl = lookup.get_template("employee.html")
            session = rwObjects.Session()

            # если пользователь с правами администратора, выбираем всех сотрудников
            if 'admin' in session_context['groups']:
                users = session.query(rwObjects.Employee). \
                    filter_by(comp_id=session_context['comp_id']).all()
                obj_keys = users[0].get_attrs()
                f = users[0].get_fields()
                session_context['back_ref'] = '/settings'
                session_context['menu'] = "employee"

            # если пользователь с обычными правами, только свой профиль
            else:
                users = [rwObjects.get_by_uuid(session_context['uuid'])[0]]
                obj_keys = users[0].get_attrs()
                f = users[0].get_fields()
                session_context['back_ref'] = '/settings'
                session_context['menu'] = "accounts"

            linked_objects = dict()
            for user in users:
                refs = session.query(rwObjects.Reference). \
                    filter(rwObjects.sqlalchemy.and_(rwObjects.Reference.source_uuid == user.uuid,
                                                     rwObjects.Reference.target_type == "accounts",
                                                     rwObjects.Reference.link == 0)).all()
                linked_objects[user.uuid] = []

                for ref in refs:
                    linked_objects[user.uuid].append(rwObjects.get_by_uuid(ref.target_uuid)[0])

            session.close()
            cherrypy.session['session_context'] = session_context
            return tmpl.render(obj=users, keys=obj_keys, session_context=session_context,
                               view_f=f[1], all_f=f[0], linked=linked_objects)

        elif menu == 'clients':
            tmpl = lookup.get_template("settings_dashboard.html")
            session_context['back_ref'] = '/settings?menu=clients'

        elif menu == 'ktree':
            tmpl = lookup.get_template("ktree_settings.html")
            session = rwObjects.Session()
            tree = rwObjects.KnowledgeTree()
            session_context['back_ref'] = '/settings?menu=ktree'
            session_context['menu'] = "ktree_settings"
            return tmpl.render(obj=tree, session=session,
                               session_context=session_context)
        else:
            print "меню без указания."
            tmpl = lookup.get_template("settings_dashboard.html")
            session_context['back_ref'] = '/settings'
            session_context['menu'] = "settings"
            params = cherrypy.request.headers
            return tmpl.render(params=params, session_context=session_context)

    @cherrypy.expose
    @require(member_of("users"))
    def help(self, menu=None):
        raise cherrypy.HTTPRedirect("/")

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
    # print "user login : %s" % login
    user = rwObjects.get_employee_by_login(login)
    # print "user attrs: %s" % user.get_attrs()
    for key in user.get_attrs():
        context[key] = user.__dict__[key]

    context['company'] = rwObjects.get_company_by_id(user.comp_id).name
    context['company_uuid'] = rwObjects.get_company_by_id(user.comp_id).uuid
    context['company_prefix'] = rwObjects.get_company_by_id(user.comp_id).prefix
    context['groups'] = list()
    context['back_ref'] = "/"
    context['menu'] = "main"
    context['username'] = context['login'].split("@", 1)[0]
    context['groups'] = user.access_groups

    cherrypy.session['session_context'] = context

    return context


cherrypy.config.update("server.config")
cherrypy.config.update({
    'tools.gzip.on': True,
    'tools.sessions.on': True,
    'tools.auth.on': True
})

if __name__ == '__main__':
    cherrypy.quickstart(Root(), '/', "app.config")

