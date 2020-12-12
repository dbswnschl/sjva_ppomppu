# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
from datetime import datetime
import re

# third-party

# sjva 공용
from framework import app, db, scheduler, path_app_root
from framework.job import Job
from framework.util import Util
from framework.common.rss import RssUtil
from system.logic import SystemLogic


# 패키지
from .plugin import logger, package_name
from .model import ModelSetting
#########################################################

class LogicNormal(object):
    @staticmethod
    def scheduler_function():
        try:
            logger.debug('scheduler_function')
            LogicNormal.process_insert_feed()
            LogicNormal.process_download_mode()

        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
