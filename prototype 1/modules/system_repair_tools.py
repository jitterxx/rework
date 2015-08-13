# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:11:50 2015

Функции для проверки и исправления связей.

"""
__author__ = 'sergey'

import celery
import prototype1_objects_and_orm_mappings as rwObjects
import prototype1_email_module as rwEmail
from datetime import timedelta, datetime
import prototype1_queue_module as rwQueue

import sys

reload(sys)
sys.setdefaultencoding("utf-8")


def repair_apply_rules_func():
    """
    Функция ищет все события создания объектов и запускает заново автоматические правила.
    :return:
    """

    session = rwObjects.Session()

    #Забираем все события создания

    response = session.query(rwObjects.Reference).filter(rwObjects.Reference.link == 1).all()

    for ref in response:
        print "Проверка для ",ref
        print ref.source_uuid
        print ref.source_type
        print ref.target_uuid
        print ref.target_type
        try:
            rwQueue.apply_rules.delay(ref.source_uuid,ref.source_type,ref.target_uuid, ref.target_type)
        except Exception as e:
            print e
        else:
            pass




    session.close()


repair_apply_rules_func()