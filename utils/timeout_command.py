#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import datetime
import signal


def run(cmd, timeout=10):
    start = datetime.datetime.now()
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
        now = datetime.datetime.now()
        if (now - start).seconds > timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None
    return process.stdout.read()
