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
try:
    from selenium import webdriver
except:
    import subprocess
    import sys
    subprocess.check_output([sys.executable, '-m', 'pip', 'install', 'selenium'], universal_newlines=True)
    from selenium import webdriver

# sjva 공용
from framework import app, db, scheduler, path_app_root
from framework.job import Job
from framework.util import Util
from framework.common.rss import RssUtil
from system.logic import SystemLogic
from tool_base import ToolBaseNotify
from system import SystemLogicSelenium

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelFeed
#########################################################

class LogicNormal(object):
    driver = None
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
            data = item.groupdict()
            data['link'] = 'https://www.ppomppu.co.kr/zboard/view.php?id=' + LogicNormal.get_board_ids(url)[0] + '&no=' + data['rss_id']
            if ModelSetting.get_bool('use_mall_link'):
                data['mall_link'] = LogicNormal.get_mall_link(data['link'])
                if ModelSetting.get_bool('use_bot_lp_url'):
                    data['mall_link'] = LogicNormal.convert_link_price(data['mall_link'])
            datas.append(data)
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
            if ModelSetting.get_bool('use_mall_link'):
                data['mall_link'] = LogicNormal.get_mall_link(data['link'])
                if ModelSetting.get_bool('use_bot_lp_url'):
                    data['mall_link'] = LogicNormal.convert_link_price(data['mall_link'])
            datas.append(data)
        if len(datas) == 0 :
            logger.error('Did not regex parsing.')
            logger.error(getdata.text)
        return datas
    @staticmethod
    def get_board_ids(url_text=None):
        if not url_text:
            url_text = str(ModelSetting.get('rss_url'))
        result = []
        if type(url_text) == str and ',' in url_text:
            url_arr = url_text.split(',')
            url_arr = [x.strip() for x in url_arr]
        elif type(url_text) == str:
            url_arr = []
            url_arr.append(url_text.strip())
        else:
            url_arr = url_text
        for url in url_arr:
            if 'id=' in url:
                result.append(url.split('id=')[1].split('&')[0])
            elif 'no=' in url:
                result.append(url.split('no=')[1].split('&')[0])
        return result
    @staticmethod
    def process_insert_feed():
        is_rss = ModelSetting.get_bool('use_rss')
        rss_url = str(ModelSetting.get('rss_url'))
        if ',' in rss_url:
            rss_url = rss_url.split(',')
            rss_url = [x.strip() for x in rss_url]
        else:
            rss_url = [rss_url.strip()]
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
        message_format = message_format.replace('{mall_link}', data.mall_link if data.mall_link else '')
        if type(message_format) != str:
            message_format = message_format.encode('utf-8')
        message_format = message_format.replace('\\n','\n')
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
            ToolBaseNotify.send_message(message, message_id=bot_id)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_lp_site_code(req):
        result = {'result':'-1'}
        try:
            if LogicNormal.driver is None:
                LogicNormal.driver = SystemLogicSelenium.create_driver()
            driver = LogicNormal.driver
            data = req.form
            lp_id = data['lp_id']
            lp_pw = data['lp_pw']
            try:
                try:
                    driver.get('https://ac.linkprice.net/login')
                    driver.implicitly_wait(10)
                    driver.find_element_by_xpath('//*[@id="content"]/div/form/div[1]/div[2]/div[1]/input').send_keys(lp_id)
                    driver.find_element_by_xpath('//*[@id="content"]/div/form/div[1]/div[2]/div[2]/input').send_keys(lp_pw)
                    driver.find_element_by_xpath('//*[@id="content"]/div/form/div[1]/div[2]/button').click()
                    driver.implicitly_wait(10)
                except:
                    pass
                driver.get('https://ac.linkprice.net/myinfo/commission')
                driver.find_element_by_xpath('//*[@id="content"]/div/div/div[1]/div/div[1]/div/span[1]').click()
                site_code = driver.find_element_by_xpath(
                    '//*[@id="content"]/div/div/div[1]/div/div[1]/div/div[2]/div/div[2]/div[2]/table/tr[3]/td[2]').text.strip()
                driver.implicitly_wait(10)
                result['result'] = site_code
            except Exception as exc:
                logger.error(driver.page_source)
                logger.error('Exception:%s', exc)
                logger.error(traceback.format_exc())
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return result
    @staticmethod
    def get_mall_link(pp_url):
        # ppomppu url => mall url
        sess = requests.session()
        if type(pp_url) != str:
            pp_url = pp_url.encode('utf-8')

        getdata = sess.get(pp_url.replace('http://','https://').replace(' ','').strip())
        title_text = getdata.text.split('<div class="bookmark-three-rung-menu-box">')[0]
        check_title_regex = re.compile(r'<div class=\"*wordfix\"*>.{2}\:\s\<a\shref=.+target=\"*_blank\"*>(?P<market_url>.+)</a>')
        matches = check_title_regex.search(str(title_text).decode('utf-8')) if check_title_regex and title_text else None
        market_url = matches.groupdict()['market_url'].split('&amp;')[0].split('&nbsp;')[0] if matches else None
        market_link = market_url.decode('utf-8') if market_url else None

        if not matches:
            logger.debug(getdata.url)
            market_link = None
        return market_link
    @staticmethod
    def convert_link_price(mall_link):
        a_id = ModelSetting.get('lp_site_code')
        result = mall_link
        if mall_link and len(mall_link) > 0 and a_id and len(a_id) > 0:
            import urllib
            encoded_url = urllib.quote(mall_link.encode('utf-8'))
            url = 'http://api.linkprice.com/ci/service/custom_link_xml?a_id={a_id}&url={encoded_url}&mode=json'.format(a_id=a_id,encoded_url=encoded_url)
            sess = requests.session()
            json_result = sess.get(url).json()
            if 'S' in json_result['result'].upper():
                result = json_result['url']
        return result


