#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import ConfigParser
import base64
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import parseaddr, formataddr


class SendMail:
    def __init__(self, sfile="conf/mail.ini", param="gmail"):
        """
        初始化ini配置文件信息
        :param sfile: ini配置文件路径
        :param param: ini配置文件的paramater
        """
        self.__sfile = sfile
        self.__param = param

    def __get_mail_conf(self):
        """
        通过配置文件获取邮件相关信息
        :return: SMTP服务器地址、登录账号、登录密码、发件人名称、发件人地址
        """
        if not os.path.exists(self.__sfile):
            print "Error: %s doesn't exist" % self.__sfile
            sys.exit(-1)
        conf = ConfigParser.ConfigParser()
        conf.read(self.__sfile)
        try:
            mail_host = conf.get(self.__param, "host")
            mail_user = conf.get(self.__param, "user")
            mail_passwd_base64 = conf.get(self.__param, "passwd")
            mail_passwd = base64.decodestring(mail_passwd_base64)
            sender_name = conf.get(self.__param, "name")
            sender_addr = conf.get(self.__param, "sender")
        except Exception as e:
            print "Error:", e
            sys.exit(-2)
        return mail_host, mail_user, mail_passwd, sender_name, sender_addr

    @staticmethod
    def __format_addr(raw_addr):
        """
        格式化邮件地址
        :param raw_addr: 原始格式地址，可以为仅邮箱地址或"名称<邮箱地址>"
        :return: 格式化后的邮件地址
        """
        name, addr = parseaddr(raw_addr)
        return formataddr((Header(name, "utf-8").encode(),
                           addr.encode("utf-8") if isinstance(addr, unicode) else addr))

    def send_mail(self, rcpt_list, subject, content, att_list=None, cc_list=None, mail_type="html"):
        """
        发送邮件
        :param rcpt_list: 收件人列表
        :param subject: 标题
        :param content: 内容
        :param att_list: 附件列表，默认为空
        :param cc_list: 抄送人列表，默认为空
        :param mail_type: 邮件类型，"html"或"plain"，默认为"html"
        :return: 是否发送成功，True或False
        """
        if cc_list is None:
            cc_list = []
        if att_list is None:
            att_list = []
        # 通过配置文件获取邮箱服务器、登录账号、登录密码、发件人名称和发件人地址
        mail_host, mail_user, mail_passwd, sender_name, sender_addr = self.__get_mail_conf()
        # 格式化邮箱地址
        mail_from = self.__format_addr("%s <%s>" % (sender_name, sender_addr))
        rcpt_list = [self.__format_addr(rcpt_addr) for rcpt_addr in rcpt_list]
        cc_list = [self.__format_addr(cc_addr) for cc_addr in cc_list]
        # 配置邮件标题、发件人、收件人、抄送人和内容
        msg = MIMEMultipart()
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = mail_from
        msg["To"] = ";".join(rcpt_list)
        msg["Cc"] = ";".join(cc_list)
        text_msg = MIMEText(content, _subtype=mail_type, _charset="utf-8")
        msg.attach(text_msg)
        # 配置附件
        for att_path in att_list:
            att_name = os.path.basename(att_path)
            with open(att_path, "rb") as fp:
                part = MIMEApplication(fp.read())
                part.add_header("Content-Disposition", "attachment", filename=att_name)
                msg.attach(part)
        # 发送邮件
        try:
            server = smtplib.SMTP_SSL()
            server.connect(mail_host)
            server.login(mail_user, mail_passwd)
            server.sendmail(mail_from, rcpt_list+cc_list, msg.as_string())
            server.close()
            return True, None
        except Exception as e:
            print "Error:", e
            return False, e.message
