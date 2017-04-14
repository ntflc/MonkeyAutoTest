#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import datetime
import logging
import re

LOG_ROOT = "logs"
HISTORY_ROOT = "history_logs"


class ProjectLog:
    def __init__(self):
        self.log_root = LOG_ROOT
        self.log_path = "{}/{}".format(LOG_ROOT, "log.txt")
        self.history_root = HISTORY_ROOT

    def set_up(self):
        # 清理之前的项目日志目录
        if os.path.exists(self.log_root):
            shutil.rmtree(self.log_root)
        # 创建新的项目日志目录
        os.makedirs(self.log_root)
        # 初始化logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s\t[%(threadName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            filename=self.log_path,
            filemode="w"
        )

    def tear_down(self):
        # 创建历史结果目录
        if not os.path.exists(self.history_root):
            os.makedirs(self.history_root)
        # 将本次结果目录复制到历史结果目录
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        dest_dir = "{}/{}".format(self.history_root, now)
        shutil.copytree(self.log_root, dest_dir)


class DeviceLog:
    def __init__(self, sn):
        self.sn = sn
        self.device_root = "{}/{}".format(LOG_ROOT, self.sn)
        self.anr_dir = "{}/{}".format(self.device_root, "anr")
        self.crash_dir = "{}/{}".format(self.device_root, "crash")
        self.dump_dir = "{}/{}".format(self.device_root, "dumpsys")
        self.log_path = "{}/{}".format(self.device_root, "monkey.log")

    def init(self):
        # 清理device之前的日志目录
        if os.path.exists(self.device_root):
            shutil.rmtree(self.device_root)
        # 创建device所需的日志目录
        os.makedirs(self.device_root)
        os.makedirs(self.anr_dir)
        os.makedirs(self.crash_dir)
        os.makedirs(self.dump_dir)

    @staticmethod
    def __remove_excess_traces(anr_info):
        # 获取PID
        pid = 0
        for line in anr_info:
            if line.startswith("PID: "):
                pid = re.findall(r"PID: (\d+)", line)[0]
                break
        # 获取anr traces起始、末尾行，对应pid的起始、末尾行:
        trace_start = 0
        trace_end = 0
        trace_pid_start = 0
        trace_pid_end = 0
        for i in range(len(anr_info)):
            line = anr_info[i]
            if "----- pid " in line and trace_start == 0:
                trace_start = i
            if "----- end " in line:
                trace_end = i
            if "----- pid %s " % pid in line and trace_pid_start == 0:
                trace_pid_start = i
            if "----- end %s " % pid in line and trace_pid_end == 0:
                trace_pid_end = i
        # 如果起始、末尾行有问题，则不处理
        if not (0 < trace_start <= trace_pid_start < trace_pid_end <= trace_end or
                (trace_pid_start == trace_pid_end == 0 < trace_start < trace_end)):
            return anr_info
        # 处理保留信息
        anr_store = []
        for i in range(len(anr_info)):
            line = anr_info[i]
            if i < trace_start or i > trace_end or trace_pid_start <= i <= trace_pid_end:
                anr_store.append(line)
        return anr_store

    def check(self, package):
        with open(self.log_path, "r") as fp:
            # 判断文件行是否为anr或crash，如果是则做相关处理
            is_anr = 0
            is_crash = False
            # anr和crash计数
            anr_cnt = 0
            crash_cnt = 0
            # anr和crash信息
            anr_info = []
            crash_info = []
            # 逐行读取日志信息
            for line in fp:
                # ANR处理
                if line.startswith("// NOT RESPONDING: {} ".format(package.name)):
                    if is_anr == 0:
                        anr_cnt += 1
                    is_anr += 1
                if is_anr != 0:
                    anr_info.append(line)
                if is_anr != 0 and line.strip() == "// meminfo status was 0":
                    is_anr -= 1
                    if is_anr == 0:
                        # 去掉多余的traces
                        anr_info = self.__remove_excess_traces(anr_info)
                        # 存成文件
                        with open("{}/anr_{}_{}.txt".format(self.anr_dir, self.sn, anr_cnt), "w") as anr_fp:
                            for anr_line in anr_info:
                                anr_fp.write(anr_line)
                        # 清空
                        anr_info = []
                # CRASH处理
                if line.startswith("// CRASH: {} ".format(package.name)) or line.startswith("// CRASH: {}:".format(package.name)):
                    is_crash = True
                    crash_cnt += 1
                if is_crash:
                    crash_info.append(line)
                if is_crash and line.strip() == "//":
                    # 存成文件
                    with open("{}/crash_{}_{}.txt".format(self.crash_dir, self.sn, crash_cnt), "w") as crash_fp:
                        for crash_line in crash_info:
                            crash_fp.write(crash_line)
                    # 清空
                    crash_info = []
                    is_crash = False

    @staticmethod
    def __numerical_sort(value):
        numbers = re.compile(r"(\d+)")
        parts = numbers.split(value)
        parts[1::2] = map(int, parts[1::2])
        return parts

    def get(self):
        # 获取anr、crash、dumpsys
        anr_fn_list = os.listdir(self.anr_dir)
        anr_fn_list = sorted(anr_fn_list, key=self.__numerical_sort, reverse=False)
        anr_cnt = len(anr_fn_list)
        crash_fn_list = os.listdir(self.crash_dir)
        crash_fn_list = sorted(crash_fn_list, key=self.__numerical_sort, reverse=False)
        crash_cnt = len(crash_fn_list)
        dumpsys_fn_list = os.listdir(self.dump_dir)
        # 将anr、crash、dumpsys写入附件list
        att_list = []
        for fn in anr_fn_list:
            att_list.append("{}/{}".format(self.anr_dir, fn))
        for fn in crash_fn_list:
            att_list.append("{}/{}".format(self.crash_dir, fn))
        for fn in dumpsys_fn_list:
            att_list.append("{}/{}".format(self.dump_dir, fn))
        # 返回anr_cnt、crash_cnt和att_list
        return anr_cnt, crash_cnt, att_list
