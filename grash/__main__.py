#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import grash

settings = grash.Settings()

if __name__ == "__main__":
    templatePath = os.path.join(os.getcwd(), settings.templatePath)
    site = grash.make(templatePath=templatePath)
    site.render()
