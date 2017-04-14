#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import argparse
import threading
from utils import addition
from utils import ProjectLog


def init_param():
    """
    系统参数：
    -v/--version,必填，项目版本。该项目版本必须为conf/project.json中的主key
    -u/--url，选填，apk网络地址。如果存在该项，则不自动取包，改用该地址的apk文件（优先级高于-p/--path）
    -p/--path，选填，apk本地路径。如果存在该项，则不自动取包，改用该路径的apk文件（优先级低于-u/--url）
    -s/--sn，必填，待测设备序列号。如果有多个，以空格隔开
    -i/--uninstall，选填，安装前是否卸载。参数取值为true时，安装apk之前会先执行卸载操作
    -t/--throttle，选填，monkey参数。默认值为700
    -c/--count，选填，monkey参数。默认值为10000
    -r/--recipient，必填，收件人。如果有多个，以空格隔开
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", required=True, help="Project version, must in conf/project.json")
    parser.add_argument("-u", "--url", required=False, help="URL of apk which for monkey test")
    parser.add_argument("-p", "--path", required=False, help="Local path of apk which for monkey test")
    parser.add_argument("-s", "--sn", required=True, help="Serial number(s) of Android device")
    parser.add_argument("-i", "--uninstall", required=False, help="Uninstall package before install")
    parser.add_argument("-t", "--throttle", required=False, help="Parameter in monkey, throttle", default="700")
    parser.add_argument("-c", "--count", required=False, help="Parameter in monkey, count", default="10000")
    parser.add_argument("-r", "--recipient", required=True, help="Email recipient(s) of results")
    args = parser.parse_args()
    prj_ver = args.version
    apk_url = args.url or ""
    apk_path = args.path or ""
    serial_number = args.sn
    sn_list = serial_number.split()
    need_uninstall = True if args.uninstall is not None and args.uninstall.lower() == "true" else False
    throttle = int(args.throttle)
    count = int(args.count)
    recipient = args.recipient
    rcpt_list = recipient.split()
    return prj_ver, apk_url, apk_path, sn_list, need_uninstall, throttle, count, rcpt_list


def main():
    # 获取系统参数
    prj_ver, apk_url, apk_path, sn_list, need_uninstall, throttle, count, rcpt_list = init_param()
    # 获取版本信息
    prj_json = addition.get_project_json()
    if prj_ver not in prj_json:
        logging.error("project version not found")
        sys.exit(-1)
    # 获取apk安装包
    logging.info(">>> Getting package")
    package = addition.get_package(prj_ver, prj_json[prj_ver], apk_url, apk_path)
    logging.info("path: {}".format(package.path))
    logging.info("name: {}".format(package.name))
    logging.info(">>> Done")
    # 多线程测试
    thread_list = []
    for sn in sn_list:
        thread = threading.Thread(
            target=addition.monkey_test,
            name=sn,
            args=(sn, package, prj_json[prj_ver], need_uninstall, throttle, count, rcpt_list)
        )
        thread_list.append(thread)
    # 启动所有线程
    for thread in thread_list:
        thread.start()
    # 主线程等待所有子线程退出
    for thread in thread_list:
        thread.join()


if __name__ == "__main__":
    # 初始化日志
    project_log = ProjectLog()
    project_log.set_up()
    # 主程序
    main()
    # 将本次结果复制到历史日志目录
    project_log.tear_down()
