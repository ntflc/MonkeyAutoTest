#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket
import subprocess
import shutil
import logging

# 设置连接最大时长
socket.setdefaulttimeout(10)


def get_apk_from_url(url, prj_ver):
    # 如果路径不存在，先创建路径
    saved_path = "apks/" + prj_ver
    if not os.path.isdir(saved_path):
        os.mkdir(saved_path)
    # 下载apk包
    # 拆分出apk包的文件名，从而得到目标路径
    apk_name = url.split("/")[-1]
    file_path = saved_path + "/" + apk_name
    # 如果apk文件存在，则先删除
    if os.path.exists(apk_name):
        os.remove(apk_name)
    # 下载
    try:
        cmd = "wget '%s' %s" % (url, saved_path)
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.communicate()
        shutil.move(apk_name, file_path)
        return file_path
    except Exception as e:
        logging.warning(e)
        return None


def get_latest_apk():
    # TODO
    # 自动取最新包代码
    return "apk_path"
