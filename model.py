# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import json
import datetime
# third-party
try:
    from sqlalchemy import or_, and_, func, not_, desc
    from sqlalchemy.orm import backref
except:
    import subprocess
    import sys
    subprocess.check_output([sys.executable, '-m', 'pip', 'install', 'sqlalchemy'], universal_newlines=True)
    from sqlalchemy import or_, and_, func, not_, desc
    from sqlalchemy.orm import backref
# sjva 공용
from framework import db, app, path_app_root
from framework.util import Util

# 패키지

from .plugin import logger, package_name

#########################################################

app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (
    os.path.join(path_app_root, 'data', 'db', '%s.db' % package_name))


class ModelSetting(db.Model):
    __tablename__ = '%s_setting' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def get(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value.strip()
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_int(key):
        try:
            return int(ModelSetting.get(key))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def get_bool(key):
        try:
            return (ModelSetting.get(key) == 'True')
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def set(key, value):
        try:
            item = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
            if item is not None:
                item.value = value.strip()
                db.session.commit()
            else:
                db.session.add(ModelSetting(key, value.strip()))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def to_dict():
        try:
            return Util.db_list_to_dict(db.session.query(ModelSetting).all())
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                logger.debug('Key:%s Value:%s', key, value)
                if key in ['scheduler', 'is_running', 'global_scheduler_sub']:
                    continue
                if key == 'default_username' and value.startswith('==='):
                    continue
                entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                entity.value = value
            db.session.commit()
            return True
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            logger.debug('Error Key:%s Value:%s', key, value)
            return False

    @staticmethod
    def get_list(key):
        try:
            value = ModelSetting.get(key)
            values = [x.strip().replace(' ', '').strip() for x in value.replace('\n', '|').split('|')]
            values = Util.get_list_except_empty(values)
            return values
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            logger.error('Error Key:%s Value:%s', key, value)

class ModelFeed(db.Model):
    __tablename__ = '%s_feed' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name
    rss_id = db.Column(db.Integer, primary_key=True)
    created_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    pub_date = db.Column(db.DateTime)
    title = db.Column(db.String)
    author = db.Column(db.String)
    description = db.Column(db.String)
    link = db.Column(db.String)
    status = db.Column(db.Integer) # -1 : 통과, 0 : 최초, 1: 알람준비, 2: 알람완료
    def __init__(self):
        self.created_time = datetime.datetime.now()
        self.update_time = datetime.datetime.now()
        self.status = 0
    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        ret['update_time'] = self.created_time.strftime('%m-%d %H:%M:%S')
        ret['pub_date'] = self.created_time.strftime('%m-%d %H:%M:%S')
        return ret

    @staticmethod
    def get_feed(data):
        try:
            if type(data) == dict:
                query = db.session.query(ModelFeed).filter(ModelFeed.rss_id == data['rss_id'])
            else:
                query = db.session.query(ModelFeed).filter(ModelFeed.rss_id == data.rss_id)
            return query.all()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return []
    @staticmethod
    def add_feed(datas, is_rss = True):
        try:
            for data in datas:
                entity = ModelFeed.get_feed(data)
                if entity is None or len(entity) == 0:
                    r = ModelFeed()
                    if is_rss:
                        r.pub_date = datetime.datetime.strptime(data['pub_date'], '%b, %d %Y %H:%M:%S %Z')
                        r.description = data['description'].replace('&nbsp;', ' ')
                    else:
                        if ':' in data['pub_date']:
                            r.pub_date = datetime.datetime.strptime(data['pub_date'], '%H:%M:%S')
                        elif '/' in data['pub_date']:
                            r.pub_date = datetime.datetime.strptime(data['pub_date'], '%Y/%m/%d')
                        else:
                            r.pub_date = datetime.datetime.strptime(data['pub_date'], '%Y:%m:%d')
                    r.rss_id = int(data['rss_id'])
                    r.title = data['title']
                    r.author = data['author']
                    r.link = data['link'].replace('&amp;','&')
                    db.session.add(r)
                    db.session.commit()
            return 'success'

        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return 'fail'
    @staticmethod
    def get_feeds_by_status(status):
        try:
            query = db.session.query(ModelFeed).filter(ModelFeed.status == int(status))
            return query.all()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return []
    @staticmethod
    def update_feed(datas):
        try:
            for data in datas:
                entity = ModelFeed.get_feed(data)
                if entity and len(entity) > 0:
                    if type(data) == dict:
                        r = db.session.query(ModelFeed).filter(ModelFeed.rss_id==data['rss_id']).first()
                        r.status = data['status']
                    else:
                        r = db.session.query(ModelFeed).filter(ModelFeed.rss_id==data.rss_id).first()
                        r.status = data.status
                    r.update_time = datetime.datetime.now()
                    db.session.commit()

            return 'success'
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return 'fail'

    @staticmethod
    def web_list(req):
        try:
            ret = {}
            page_size = 15
            page = int(req.form['page']) if 'page' in req.form else 1
            search = req.form['search_word'] if 'search_word' in req.form else ''
            option = req.form['option']
            order = req.form['order'] if 'order' in req.form else 'desc'
            query = ModelFeed.make_query(search=search, option=option, order=order)
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = Util.get_paging_info(count, page, page_size)
            return ret
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return {}

    @staticmethod
    def remove(rss_id):
        try:
            db.session.query(ModelFeed).filter_by(rss_id=rss_id).delete()
            db.session.commit()
            return 'success'
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return 'fail'

    @staticmethod
    def make_query(search='', option='all', order='desc'):
        query = db.session.query(ModelFeed)
        if search is not None and search != '':
            if search.find('|') != -1:
                tmp = search.split('|')
                conditions = []
                for tt in tmp:
                    if tt != '':
                        conditions.append(ModelFeed.title.like('%' + tt.strip() + '%'))
                query = query.filter(or_(*conditions))
            elif search.find(',') != -1:
                tmp = search.split(',')
                for tt in tmp:
                    if tt != '':
                        query = query.filter(ModelFeed.title.like('%' + tt.strip() + '%'))
            else:
                query = query.filter(
                    or_(ModelFeed.title.like('%' + search + '%'), ModelFeed.description.like('%' + search + '%'),
                        ModelFeed.author.like('%' + search + '%')))
        if option == 'wait':
            query = query.filter(ModelFeed.status == 0)
        elif option == 'true':
            query = query.filter(ModelFeed.status == 2)
        elif option == 'false':
            query = query.filter(ModelFeed.status == -1)

        if order == 'desc':
            query = query.order_by(desc(ModelFeed.created_time))
        else:
            query = query.order_by(ModelFeed.created_time)
        return query