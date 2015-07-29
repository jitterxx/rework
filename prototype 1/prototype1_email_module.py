# -*- coding: utf-8 -*-
"""
Created on Mon May 25 16:01:48 2015

@author: sergey

Модуль содержит все функции необходимые для получения и записи
Messages типа email.

"""

#!/usr/bin/python -t
# coding: utf8

import imaplib
import email
import pandas as pd
from bs4 import BeautifulSoup
import chardet
import prototype1_objects_and_orm_mappings as rwObjects
import datetime
import json



import sys
reload(sys)
sys.setdefaultencoding("utf-8")


debug = False

def get_text(data):
    #Извлекаем из html сообщения только текст
    soup = BeautifulSoup(data,from_encoding="utf8")

    # Содержимое ссылок заменяем на LINK
    tag = soup.new_tag(soup,"b")
    tag.string = 'LINK'
    for link in soup.find_all('a'):
        link.replaceWith(tag)
    for link in soup.find_all('script'):
        link.replaceWith(tag)
    for link in soup.find_all(''):
        link.replaceWith(tag)
    
    text = soup.get_text()
    text = strip_text(text)
    
    return text

def strip_text(data):
    #Delete spec \t\n\r\f\v
    #text = re.sub(u'[\r|\n|\t]+',u' ',data,re.I|re.U|re.M)
    
    #Multiple spaces in one
    #text = re.sub(r'\s{2:}',r' ',data,re.I|re.U|re.M)
    #text = re.sub(u'\s+',u' ', text,re.I|re.U|re.M)
    #text = data.replace('\\n',' ')
    #text = text.replace('\\t',' ')    
    text = data.replace('\\W',' ')
    
    text = ' '.join(text.split())
    
    return text


def get_emails(account_attr):

    server = account_attr.server
    port = account_attr.port
    login = account_attr.login
    password = account_attr.password
    date_after = account_attr.last_check.strftime("%d-%b-%Y")
    
    date_before = account_attr.last_check.strftime("%d-%b-%Y")
    dirs = json.loads(account_attr.dirs)
    status = ""    
    
    try:
        M = imaplib.IMAP4_SSL(server)
    except: 
        print 'Connection problem!', sys.exc_info()[0]
        status = 'ERROR.\n'
        raise
            
    
    print M.PROTOCOL_VERSION
    
    #password = raw_input('Password:')
    
    M.login(login,password)
    s = {}
    
    for cur_dir in dirs.keys():
        if debug:
            print M.select(dirs[cur_dir])
        
        M.select(dirs[cur_dir])
        
        #typ, data = M.search('UTF8','SINCE',date_after)
        #Запоминиаем какие письма были непрочитанными        
        typ, data = M.search(None,'(UNSEEN)','(SINCE "%s")' % (date_after))
        unseen_num = data[0].split()
        
        #Ищем все письма начиная с date_after
        typ, data = M.search(None,'(SINCE "%s")' % (date_after))
        
        for num in data[0].split():
            typ, data = M.fetch(num, '(RFC822)')
            
            if num in unseen_num:
                M.store(num, '-FLAGS', '\Seen')
        
            msg = email.message_from_string(data[0][1])
            
            
            msg_data = {}
            for n,m in msg.items():
                k = ''
        
                if debug:
                    print 'm',m
                    pass
                m = m.replace('?=<','?= <')
                m = strip_text(m)
                if debug:
                    print m
                    pass
                
                broken = False
                try:            
                    for h in email.header.decode_header(m):
                        
                        k = ' '.join((k,h[0]))            
                        if not (h[1] == None):            
                            #Делаем перекодировку в UTF8
                            k = k.decode(h[1]).encode('utf8')
                        else:
                            #Проверяем что строка корректно перекодирована
                            if not (chardet.detect(k)['encoding'] == 'UTF-8'):
                                k = k.decode(chardet.detect(k)['encoding']).encode('utf8')
                        
                    if n in msg_data.keys():
                        msg_data[n] = msg_data[n] + k
                    else:
                        msg_data[n] = k
                except:
                    broken = True
            
            if debug:
                print msg_data['From']
                pass
        
            
            msg_data['Text'] = ''
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        html = unicode(part.get_payload(decode=True),
                                       part.get_content_charset(),
                                       'replace').encode('utf8','replace')
                        msg_data['Text'] +=  get_text(html)
                    elif part.get_content_type() == "text/html":

                        if not part.get_content_charset():
                            part.set_charset("utf8")

                        html = unicode(part.get_payload(decode=True),
                                       part.get_content_charset(),
                                       'replace').encode('utf8','replace')
                        msg_data['Text'] +=  get_text(html)
        
            else:
                if msg.get_content_type() == "text/plain":
                    if debug:
                        print "msg.get_content_charset(): ",msg.get_content_charset()
                        print "msg.get_payload(decode=True) : ",msg.get_payload(decode=True)
                    
                    if not msg.get_content_charset():
                        msg.set_charset("utf8")
                    
                    html = unicode(msg.get_payload(decode=True),
                                   msg.get_content_charset(),
                                   'replace').encode('utf8','replace')
                    msg_data['Text'] +=  get_text(html)
                elif msg.get_content_type() == "text/html":
                    html = unicode(msg.get_payload(decode=True),
                                   msg.get_content_charset(),
                                   'replace').encode('utf8','replace')
                    msg_data['Text'] +=  get_text(html)
                if debug:
                    print 'HTML:',html
                    print 'TEXT:',msg_data['Text']       
            
            
            if broken and debug:
                print 'Broken encoding. Skip message.'
            else:
                #переводим все ключи в lowcase
                msg_low = dict((k.lower(), v) for k, v in msg_data.iteritems())
                s[num] = dict(zip(msg_low.keys(), msg_low.values()))

    
    M.close()
    M.logout()

    return s,status


def get_email_messages():
    
    accounts = []
    
    session = rwObjects.Session()
 
    try:
        query = session.query(rwObjects.Account)
    except rwObjects.sqlalchemy.orm.exc.NoResultFound:
        print 'No accounts.'        
    else:
        for each in query.all():
            accounts.append(each)
    finally:
        session.close()

    session = rwObjects.Session()        
    for account in accounts:
        status = ''
        emails = {}
    
        #Получем емайлы        
        if account.acc_type == 'email':
            print "Подключаюсь к " + str(account.login) + "..."
            try:
                emails,status = get_emails(account)
                #print type(emails)
                
            except RuntimeError:
                print 'Ошибка получения сообщений'
                status = 'Error.' + str (sys.exc_info())
            else:
                email_data = {}
                for email_data in emails.values():
                    #print type(email_data)
                    #print email_data['from']
                    #print email_data['to']
                    
                    
                    source = {'uuid':account.uuid,
                              'source_type':account.__tablename__,
                              'id':account.id} 
                    msg = rwObjects.Message()
                    msg_status = "OK"
                    
                    
                    if msg.is_exist_msg(session,email_data['message-id']):
                        print email_data['message-id']
                        print "Сообщение уже существует. Не добавляем."                    
                        print "----------------------------------------------"
                        
                    else:
                                                
                        msg_status = msg.create_email(session,source,
                                         email_data,email_data['message-id'])
                    
                    if msg_status[0][0] == 'OK':
                        print msg_status[0][1]
                        print msg_status[1][1]
                account.last_check = datetime.datetime.now()
                session.add(account)
                status = 'OK'
            finally:
                session.commit()
                session.close()
                
        else:
            #обработка других каналов
            pass
        
   
    return status

def test():
    print get_email_messages()

    

#rwObjects.create_tables()
#rwObjects.test()
test()
    
    
    