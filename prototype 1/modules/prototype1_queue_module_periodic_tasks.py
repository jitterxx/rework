# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 13:11:50 2015

@author: sergey

Файл настроек для периодических задач.
"""


import celery
from celery.decorators import periodic_task
from datetime import timedelta,datetime
import prototype1_queue_module as rwQueue

import sys
reload(sys)
sys.setdefaultencoding("utf-8")


app = celery.Celery('tasks', backend='rpc://', broker='amqp://guest@localhost//')
app.conf.update(
    CELERYBEAT_SCHEDULE = {
        'add-every-5-min': {
            'task': 'prototype1_queue_module.get_messages_for_account',
            'schedule': timedelta(seconds=30),
            'args': (['b1c4a3e2-3c58-11e5-b1af-f46d04d35cbd'])
        },
    },
    CELERY_TIMEZONE = 'Europe/Moscow'
)
