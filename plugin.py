# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import subprocess
import json

# third-party
from flask import Blueprint, request, render_template, redirect, jsonify, abort
from flask_login import login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, check_api
from framework.util import Util

# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
from .logic import Logic
from .logic_normal import LogicNormal
from .model import ModelSetting, ModelFeed

#########################################################
# 플러그인 공용
#########################################################
blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
menu = {
    'main' : [package_name, u'뽐뿌 알리미'],
    'sub' : [
        ['setting', u'설정'], ['list', u'목록'], ['log', u'로그']
    ],
    'category' : 'service'
}

plugin_info = {
    'version' : '0.1.0.0',
    'name' : package_name,
    'category_name' : 'service',
    'developer' : 'dbswnschl',
    'description' : u'뽐뿌 알리미',
    'home' : 'https://github.com/dbswnschl/' + package_name,
    'more' : '',
}

def plugin_load():
    logger.info('%s plugin load' % package_name)
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()
#########################################################
# WEB Menu
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/list' % package_name)

@blueprint.route('/<sub>')
@login_required
def first_menu(sub):
    arg = ModelSetting.to_dict()
    arg['package_name'] = package_name
    try:
        if sub == 'setting':
            arg['scheduler'] = str(scheduler.is_include(package_name))
            arg['is_running'] = str(scheduler.is_running(package_name))
            return render_template('%s_%s.html' % (package_name, sub), arg=arg)

        elif sub == 'list':
            return render_template('%s_%s.html' % (package_name, sub), arg=arg)

        elif sub == 'log':
            return render_template('log.html', package=package_name)
    except Exception as e:
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    try:
        if sub == 'setting_save':
            ret = ModelSetting.setting_save(request)
            return jsonify(ret)
        elif sub == 'scheduler':
            go = request.form['scheduler']
            logger.debug('scheduler :%s', go)
            if go == 'true':
                Logic.scheduler_start()
            else:
                Logic.scheduler_stop()
            return jsonify(go)
        elif sub == 'one_execute':
            ret = Logic.one_execute()
            return jsonify(ret)
        elif sub == 'reset_db':
            ret = Logic.reset_db()
            return jsonify(ret)
        elif sub == 'web_list':
            ret = ModelFeed.web_list(request)
            return jsonify(ret)
    except Exception as e:
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())