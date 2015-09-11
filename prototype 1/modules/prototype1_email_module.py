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
from bs4 import BeautifulSoup
import chardet
import datetime
import time
import json
import re
from smtplib import SMTP_SSL
import email
from prototype1_tools import *
import prototype1_objects_and_orm_mappings as rwObjects

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


debug = False


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


def get_emails(account):
    """

    :param account: Объект типа Account.
    :return: Список [messages,status]. Где messages - словарь с сообщениями в формате: messages[message_id] = {
    "Название поля в сообщении":"значение поля"}.
    """

    server = account.server
    port = account.port
    login = account.login
    password = account.password
    date_after = account.last_check.strftime("%d-%b-%Y")
    date_before = account.last_check.strftime("%d-%b-%Y")

    dirs = json.loads(account.dirs)
    status = ""    

    print account.last_check
    print date_after
    print date_before
    print dirs
    print dirs.keys()

    try:
        M = imaplib.IMAP4_SSL(server)
    except Exception as e:
        print 'Connection problem! %s' % str(e)
        status = 'ERROR.\n'
        raise Exception(e)
            
    if debug:
        print M.PROTOCOL_VERSION
    
    #password = raw_input('Password:')
    
    M.login(login,password)
    s = {}

    # Письма ищем только во Входящих и Отправленных
    for cur_dir in ['inbox','sent']:
        if debug:
            print "Проверяю папку: ",dirs[cur_dir]
            print M.select(dirs[cur_dir])
        
        M.select(dirs[cur_dir])
        
        # typ, data = M.search('UTF8','SINCE',date_after)
        # Запоминиаем какие письма были непрочитанными
        try:
            typ, data = M.search(None,'(UNSEEN)','(SINCE "%s")' % date_after)
        except Exception as e:
            raise Exception(str(date_after)+str(e))
        else:
            pass
        unseen_num = data[0].split()
        
        if debug:
            print "Ищем все письма начиная с %s " % date_after

        typ, data = M.search(None,'(SINCE "%s")' % (date_after))
        
        for num in data[0].split():
            typ, data = M.fetch(num, '(RFC822)')
            if debug:
                print "Найдено :",data

            if num in unseen_num:
                M.store(num, '-FLAGS', '\Seen')
        
            msg = email.message_from_string(data[0][1])

            msg_data = {}
            for n,m in msg.items():
                k = ''
        
                if debug:
                    print n,' : ',m
                    pass

                m = m.replace('?=<','?= <')
                m = strip_text(m)

                if debug:
                    print n,' : ',m
                    pass
                
                broken = False

                try:            
                    for h in email.Header.decode_header(m):
                        
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
                    if debug:
                        print "Ошибка кодировки в получении заголовков."
                        pass
                    broken = True
                else:
                    pass
                    #if n in ["From","To"]: print n,' : ',msg_data[n]
            
            if debug:
                print msg_data.keys()
                pass

            msg_data['text_plain'] = ''
            msg_data['raw_text_plain'] = ''
            msg_data['text_html'] = ''
            msg_data['raw_text_html'] = ''
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":

                        if not part.get_content_charset():
                            part.set_charset("utf8")
                        html = unicode(part.get_payload(decode=True),
                                       part.get_content_charset(),
                                       'replace').encode('utf8','replace')
                        msg_data['text_plain'] += html
                        msg_data['raw_text_plain'] += html
                    elif part.get_content_type() == "text/html":

                        if not part.get_content_charset():
                            part.set_charset("utf8")

                        html = unicode(part.get_payload(decode=True),
                                       part.get_content_charset(),
                                       'replace').encode('utf8','replace')
                        msg_data['text_html'] += html
                        msg_data['raw_text_html'] += html
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
                    msg_data['text_plain'] += html
                    msg_data['raw_text_plain'] += html
                elif msg.get_content_type() == "text/html":

                    if not msg.get_content_charset():
                        msg.set_charset("utf8")

                    html = unicode(msg.get_payload(decode=True),
                                   msg.get_content_charset(),
                                   'replace').encode('utf8','replace')
                    msg_data['text_html'] += html
                    msg_data['raw_text_html'] += html

                if debug:
                    print 'HTML:',msg_data['raw_text_html']
                    print 'TEXT:',msg_data['text_html']
            
            if broken and debug:
                print 'Broken encoding. Skip message.'
            else:
                # переводим все ключи в lowcase
                msg_low = dict((k.lower(), v) for k, v in msg_data.iteritems())

                """Очищаем поля from,to,message-id"""
                for k in msg_low.keys():
                    """
                    if k in ['to','from','cc','bcc']:
                        ea = extract_addresses(msg_low[k])
                        msg_low[k] = ea
                    """
                    if k in ['message-id']:
                        msg_low[k] = msg_low[k].strip("[ |<|>]")

                s[num] = dict(zip(msg_low.keys(), msg_low.values()))

    M.close()
    M.logout()

    return s,status


"""
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
"""


def send_message_smtp(account, to_field, msg):
    """
    Функция отправки сообщения.

    :param account: содежит объект класса Account для отправки письма
    :param to_field: адреса на которые будет произведена отправка сообщения
    :param msg: сформированное сообщение. Объект класса email.MIMEMultipart.MIMEMultipart

    :return: статус отправки
    """

    server = "smtp." + re.split('\.',account.server,1)[1]

    # Send mail
    try:
        smtp = SMTP_SSL()
        smtp.connect(server)
        smtp.login(account.login, account.password)
        smtp.sendmail(account.login, to_field, msg.as_string())
        smtp.quit()
    except Exception as e:
        return [False,str(e)]
    else:
        return [True,"OK"]


def save_message_to(msg, save_dir, account):
    """
    Функция сохраняет переданное сформированное сообщение в указанный каталог аккаунта.

    :param msg: сформированное сообщение email
    :param save_dir: каталог для сохранения сообщения
    :param account: объект класса Account для сохранения сообщения
    :return: статус операции
    """

    dirs = json.loads(account.dirs)
    try:
        M = imaplib.IMAP4_SSL(account.server)
    except Exception as e:
        print 'Connection problem! %s ' % str(e)
        return [False,str(e)]
    try:
        M.login(account.login, account.password)
    except Exception as e:
        print 'Auth problem!%s ' % str(e)
        return [False,str(e)]
    else:
        try:
            M.append(dirs[save_dir], "", imaplib.Time2Internaldate(time.time()), msg.as_string())
        except Exception as e:
            print 'Message save problem!%s ' % str(e)
            return [False,str(e)]

        M.logout()
        print "Сохраняем в %s" % save_dir

    return [True,"OK"]


def outgoing_message(data):
    """
    Функция проверяет правильность заполнения всех зоголовков и формирует сообщение.
    В зависимости от указанной опции, отправляет по smtp получателю и записыает в папку sent аккаунта или записывает
    сообщение в папку draft.

    :param data: данные для формирования письма.
    :return:
    """

    try:
        account = rwObjects.get_by_uuid(data['account'])[0]
    except Exception as e:
        return [False,"Ошибка при получении данных аккаунта. Ошибка: %s" % str(e)]
    else:
        pass

    to_field = ""
    msg = email.MIMEMultipart.MIMEMultipart()
    msg['Message-ID'] = email.Utils.make_msgid()
    data['from'] = account.login
    from email.header import Header

    # Проверка параметров полученных при написании сообщения
    # Кодирование заголовков
    try:
        for f in ['to', 'cc', 'from']:
            addrs = extract_addresses(data[f])
            s = list()
            print "Поле %s" % f
            for addr in addrs.keys():
                if addr or f == 'cc':
                    s.append(email.utils.formataddr((str(email.header.make_header([(addrs[addr],'utf8')])), addr)))
                else:
                    return [False, "rwEmail.outgoing_message. Операция extract_addresses. Пустой параметр: %s"\
                            % str(f)]
                print ", ".join(s)
            data[f] = ", ".join(s)
            if f == 'to':
                to_field = ", ".join(addrs.keys())
    except Exception as e:
        return [False, "rwEmail.outgoing_message. Операция проверки параметров. Ошибка: %s" % str(e)]

    msg['From'] = data['from']
    msg['To'] = data['to']
    msg['Cc'] = data['cc']
    msg['Subject'] = email.header.Header(data['subject'], 'utf8')

    if 'references' in data.keys():
        msg['References'] = email.header.Header(data['references'],'utf8')

    data_html = data['body']
    data_plain = ''

    msg.preamble = "This is a multi-part message in MIME format."
    msg.epilogue = "End of message"
    msgAlternative = email.MIMEMultipart.MIMEMultipart('alternative')
    msg.attach(msgAlternative)
    msgText = email.MIMEText.MIMEText(data_plain, "plain", "UTF-8")
    msgAlternative.attach(msgText)
    to_attach = email.MIMEText.MIMEText(data_html, "html", "UTF-8")
    msgAlternative.attach(to_attach)

    print msg.as_string()

    if data['send_options'] == 'to_drafts':
        # Сохраняем в Черновики
        status = save_message_to(msg, "drafts", account)
        return status

    elif data['send_options'] == 'now':
        # Отправляем и сохраняем в Отправленные
        status_send = send_message_smtp(account, to_field, msg)
        if not status_send[0]:
            return status_send
        status_save = save_message_to(msg, "sent", account)
        if not status_save[0]:
            return status_save

    return [True,"OK"]



