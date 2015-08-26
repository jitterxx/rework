# -*- coding: utf-8 -*-
"""
Created on Mon May 25 16:01:48 2015

@author: sergey

Модуль содержит функции необходимые для проведения классификации текстовых
данных.


"""

#!/usr/bin/python -t
# coding: utf8

__author__ = 'sergey'

from email import utils
import re


def extract_addresses(field):
    """
    :param field: Строка из которой надо извлечь имена и адреса. ФОрмат строки: ФИО_пробел_<email>,
    ФИО_пробел_<email>,... .

    :return addresses: Возвращает словарь в формате: key - email: value - ФИО или email, если ничего не было указано.
    """

    addresses = dict()
    a = re.split(",",str(field))
    for each in a:
        name, addr = utils.parseaddr(each)
        if name == "":
            addresses[addr] = addr
        else:
            addresses[addr] = name

    return addresses
