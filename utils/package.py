#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import logging
from utils import timeout_command


class Package:
    def __init__(self, pkg_path):
        self.path = pkg_path
        self.filename = ""
        self.name = ""
        self.activity = ""
        self.__set_pkg_info()

    def __set_pkg_info(self):
        # 判断路径是否存在
        if not os.path.exists(self.path):
            logging.error("package from '{}' not found".format(self.path))
            sys.exit(-1)
        # 获取文件名
        self.filename = os.path.basename(self.path)
        # 获取包名
        cmd = "aapt dump badging {} | grep package".format(self.path)
        rst = timeout_command.run(cmd)
        if rst is None:
            logging.warning("[pkg_info] time out: {}".format(cmd))
        elif "ERROR" in cmd:
            logging.warning("[pkg_info] cannot execute: {}".format(cmd))
            logging.warning("[pkg_info] result: {}".format(rst))
        else:
            try:
                package_name = re.findall(r"name='([a-zA-Z._]+)'", rst)[0]
                self.name = package_name
            except Exception as e:
                logging.warning("[pkg_info] failed to regex package name from {}. {}".format(rst, e))
        # 获取启动Activity
        cmd = "aapt dump badging {} | grep launchable-activity".format(self.path)
        rst = timeout_command.run(cmd)
        if rst is None:
            logging.warning("[pkg_info] time out: {}".format(cmd))
        elif "ERROR" in cmd:
            logging.warning("[pkg_info] cannot execute: {}".format(cmd))
            logging.warning("[pkg_info] result: {}".format(rst))
        else:
            try:
                activity_list = re.findall(r"name='(.+?)'", rst)
                main_activity = ""
                for activity in activity_list:
                    if not activity.startswith("com.squareup") and not activity.startswith("com.github"):
                        main_activity = activity
                        break
                self.activity = main_activity
            except Exception as e:
                logging.warning("[pkg_info] failed to regex main activity from {}. {}".format(rst, e))
