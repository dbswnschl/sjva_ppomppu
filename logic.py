# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import time
import threading

# third-party

# sjva 공용
from framework import db, scheduler, path_app_root
from framework.job import Job
from framework.util import Util

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting
from .logic_normal import LogicNormal
#########################################################

class Logic(object):
    db_default = {
        'db_version': '2',
        'auto_start': 'False',
        'interval': '1',
        'allow_duplicate': 'True',
        'rss_url' : 'http://www.ppomppu.co.kr/rss.php?id=ppomppu',
        'include_keyword' : '',
        'exclude_keyword' : '',
        'include_all': 'True',
        'message_format': '[{title}] : {link}\n{mall_link}',
        'bot_id' : 'bot_sjva_ppomppu',
        'use_rss' : 'True',
        'use_mall_link':'True',
        'lp_id' : '',
        'lp_pw' : '',
        'lp_site_code' : '',
        'use_bot_lp_url': 'False'
    }

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
            Logic.migration()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_load():
        try:
            Logic.db_init()
            if ModelSetting.get_bool('auto_start'):
                Logic.scheduler_start()
            from .plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_unload():
        pass

    @staticmethod
    def scheduler_start():
        try:
            logger.debug('%s scheduler_start' % package_name)
            job = Job(package_name, package_name, ModelSetting.get('interval'), Logic.scheduler_function, u"뽐부 알리미",
                      False)
            scheduler.add_job_instance(job)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def scheduler_stop():
        try:
            logger.debug('%s scheduler_stop' % package_name)
            scheduler.remove_job(package_name)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def scheduler_function():
        try:
            LogicNormal.scheduler_function()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def reset_db():
        try:
            from .model import ModelFeed
            db.session.query(ModelFeed).delete()
            db.session.commit()
            return True
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def one_execute():
        try:
            if scheduler.is_include(package_name):
                if scheduler.is_running(package_name):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(package_name)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    Logic.scheduler_function()

                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret

    @staticmethod
    def migration():
        try:
            if ModelSetting.get('db_version') == '1':
                import sqlite3
                db_file = os.path.join(path_app_root, 'data', 'db', '%s.db' % package_name)
                connection = sqlite3.connect(db_file)
                cursor = connection.cursor()
                query = 'ALTER TABLE %s_feed ADD mall_link VARCHAR' % (package_name)
                cursor.execute(query)
                connection.close()
                ModelSetting.set('db_version', '2')
                db.session.flush()
            pass
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
