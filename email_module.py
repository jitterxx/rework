# -*- coding: utf-8 -*-
"""
Created on Mon May 25 16:01:48 2015

@author: sergey
"""

#!/usr/bin/python -t
# coding: utf8

import imaplib
import email
import pandas as pd
from bs4 import BeautifulSoup
import chardet


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


def get_emails_google(ddd):
    server = "imap.gmail.com"
    port = "993"
    login = "sergey@reshim.com"
    password = "OO00zZOK2"
    date_after = ddd
    date_before = "25-may-2015"
    dirs = {'inbox':'INBOX','sent':'[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-'}
    
    try:
        M = imaplib.IMAP4_SSL(server)
    except: 
        print 'Connection problem!', sys.exc_info()[0]
        
            
    
    print M.PROTOCOL_VERSION
    
    #password = raw_input('Password:')
    
    M.login(login,password)
    s = {}
    
    for cur_dir in dirs.keys():
        print M.select(dirs[cur_dir])
        
        typ, data = M.search('UTF8','SINCE',date_after)
     
        for num in data[0].split():
            typ, data = M.fetch(num, '(RFC822)')
        
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
                        html = unicode(part.get_payload(decode=True),
                                       part.get_content_charset(),
                                       'replace').encode('utf8','replace')
                        msg_data['Text'] +=  get_text(html)
        
            else:
                if msg.get_content_type() == "text/plain":
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
                s[num] = dict(zip(msg_data.keys(), msg_data.values()))
    
    M.close()
    M.logout()
    
    return s

"""emails = get_emails()

f2 = open("email_df", 'w')
emails.to_json(f2)
f2.close()
"""


