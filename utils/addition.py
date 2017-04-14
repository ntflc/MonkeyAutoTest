#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import logging
from utils import get_apk
from utils import Device
from utils import Package
from utils import DeviceLog
from libs import SendMail


def get_project_json(sfile="conf/project.json"):
    with open(sfile) as json_file:
        try:
            prj_json = json.load(json_file)
        except Exception as e:
            logging.error(e)
            sys.exit(-1)
    return prj_json


def monkey_test(sn, package, prj_info, need_uninstall, throttle, count, rcpt_list):
    device = Device(sn)
    device_log = DeviceLog(sn)
    # 初始化设备日志
    logging.info(">>> Init log for device")
    device_log.init()
    logging.info(">>> Done")
    # 卸载apk文件
    if need_uninstall:
        logging.info(">>> Uninstall package")
        device.uninstall(package)
        logging.info(">>> Done")
    # 安装apk文件
    logging.info(">>> Install package")
    device.install(package)
    logging.info(">>> Done")
    # 安装Wifi Manager
    logging.info(">>> Install Wifi Manager")
    device.install(Package("apks/wifimanager-debug.apk"))
    logging.info(">>> Done")
    # 启动Wifi Manager
    logging.info(">>> Enable Wifi Manager")
    device.enable_wifi_manager()
    logging.info(">>> Done")
    # 安装simiasque
    logging.info(">>> Install simiasque")
    device.install(Package("apks/simiasque-debug.apk"))
    logging.info(">>> Done")
    # 启动simiasque
    logging.info(">>> Enable simiasque")
    device.enable_simiasque()
    logging.info(">>> Done")
    # 执行monkey测试
    logging.info(">>> Run monkey test")
    device.run_monkey(package, device_log.log_path, throttle, count)
    logging.info(">>> Done")
    # 关闭simiasque
    logging.info(">>> Disable simiasque")
    device.disable_simiasque()
    logging.info(">>> Done")
    # 关闭屏幕
    logging.info(">>> Turn off screen")
    device.turn_off_screen()
    logging.info(">>> Done")
    # 生成dumpsys信息
    logging.info(">>> Dumpsys activities")
    device.dumpsys_activity(device_log.dump_dir)
    logging.info(">>> Done")
    # 分析设备日志
    logging.info(">>> Check logs")
    device_log.check(package)
    logging.info(">>> Done")
    # 获取anr数量、crash数量和附件list
    anr_cnt, crash_cnt, att_list = device_log.get()
    # 发送邮件
    send_log(prj_info, device, package, rcpt_list, anr_cnt, crash_cnt, att_list)


def send_log(prj_info, device, package, rcpt_list, anr_cnt, crash_cnt, att_list):
    # 如果没有anr和crash，则不发邮件
    if anr_cnt == 0 and crash_cnt == 0:
        logging.info("No anr or crash, won't send mail")
        return
    prj_name = prj_info["name"]
    subject = u"%s Monkey测试异常提醒" % prj_name
    content = "<table border='1' cellspacing='0' cellpadding='0'>" \
              + "<tr align='center'><th style='width:600px' colspan='2'>{} Monkey测试结果</th></tr>".format(prj_name) \
              + "<tr><td width='30%%'><b>安装包文件名</b></td><td width='70%%'>{}</a></td></tr>".format(package.filename) \
              + "<tr><td width='30%%'><b>安装包包名</b></td><td width='70%%'>{}</td>".format(package.name) \
              + "<tr><td width='30%%'><b>设备型号</b></td><td width='70%%'>{}</td>".format(device.model) \
              + "<tr><td width='30%%'><b>设备序列号</b></td><td width='70%%'>{}</td>".format(device.sn) \
              + "<tr><td width='30%%'><b>系统版本</b></td><td width='70%%'>{}</td>".format(device.os) \
              + "<tr><td width='30%%'><b>分辨率</b></td><td width='70%%'>{}</td>".format(device.screen) \
              + "<tr><td width='30%%'><b>发现ANR次数</b></td><td width='70%%'>{}</td>".format(anr_cnt) \
              + "<tr><td width='30%%'><b>发现CRASH次数</b></td><td width='70%%'>{}</td>".format(crash_cnt) \
              + "</table>" \
              + "<br/><p>具体日志见附件</p>"
    status, reason = SendMail().send_mail(rcpt_list, subject, content, att_list=att_list)
    if status:
        logging.info("Succeed in sending mails")
    else:
        logging.error("Failed to send mails, reason: %s" % reason)


def get_package(prj_ver, prj_info, apk_url, apk_path):
    # 如果apk_url不为空，优先下载该apk
    if apk_url != "":
        logging.info("[get_package] get apk from url: {}".format(apk_url))
        apk_path = get_apk.get_apk_from_url(apk_url, prj_ver)
    # 如果apk_url为空，apk_path不为空，直接使用该路径的apk
    elif apk_path != "":
        logging.info("[get_package] get apk from local: {}".format(apk_path))
    # 如果apk_url和apk_path均为空，则通过prj_info下载最新包
    else:
        logging.info("[get_package] get latest apk...")
        apk_path = get_apk.get_latest_apk()
    # 如果apk_path为None，则报错，否则返回包
    if apk_path is None:
        logging.error("[get_package] failed to get package")
        sys.exit(-1)
    return Package(apk_path)
