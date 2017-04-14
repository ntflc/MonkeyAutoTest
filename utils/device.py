#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import re
import random
import logging
from utils import timeout_command


class Device:
    def __init__(self, sn):
        self.sn = sn
        self.os = ""
        self.screen = ""
        self.model = ""
        self.__set_device_info()

    def __set_device_info(self):
        # 获取本机所有设备名
        rst = timeout_command.run("adb devices")
        sn_list = re.findall(r"(.+?)\s+device\n", rst)
        # 判断device是否存在
        if self.sn not in sn_list:
            logging.error("device [{}] not found".format(self.sn))
            sys.exit(-1)
        # 获取系统版本号
        cmd = "adb -s {} shell getprop ro.build.version.release".format(self.sn)
        rst = timeout_command.run(cmd)
        if rst is None:
            logging.warning("[device_info] time out: {}".format(cmd))
        elif "error" in rst:
            logging.warning("[device_info] cannot execute: {}".format(cmd))
            logging.warning("[device_info] result: {}".format(rst))
        else:
            try:
                os_version = re.findall(r"\d.\d.\d|\d.\d|[A-Z]", rst)[0]
                self.os = os_version
            except Exception as e:
                logging.warning("[device_info] failed to regex os from {}. {}".format(rst, e))
        # 获取分辨率
        cmd = "adb -s {} shell dumpsys window | grep init".format(self.sn)
        rst = timeout_command.run(cmd)
        if rst is None:
            logging.warning("[device_info] time out: {}".format(cmd))
        elif "error" in rst:
            logging.warning("[device_info] cannot execute: {}".format(cmd))
            logging.warning("[device_info] result: {}".format(rst))
        else:
            try:
                screen = re.findall(r"init=(\d{3,4}x\d{3,4})", rst)[0]
                self.screen = screen
            except Exception as e:
                logging.warning("[device_info] failed to regex screen from {}. {}".format(rst, e))
        # 获取设备名
        cmd = "adb -s {} shell getprop ro.product.model".format(self.sn)
        rst = timeout_command.run(cmd)
        if rst is None:
            logging.warning("[device_info] time out: {}".format(cmd))
        elif "error" in rst:
            logging.warning("[device_info] cannot execute: {}".format(cmd))
            logging.warning("[device_info] result: {}".format(rst))
        else:
            try:
                model = rst.strip()
                self.model = model
            except Exception as e:
                logging.warning("[device_info] failed to get model. {}".format(e))

    def install(self, package):
        # 安装包
        cmd = "adb -s {} install -r {}".format(self.sn, package.path)
        rst = timeout_command.run(cmd, 600)
        if rst is None:
            logging.error("[install] failed to install, the command is: {}".format(cmd))
            sys.exit(-1)
        elif "Success" in rst:
            logging.info("[install] succeeded in installing {}".format(package.name))
        elif "Failure" in rst:
            try:
                key = re.findall(r"Failure \[(.+?)\]", rst)[0]
            except Exception as e:
                logging.debug(e)
                key = "NULL"
            logging.error("[install] failed to install {}, reason: {}".format(package.name, key))
            sys.exit(-1)

    def uninstall(self, package):
        # 卸载包
        cmd = "adb -s {} uninstall {}".format(self.sn, package.name)
        rst = timeout_command.run(cmd, 600)
        if rst is None:
            logging.error("[uninstall] failed to uninstall, the command is: {}".format(cmd))
        elif "Success" in rst:
            logging.info("[uninstall] succeeded in uninstalling {}".format(package.name))
        elif "Failure" in rst:
            try:
                key = re.findall(r"Failure \[(.+?)\]", rst)[0]
            except Exception as e:
                logging.debug(e)
                key = "NULL"
            logging.error("[uninstall] failed to uninstall {}, reason: {}".format(package.name, key))

    def enable_simiasque(self):
        # 启动simiasque
        cmd = "adb -s {} shell am start -n org.thisisafactory.simiasque/org.thisisafactory.simiasque.MyActivity_".format(self.sn)
        timeout_command.run(cmd)
        time.sleep(1)
        # 返回桌面
        cmd = "adb -s {} shell input keyevent KEYCODE_HOME".format(self.sn)
        timeout_command.run(cmd)
        time.sleep(1)
        # 打开simiasque开关
        cmd = "adb -s {} shell am broadcast -a org.thisisafactory.simiasque.SET_OVERLAY --ez enable true".format(self.sn)
        timeout_command.run(cmd)

    def disable_simiasque(self):
        # 关闭simiasque开关
        cmd = "adb -s {} shell am broadcast -a org.thisisafactory.simiasque.SET_OVERLAY --ez enable false".format(self.sn)
        timeout_command.run(cmd)

    def enable_wifi_manager(self):
        # 启动Wifi Manager
        cmd = "adb -s {} shell am start -n com.ntflc.wifimanager/.MainActivity".format(self.sn)
        timeout_command.run(cmd)
        time.sleep(1)
        # 返回桌面
        cmd = "adb -s {} shell input keyevent KEYCODE_HOME".format(self.sn)
        timeout_command.run(cmd)

    def dumpsys_activity(self, path):
        dumpsys_name = "dumpsys_{}.txt".format(self.sn)
        # adb shell dumpsys activity
        cmd = "adb -s {} shell dumpsys activity > {}/{}".format(self.sn, path, dumpsys_name)
        logging.info(cmd)
        timeout_command.run(cmd)

    def turn_off_screen(self):
        cmd = "adb -s {} shell input keyevent POWER".format(self.sn)
        timeout_command.run(cmd)

    def run_monkey(self, package, path, throttle=700, cnt=10000):
        # 停止进程
        cmd = "adb -s {} shell am force-stop {}".format(self.sn, package.name)
        os.popen(cmd)
        time.sleep(3)
        # 生成随机数
        rand = random.randint(0, 65535)
        # 执行monkey命令
        cmd = "adb -s {} shell monkey -p {} -s {} --ignore-crashes --ignore-timeouts --throttle {} -v {} > {}".format(
            self.sn, package.name, rand, throttle, cnt, path
        )
        logging.info(cmd)
        os.popen(cmd)
        time.sleep(5)
        # 停止进程
        cmd = "adb -s {} shell am force-stop {}".format(self.sn, package.name)
        os.popen(cmd)
