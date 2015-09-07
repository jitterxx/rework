# -*- coding: utf-8 -*-


"""

"""

import sys

reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.append('../modules')

import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_queue_module as rwQueue
import prototype1_type_classifiers as rwLearn
import prototype1_email_module as rwEmail
import cherrypy
from bs4 import BeautifulSoup
from auth import AuthController, require, member_of, name_is, all_of, any_of
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
            return ShowError("EditObject. Операция rwObjects.get_by_uuid(uuid)[0]. Ошибка : %s" % str(e))
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
            print e
            return ShowError(str(e))
        else:
            obj_keys = obj.get_attrs()
            f = obj.get_fields()
            session_context = cherrypy.session.get('session_context')
            neighbors = G.neighbors(session_context['uuid'])

            # Ищем подходящие для этого ДО кейсы, считаем расстояние и выбираем только подходящие
            cases = dict()
            nbrs = list()

            if obj.__tablename__ == 'dynamic_object':
                obj.clear_text()
                nbr = list()
                try:
                    nbr = rwLearn.predict_neighbors(rwObjects.default_neighbors_classifier,\
                                                                        [obj.__dict__['text_clear']])
                except ValueError as e:
                    print "Недостаточно кейсов для тренировки. Ошибка: %s" % str(e)
                    session_context['message_to_user'] = "Поиск подходящих кейсов невозможен. Необходимо создать 3  " \
                                                         "или больше кейсов."
                    cherrypy.session['session_context'] = session_context
                except Exception as e:
                    print "Ошибка получения сосдей поиске кейсов. Ошибка: %s " % str(e)

                print "nbrs : %s" % nbr
                for i in nbr:
                    case = rwObjects.get_by_uuid(i[0])[0]
                    print "Кейс : %s (расстояние %s)" % (case.subject,i[1])
                    if i[1] < 0.9998:
                        cases[i[0]] = case
                        nbrs.append(i)

            # Является ли текущий пользователь экспертом для одного из узлов НЗ, к которому относиться объект
            # если являеться, то можно предоставить доступ
            show_object = False
            session = rwObjects.Session()
            leafs = rwObjects.get_ktree_for_object(session, obj.uuid)[0]
            session.close()
            for leaf in leafs.values():
                if session_context['login'] == leaf.expert:
                    show_object = True

            # Создаем список связанных объектов для показа
            linked_nodes = dict()
            for i in G.neighbors(obj.uuid):
                if i != obj.uuid:
                    try:
                        lo = rwObjects.get_by_uuid(i)[0]
                    except Exception as e:
                        return ShowError("Showbject. Операция : linked_nodes[i] = rwObjects.get_by_uuid(i)[0]. Ошибка :"
                                         "%s" % str(e))
                    try:
                        linked_nodes[lo.__tablename__]
                    except KeyError:
                        linked_nodes[lo.__tablename__] = dict()
                    linked_nodes[lo.__tablename__][lo.uuid] = lo

            print "Объект для вывода связей : %s" % obj.uuid
            print "linked_nodes : %s" % linked_nodes

            print "session_context['menu'] : %s " % session_context['menu']

            if session_context['menu'] in ['accounts', 'employee']:
                session_context['back_ref'] = "/settings/?menu=" + session_context['menu']
            if session_context['menu'] == 'settings':
                session_context['back_ref'] = "/settings"

            session_context['menu'] = "show_object"
            return tmpl.render(obj=obj, keys=obj_keys,
                               session_context=session_context, all_f=f[0], view_f=f[1],
                               neighbors=neighbors, cases=cases, nbrs=nbrs, show_object=show_object,
                               linked_nodes=linked_nodes)

    @cherrypy.expose
    def frame(self, uuid):
        print "Отдаем данные во фрейм..."
        try:
            obj = rwObjects.get_by_uuid(uuid)[0]
        except Exception as e:
            print e
            return ShowError(str(e))
        else:
            pass
        if obj.__tablename__ == 'dynamic_object' and obj.__dict__['raw_text_html']:
            return obj.__dict__['raw_text_html']
        else:
            return ShowError("Frame не может быть вызван для других объектов.")


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
            raise cherrypy.HTTPRedirect(url)


class LinkObject(object):
    def __init__(self):
        pass

    @cherrypy.expose
    def addlink(self, uuid):
        data = cherrypy.request.params
        session = rwObjects.Session()
        tmpl = lookup.get_template("add_link_to_ktree.html")

        try:
            obj = rwObjects.get_by_uuid(uuid)[0]
            custom = rwObjects.get_ktree_custom(session)
        except Exception as e:
            return ShowError("""LinkObject.addlink. Операция rwObjects.get_by_uuid() или
                                rwObjects.get_by_uuid(uuid)[0]. Ошибка : %s""" % str(e))
        print custom.values()
        used_category = rwObjects.get_ktree_for_object(session, uuid)[0]

        session.close()
        return tmpl.render(obj=obj, category=custom,
                           session_context=cherrypy.session.get('session_context'),
                           used_category=used_category)

    @cherrypy.expose
    def savelink(self, object_uuid, object_type, category_type=None, category_uuid=None):
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

        old_edges = rwObjects.get_ktree_for_object(session, object_uuid)[0]
        edges_for_delete = list()

        # Ищем связи которые надо удалить
        for old in old_edges.values():
            if old.uuid not in category_uuid:
                edges_for_delete.append(old.uuid)

        # Производим связывание объекта с категориями
        for category in category_uuid:
            # Устанавливаем новые связи
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

        # Получаем список старых связей
        try:
            resp = session.query(rwObjects.Reference).filter(rwObjects.and_(\
                rwObjects.Reference.source_type == 'knowledge_tree',
                rwObjects.Reference.source_uuid.in_(edges_for_delete),
                rwObjects.Reference.target_uuid == object_uuid,
                rwObjects.Reference.link == 0)).all()
        except Exception as e:
            print str(e)
            return ShowError("Ошибка : %s" % str(e))
        # Удаляем старые связи
        try:
            for one in resp:
                session.delete(one)
            session.commit()
        except Exception as e:
            print str(e)
            return ShowError("Ошибка : %s" % str(e))

        try:
            st = rwLearn.clear_autoclassify(session, object_uuid)
        except Exception as e:
            print "Проблемы удаления автоклассфиикации.."
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
                           access_groups=obj.ACCESS_GROUPS)

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

        print v

        tmpl = lookup.get_template("timeline.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/timeline'
        session_context['menu'] = 'timeline'
        cherrypy.session['session_context'] = session_context
        session = rwObjects.Session()
        try:
            events = session.query(rwObjects.Reference).filter(rwObjects.Reference.link == link). \
                order_by(rwObjects.desc(rwObjects.Reference.timestamp)).all()
            obj_keys = events[0].get_attrs()
            fields = events[0].get_fields()
        except IndexError:
            obj_keys = rwObjects.rw_parent().get_attrs()
            fields = rwObjects.rw_parent().get_fields()
        except Exception as e:
            return ShowError(str(e))

        actors = {}
        neighbors = G.neighbors(session_context['uuid'])

        for event in events:
            event.read(session)
            # print "Source UUID : %s" % event.source_uuid
            # print "Target UUID : %s" % event.target_uuid
            try:
                obj = rwObjects.get_by_uuid(event.source_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                return ShowError(str(e))
            else:
                if event.source_uuid not in actors.keys():
                    actors[event.source_uuid] = obj
                    print "Actor: %s" % actors[event.source_uuid].SHORT_VIEW_FIELDS

            try:
                obj = rwObjects.get_by_uuid(event.target_uuid)[0]
            except Exception as e:
                print e[0]
                print e[1]
                return ShowError(str(e))
            else:
                if event.target_uuid not in actors.keys():
                    actors[event.target_uuid] = obj
                    print "Actor: %s" % actors[event.target_uuid].SHORT_VIEW_FIELDS

                    # print "events[0].get_fields() : %s" % fields
                    # print "obj_keys : %s " % obj_keys
        print "All actors: %s" % actors.keys()
        print "Соседи: %s" % neighbors
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
        G.reload()
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
        experts = rwObjects.get_userlist_in_group(session, 'expert')

        return tmpl.render(obj=obj, keys=obj_keys, name="раздел Навигатора Знаний",
                           session_context=session_context,
                           all_f=f[0], create_f=f[3],
                           experts=experts[1])

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
            params['action'] = data['action']
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
        url = session_context['back_ref']

        print "Данные из запроса : "
        print data
        print "\nКонтекст :"
        print session_context
        print "Переадресация на show_object... ", url

        session = rwObjects.Session()
        try:
            rwObjects.KnowledgeTree.ktree_return_childs(session, data['parent_id'])
        except Exception as e:
            return ShowError("""Ktree.create_new. Операция: rwObjects.KnowledgeTree.ktree_return_childs(session,
            data['parent_id']). Ошибка : %s""" % str(e))
        else:
            pass

        source = rwObjects.get_by_uuid(session_context['uuid'])[0]

        """
        Создаем новый объект класса KnowledgeTree
        Для каждого нового типа необходимо добавить в  create_new_object условия.
        Проверка параметров происходит там же, если чего-то не хватает то ловим Exception.
        """

        try:
            status, obj = rwObjects.create_new_object(session, "knowledge_tree", data, source)
        except Exception as e:
            return ShowError("""Ktree.create_new. Операция: rwObjects.create_new_object(session, 'knowledge_tree',
                             params, source). Ошибка : %s""" % str(e))
        else:
            print status

        session.close()
        raise cherrypy.HTTPRedirect(url)

    @cherrypy.expose
    def classify(self):

        s = rwLearn.check_conditions_for_classify()
        if s[0]:
            session = rwObjects.Session()
            status = rwLearn.retrain_classifier(session, rwObjects.default_classifier)
            print status[0]
            print status[1]
            session.close()
        else:
            return ShowError(s[1])

        session_context = cherrypy.session.get('session_context')

        raise cherrypy.HTTPRedirect(session_context['back_ref'])


class ShowKTreeCategory(object):
    @cherrypy.expose
    def index(self, category_uuid):

        tmpl = lookup.get_template("ktree_show_category.html")
        session_context = cherrypy.session.get('session_context')
        session_context['back_ref'] = '/ktree'
        session_context['menu'] = 'ktree_category'
        if session_context['menu'] == 'ktree_category':
            #session_context['back_ref'] = '/ktree/' + str(category_uuid)
            session_context['menu'] = 'ktree_category'

        if session_context['menu'] == 'ktree_settings':
            session_context['back_ref'] = '/settings?menu=ktree'
            session_context['menu'] = 'ktree_settings'

        cherrypy.session['session_context'] = session_context

        # print category_uuid

        session = rwObjects.Session()
        leaf = rwObjects.get_by_uuid(category_uuid)[0]

        # Получаем все связанные объекты для этого пользователя
        neighbors = G.neighbors(session_context['uuid'])
        neighbors.append(session_context['uuid'])

        # Получаем все объекты связанные с этим узлом НЗ
        try:
            response = session.query(rwObjects.Reference). \
                filter(rwObjects.or_(rwObjects.Reference.source_uuid == leaf.uuid, \
                                     rwObjects.Reference.target_uuid == leaf.uuid)). \
                order_by(rwObjects.desc(rwObjects.Reference.timestamp)).all()
        except Exception as e:
            raise e
        else:
            pass
        nodes = list()
        for line in response:
            source = rwObjects.get_by_uuid(line.source_uuid)[0]
            target = rwObjects.get_by_uuid(line.target_uuid)[0]
            if line.link == 0 and source.uuid == category_uuid:
                nodes.append(target)
            elif line.link == 0 and target.uuid == category_uuid:
                nodes.append(source)

        # Получаем результаты автоклассификации для объектов в этом узле НЗ
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
        elif len(vpath) == 2 and vpath[1] == 'frame':
            cherrypy.request.params['uuid'] = vpath[0]
            print "Выводим данные объекта во фрейм : ", vpath
            return ShowObject()
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


G = rwObjects.AccessGraph()


class Case(object):
    """

    """
    _cp_config = {
        'auth.require': [member_of('users')]
    }

    def _cp_dispatch(self, vpath):
        """
        Обработка REST URL
        """

        if len(vpath) == 1 and vpath[1] == 'add':
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
        elif len(vpath) == 2 and vpath[1] == 'use':
            cherrypy.request.params['case_uuid'] = vpath[0]
            print "Используем кейс..."
            return self
        elif len(vpath) == 0:
            print "Вывод переадресации : ", vpath
            return self

        return vpath

    @cherrypy.expose
    def add(self, uuid):

        tmpl = lookup.get_template("add_case.html")
        session_context = cherrypy.session.get('session_context')
        session = rwObjects.Session()
        try:
            do_object = rwObjects.get_by_uuid(uuid)[0]
        except Exception as e:
            return ShowError(str(e))
        else:
            pass

        obj = rwObjects.Case()
        obj_keys = obj.get_attrs()
        f = obj.get_fields()
        session.close()
        return tmpl.render(obj=obj, keys=obj_keys, name=obj.NAME,
                           session_context=session_context,
                           all_f=f[0], create_f=f[3],
                           do_object=do_object)

    @cherrypy.expose
    def use(self,case_uuid, for_uuid):
        tmpl = lookup.get_template("use_case.html")
        session_context = cherrypy.session.get('session_context')
        session = rwObjects.Session()
        # Получаем объекты
        try:
            obj = rwObjects.get_by_uuid(for_uuid)[0]
            case = rwObjects.get_by_uuid(case_uuid)[0]
        except Exception as e:
            return ShowError(str(e))
        else:
            pass

        accounts = dict()
        obj_nbrs = G.neighbors(for_uuid)
        user_nbrs = G.neighbors(session_context['uuid'])
        # Создаем список аккаунтов пользователя через которые можно отправить ответ
        for i in user_nbrs:
            node = G.graph.node[i]['obj']
            if node.__class__.__name__ == 'Account':
                print "Аккаунт объекта: %s" % node.login
                accounts[node.uuid] = node
        # Получаем аккаунт объекта через который можно отправить ответ
        for i in obj_nbrs:
            node = G.graph.node[i]['obj']
            if node.__class__.__name__ == 'Account':
                print "Аккаунт пользователя: %s" % node.login
                obj_account = node

        soup = BeautifulSoup(obj.__dict__['raw_text_html'], from_encoding="utf8")
        body_old = str(soup.find('body').contents[0])

        session.close()
        return tmpl.render(obj=obj, case=case, session_context=session_context, body_old=body_old,
                           accounts=accounts, obj_account=obj_account)

    @cherrypy.expose
    def send(self, **kwargs):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        print "Данные запроса:"
        for key in data.keys():
            print "%s : %s" % (key,data[key])
        # Передаем данные в функцию обрабатывающую отправку сообщений
        try:
            status = rwEmail.outgoing_message(data)
        except Exception as e:
            print "Case.send. Операция: rwEmail.outgoing_message(data). Ошибка: %s" % str(e)
            return ShowError(str(e))

        print status
        if not status[0]:
            print status[0]
            print status[1]
            return ShowError(str(status[0])+status[1])

        raise cherrypy.HTTPRedirect("/object/%s" % data['obj_uuid'])



    @cherrypy.expose
    def create_new(self, **kwargs):
        data = cherrypy.request.params
        session_context = cherrypy.session.get('session_context')
        url = session_context['back_ref']
        print "Данные запроса: %s" % data

        session = rwObjects.Session()
        # Получаем по uuid создателя кейса
        try:
            source = rwObjects.get_by_uuid(session_context['uuid'])[0]
        except Exception as e:
            return ShowError("""Case.create_new. Операция: rwObjects.get_by_uuid(). Ошибка : %s""" % str(e))
        else:
            pass

        # Создаем новый Case и проводим тренировку классификатора расстояний
        try:
            status, obj = rwObjects.create_new_object(session, "cases", data, source)
        except Exception as e:
            return ShowError("""Ktree.create_new. Операция: rwObjects.create_new_object(session, 'knowledge_tree',
                             params, source). Ошибка : %s""" % str(e))
        else:
            uuid = str(obj.uuid)
            rwLearn.train_neighbors(session, rwObjects.default_neighbors_classifier)
            print status

        # Линкуем новый Case с объектом из которого он был создан
        try:
            status = rwObjects.link_objects(session,obj.uuid,data['do_object_uuid'])
        except Exception as e:
            return ShowError("""Case.create_new. Операция: rwObjects.link_objects(session,obj.uuid,
                    data['do_object_uuid']). Ошибка : %s""" % str(e))
        else:
            print status[0]
            print status[1]
            if not status[0]:
                return ShowError(str(status[0]) + status[1])

        # Линкуем новый Case с узлами Навигатора Знаний коорые были в связаны с объектм родителем
        do_obj = rwObjects.get_by_uuid(data['do_object_uuid'])[0]
        print do_obj.NAME
        print do_obj.__dict__['custom_category']
        for cat in do_obj.__dict__['custom_category']:
            print cat.name
            try:
                status = rwObjects.link_objects(session,cat.uuid,obj.uuid)
            except Exception as e:
                return ShowError("""Case.create_new. Операция: rwObjects.link_objects(session,obj.uuid,cat).
                            Ошибка : %s""" % str(e))
            else:
                print status[0]
                print status[1]
                if not status[0]:
                    return ShowError(str(status[0]) + status[1])

        session.close()
        G.reload()
        raise cherrypy.HTTPRedirect("/object/%s/addlink" % uuid)

    @cherrypy.expose
    @require(any_of(member_of("admin"),member_of("expert")))
    def train(self):
        session_context = cherrypy.session.get('session_context')
        try:
            rwLearn.train_neighbors(None, rwObjects.default_neighbors_classifier)
        except Exception as e:
            return ShowError("Обновить классификацию кейсов нельзя. " + str(e))

        raise cherrypy.HTTPRedirect("/settings?menu=ktree")


class Root(object):

    auth = AuthController()
    restricted = RestrictedArea()

    object = Any_object()
    employee = Employee()
    timeline = Timeline()
    clients = Clients()
    ktree = KTree()
    account = Account()
    cases = Case()

    @cherrypy.expose
    @require(member_of("users"))
    def index(self):
        tmpl = lookup.get_template("dashboard.html")
        c = get_session_context(cherrypy.request.login)
        params = cherrypy.request.headers
        rwQueue.msg_delivery_for_user.delay(str(c['uuid']))
        G.reload()
        return tmpl.render(params=params, session_context=c, G=G)

    @cherrypy.expose
    @require(member_of("admin"))
    def autoclassify_all_notlinked_objects(self):

        try:
            rwLearn.autoclassify_all_notlinked_objects()
        except Exception as e:
            return ShowError("Обновить автоклассификацию нельзя. " + str(e))
        else:
            pass

        raise cherrypy.HTTPRedirect("/settings?menu=ktree")

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
        tmpl = lookup.get_template("help.html")
        session_context = cherrypy.session.get('session_context')
        return tmpl.render(session_context=session_context)

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
    context['message_to_user'] = ""

    cherrypy.session['session_context'] = context

    return context

cherrypy.config.update("server.config")

if __name__ == '__main__':
    cherrypy.quickstart(Root(), '/', "app.config")

