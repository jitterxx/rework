# -*- coding: utf-8 -*-
"""
Created on Fri May 22 18:49:46 2015

@author: sergey
"""
import datetime
import email_module as get_email
from email.utils import parseaddr
import uuid
import json
import pymorphy2

debug = True

class Subject:
    def __init__(self,name,desc):
        self.id = str(uuid.uuid1())
        self.type = ''
        self.references = []
        self.name = name
        self.desc = desc
        self.emails = []
        self.phones = []

class Object_email:
    u"""
        Класс объектов типа email.\n
        Набор аттрибутов:\n
        self.category - *Категория сообщения. Используется для реализации логики и 
        автоматического распознавания.\n
        Формат: словарь = ['название': вероятность,...]\n
        Если вероятность =1, значит указано вручную, можно использовать
        для обучения.*\n

        Методы:\n
    """
    def __init__(self):
        self.id = str(uuid.uuid1())
        self.type = 'email'
        self.references = []        
        self.desc = ''
        self.action_fw = [u'отправить']
        self.action_re = [u'получить']

        self.from_field = ''
        self.to_field = ''
        self.subject_field = ''        
        self.text = ''
        self.msg_id = ''
        u"""
        """
        self.category = {}
        
        
    
    def create(self,msg):
        self.from_field = unicode(msg['from'].lower())
        self.to_field = unicode(msg['to'].lower())
        self.date = msg['date']
        self.msg_id = msg['message-id']
        self.subject_field = unicode(msg['subject'])
        self.text = unicode(msg['text'])
        
        #Вносим в список объектов        
        objects[self.id] = self
        
        

class Line_event:       
    def __init__(self,subj,obj,targ):
        self.id = uuid.uuid1()
        self.datetime = datetime.datetime.now()
        self.subject = subj
        self.object = obj
        self.target = targ
        self.action_fw = False
        self.action_re = False
    

subjects = {}
newsubj = Subject('Сергей','разработчик')
newsubj.emails.append('sergey@reshim.com')
newsubj.type = 'employee'
subjects[newsubj.id] = newsubj

newsubj = Subject('Вера','директор')
newsubj.emails.append('ve.zhukova@gmail.com')
newsubj.type = 'employee'
subjects[newsubj.id] = newsubj

objects = {}

#Словарь для облегчения доступа к событиям
timeline = {}


def create_emails_objects(date):
    u"""
    Выделяем все поля из сообщения.
    Создаем объекты типа email и записываем доступные аттрибуты
    """
    emails = get_email.get_emails_google(date)
    for i in emails.keys():
        email = {}
        #Пишем все ключи в lowcase
        for j in emails[i].keys():
            low_key = str(j).lower()
            email[low_key] = emails[i][j]
           
        #Создаем объект        
        e = Object_email()
        e.create(email)
        

def check_subjects_for_email(message):
    u"""
    Проверка, относиться ли сообщение к одному из уже известных субъектов.
    Происходит по полям FROM, TO и свойства emails субъектов.
    1. Если ДА, то происходит привязка к субъекту и
        создаеться событие на оси времени
    2. Если НЕТ, то создаеться субъект типа contact. Событие на ось времени
        помещаеться, т.к. имеет отношения к нам.
    Тип субъекта - будет использоваться в дальнейшем для автоматического
        распознавания новых писем и отнесению их к типу. Вопрос на этой 
        стадии будет задаваться в форме - ДА/НЕТ.
    """
       
    ff = parseaddr(message.from_field)
    tf = parseaddr(message.to_field)
    message.from_field = ff[1]
    message.to_field = tf[1]
    from_name = ff[0]
    to_name = tf[0]

    #Проверка поля FROM и известных субъектов
    for subj in subjects.keys():
        #print(message.from_field, type(message.from_field))
        #print(subj.emails, type(subj.emails))
        #print(message.from_field in subj.emails)
        
        if message.from_field in subjects[subj].emails:
            print("Адрес " + message.from_field +" принадлежит " + subjects[subj].name)
            from_id = subjects[subj].id
            check_from = True

            for subj1 in subjects.keys():
                #ищем поле TO в известных субъектах
                if message.to_field in subjects[subj1].emails:
                    to_id = subjects[subj1].id
                    break
            else:
                #В поле TO совпадений не найдено, создаем субъект типа contact
                newsubj = Subject(to_name,'TO: FROM -> TO')
                newsubj.type = 'contact'
                newsubj.emails.append(message.to_field)
                subjects[newsubj.id] = newsubj
                to_id = newsubj.id
                print "Добавлен новый контакт."
            
            #Можно создавать событие на оси
            #Создаем событие на оси времени
            event = Line_event(from_id,message.id,to_id)                
            event.action_fw = True
            timeline[event.id] = event
            print "Добавлено новое событие."
            #делаем выход, т.к. отправитель и получатель один
            break
                

            
                    
    else:
        #Если выход завершился нормально, значит совпадений в поле From
        #не найдено. Добвляем новый субъект типа contact
        check_from = False
        #записываем адрес в субъект типа Контакт
        newsubj = Subject(from_name,'FROM: FROM -> TO')
        newsubj.type = 'contact'
        newsubj.emails.append(message.from_field)
        subjects[newsubj.id] = newsubj
        from_id = newsubj.id
        print "Добавлен новый контакт."


        #Проверка поля TO и известных субъектов
        for subj in subjects.keys():
            #print(message.from_field, type(message.from_field))
            #print(subj.emails, type(subj.emails))
            #print(message.from_field in subj.emails)
            
            if message.to_field in subjects[subj].emails:
                print("Адрес " + message.to_field +" принадлежит " + subjects[subj].name)
                to_id = subjects[subj].id
                check_to = True

                #Можно создавать событие на оси
                #Создаем событие на оси времени
                event = Line_event(from_id,message.id,to_id)                
                event.action_re = True
                timeline[event.id] = event
                print "Добавлено новое событие."
                #делаем выход, т.к. отправитель и получатель один
                break
    
        else:
            #В поле TO совпадений не найдено, создаем субъект типа contact
            newsubj = Subject(to_name,'TO: TO -> FROM')
            newsubj.type = 'contact'
            newsubj.emails.append(message.to_field)
            subjects[newsubj.id] = newsubj
            to_id = newsubj.id
            print "Добавлен новый контакт."
                
    
def parse_emails_objects():
    u"""
    Обрабатываем объекты типа email
    Ищем новые контакты, связываем с существующими субъектами
    """
    for i in objects.keys():
        check_subjects_for_email(objects[i])
              

def show_objects():
    print "\n********************** Объекты ***********************\n"
    for i in objects.keys():
        j = objects[i].__dict__
        for k in j.keys():
            if not k == 'text':
                print(str(k) + ' : ' + str(j[k]))

        print "--------------------Next---------------------- \n"

def show_subjects():
    print "\n******************* Люди и Контакты ***********************\n"
    for i in subjects.keys():
        j = subjects[i].__dict__
        for k in j.keys():
            print(str(k) + ' : ' + str(j[k]))
        
        #json.dump(j, open("subjects.json",'a'))
        print "------------------------------------------ \n"


def show_timeline():
    u"""
    1. Кто? Имя, адрес субъекта инициатора.
    2. Что сделал? Действие. Глагол объекта
    3. С чем? Объект действия. Тип, тема сообщения.
    4. Кому? Имя, адрес субъекта адресата действия.
    """ 
    print "\n****************** События *********************\n"
    morth = pymorphy2.MorphAnalyzer()
    for i in timeline.keys():
        p = timeline[i]
        print subjects[p.subject].name, subjects[p.subject].emails
        m = morth.parse(unicode(subjects[p.subject].name))[0]
        if 'masc' in m.tag:
            print morth.parse(unicode(objects[p.object].action_fw[0]))[0].inflect({'masc'}).word
        elif m.tag.gender == 'femn':
            print morth.parse(unicode(objects[p.object].action_fw[0]))[0].inflect({'femn'}).word
        else:
            print objects[p.object].action_fw[0]
        print objects[p.object].type
        print subjects[p.target].name,subjects[p.target].emails
        print "------------------------------------------ \n"
        #morth.parse()




