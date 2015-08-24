# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 17:04:18 2015

@author: sergey
"""
__author__ = 'sergey'


tables_update = """
                ALTER TABLE `rework`.`knowledge_tree`
                ADD COLUMN `action` VARCHAR(256) NULL DEFAULT 'no' AFTER `type`;
                """


print "\n---------------- Необходимо обновить БД ---------------------\n"
print tables_update
print """\nРаскомментируйте строку : # #tools.proxy.base: "https://test.rework.reshim.com"\n
 в файле app.config."""
print "\n---------------- Спасибо ---------------------\n"