# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
from datetime import datetime
import re
import requests
# third-party
try:
    import feedparser
except:
    import subprocess
    import sys
    subprocess.check_output([sys.executable, '-m', 'pip', 'install', 'feedparser'], universal_newlines=True)
    import feedparser
# sjva 공용
from framework import app, db, scheduler, path_app_root
from framework.job import Job
from framework.util import Util
from framework.common.rss import RssUtil
from system.logic import SystemLogic
import framework.common.notify as Notify

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelFeed
#########################################################

class LogicNormal(object):
    @staticmethod
    def scheduler_function():
        try:
            logger.debug('scheduler_function')
            LogicNormal.process_insert_feed()
            LogicNormal.process_check_rule()
            LogicNormal.process_check_alarm()

        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_rss(url):
        datas = []
        getdata = requests.get(url=url)
        check_regex = re.compile(r'<item>\s+<title>(?P<title>.+)</title>\s+<link>(?P<link>.+no=(?P<rss_id>\d+))</link>\s+\<description\>(?P<description>[\w\W]*?)\<\/description\>\s+(?:<author>(?P<author>.+)</author>\s+)*<pubDate>(?P<pub_date>.*)</pubDate>')
        for item in reversed(list(check_regex.finditer(getdata.text))):
            datas.append(item.groupdict())
        if len(datas) == 0 :
            logger.error('Did not regex parsing.')
            logger.error(getdata.text)
        return datas
    @staticmethod
    def get_crawl(url):
        datas = []
        getdata = requests.get(url=url)
        check_regex = re.compile(r'<span class=list_name>(?P<author>.+)</span>[\w\W]*?\s+<a href=\".+no=(?P<rss_id>\d+)\"\s+><font class=list_title>(?P<title>.+)</font></a>[\w\W]*?<nobr class=\'eng list_vspace\'>(?P<pub_date>\d+:\d+:\d+|\d+/\d+/\d+)</td>')

        for item in check_regex.finditer(getdata.text):
            data = item.groupdict()
            data['link'] = 'https://www.ppomppu.co.kr/zboard/view.php?id=' + LogicNormal.get_board_ids(url)[0] + '&no=' + data['rss_id']
            datas.append(data)
        if len(datas) == 0 :
            logger.error('Did not regex parsing.')
            logger.error(getdata.text)
        return datas
    @staticmethod
    def get_board_ids(url_text=None):
        if not url_text:
            url_text = ModelSetting.get('rss_url')
        result = []
        if ',' in url_text:
            url_arr = url_text.split(',')
            url_arr = [x.strip() for x in url_arr]
        else:
            url_arr = [url_text.strip()]
        for url in url_arr:
            if 'id=' in url:
                result.append(url.split('id=')[1].split('&')[0])
            elif 'no=' in url:
                result.append(url.split('no=')[1].split('&')[0])
        return result
    @staticmethod
    def process_insert_feed():
        is_rss = ModelSetting.get_bool('use_rss')
        rss_url = ModelSetting.get('rss_url')
        if ',' in rss_url:
            rss_url = rss_url.split(',')
            rss_url = [x.strip() for x in rss_url]
        else:
            rss_url = [rss_url.split()]
        datas = []
        if is_rss:
            for url in rss_url:
                datas += LogicNormal.get_rss(url)
        else:
            for url in rss_url:
                datas +=LogicNormal.get_crawl('https://www.ppomppu.co.kr/zboard/zboard.php?id=' + LogicNormal.get_board_ids(url)[0])
                logger.debug('https://www.ppomppu.co.kr/zboard/zboard.php?id=' + LogicNormal.get_board_ids(url)[0])
        if len(datas) > 0 :
            if is_rss and ModelFeed.add_feed(datas) == 'success':
                logger.debug('success1')
            elif not is_rss and ModelFeed.add_feed(datas, False) == 'success':
                logger.debug('success2')
            else:
                logger.error('fail')
        else:
            logger.error('No items.')

    @staticmethod
    def process_check_rule():
        datas = ModelFeed.get_feeds_by_status(0)
        update_datas = []
        include_keywords = ModelSetting.get('include_keyword').split(',')
        exclude_keywords = ModelSetting.get('exclude_keyword').split(',')
        include_all = ModelSetting.get_bool('include_all')
        for data in datas:
            is_pass = True
            title = data.title
            if include_all :
                is_pass = False
            for include_keyword in include_keywords:
                include_keyword = include_keyword.strip()
                if len(include_keyword) > 0 and is_pass:
                    if '/' == include_keyword[0] and '/' == include_keyword[-1]:
                        regex_keyword = re.compile(include_keyword)
                        if len(regex_keyword.findall(title)) > 0 :
                            is_pass = False
                    else:
                        if include_keyword in title:
                            is_pass = False
            for exclude_keyword in exclude_keywords:
                exclude_keyword = exclude_keyword.strip()
                if len(exclude_keyword) > 0 and not is_pass:
                    if '/' == exclude_keyword[0] and '/' == exclude_keyword[-1]:
                        regex_keyword = re.compile(exclude_keyword)
                        if len(regex_keyword.findall(title)) > 0 :
                            is_pass = True
                    else:
                        if exclude_keyword in title:
                            is_pass = True
            if is_pass:
                data.status = -1
                update_datas.append(data)
            else:
                data.status = 1
                update_datas.append(data)
        ModelFeed.update_feed(update_datas)
    @staticmethod
    def get_message_by_format(data):
        message_format = ModelSetting.get('message_format')
        message_format = message_format.replace('{title}', data.title)
        message_format = message_format.replace('{link}', data.link)
        message_format = message_format.replace('{rss_id}', str(data.rss_id))
        message_format = message_format.replace('{description}', data.description if data.description else '')
        message_format = message_format.replace('{pub_date}', str(data.pub_date))
        message_format = message_format.replace('{author}', data.author)
        return message_format
    @staticmethod
    def process_check_alarm():
        datas = ModelFeed.get_feeds_by_status(1)
        update_datas = []
        for data in datas:
            message = LogicNormal.get_message_by_format(data)
            LogicNormal.process_send_alarm(message)
            data.status = 2
            update_datas.append(data)
        ModelFeed.update_feed(update_datas)
    @staticmethod
    def process_send_alarm(message):
        try:
            bot_id = ModelSetting.get('bot_id')
            if not bot_id:
                bot_id = 'bot_sjva_ppomppu'
            Notify.send_message(message, message_id=bot_id)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

