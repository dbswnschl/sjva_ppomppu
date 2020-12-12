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
from framework import check_api, socketio

# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
from .logic import Logic
from .logic_normal import LogicNormal
from .model import ModelSetting

#########################################################
# 플러그인 공용
#########################################################
blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
menu = {
    'main' : [package_name, u'뽐뿌 알리미'],
    'sub' : [
        ['setting', u'설정'], ['log', u'로그']
    ],
    'category' : 'service'
}

plugin_info = {
    'version' : '0.1.0.0',
    'name' : package_name,
    'category_name' : 'service',
    'developer' : 'dbswnschl',
    'description' : u'뽐부 알리미',
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
    try:
        arg = {'package_name': package_name}

        if sub == 'setting':
            arg.update(ModelSetting.to_dict())
            arg['package_list'] = LogicNormal.get_youtube_dl_package()
            arg['youtube_dl_version'] = LogicNormal.get_youtube_dl_version()
            arg['DEFAULT_FILENAME'] = LogicNormal.get_default_filename()
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
# socketio
#########################################################
def socketio_emit(cmd, data):
    socketio.emit(cmd, LogicNormal.get_data(data), namespace='/%s' % package_name, broadcast=True)