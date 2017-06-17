import markdown
import random
import string
import time
from datetime import datetime
from flask import Flask, render_template, request, \
    url_for, redirect, session, Markup, current_app
from flask.ext.session import Session
from flask_paginate import Pagination, get_page_args
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey

app = Flask(__name__)
app.config.from_object('config.BaseConfig')
Session(app)
db = SQLAlchemy(app)


class Jobs(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    postdate = db.Column(db.DATE)
    issuesid = db.Column(db.Integer)

    def __init__(self, title, content, postdate, issuesid):
        self.title = title
        self.content = content
        self.postdate = postdate
        self.issuesid = issuesid

    def __repr__(self):
        return '<url {}>' . format(self.title)


class Links(db.Model):
    __tablename__ = 'links'

    short_url = db.Column(db.String(6), primary_key=True, unique=True)
    long_url = db.Column(db.String(100))
    created = db.Column(db.Integer)

    def __init__(self, short_url, long_url, created):
        self.short_url = short_url
        self.long_url = long_url
        self.created = created

    def __repr__(self):
        return '<shorturl {}>'.format(self.short_url)


class Track(db.Model):
    __tablename__ = 'track'
    ID = db.Column(db.Integer, primary_key=True, unique=True)
    SHORTURL = db.Column(db.String(15), ForeignKey('links.short_url'))
    REQUEST_TIME = db.Column(db.Integer)
    REMOTE_ADDR = db.Column(db.String(15))
    SERVER_PROTOCOL = db.Column(db.String(10))
    HTTPS = db.Column(db.String(45))
    HTTP_USER_AGENT = db.Column(db.String(250))
    HTTP_REFERRER = db.Column(db.String(45))

    def __init__(self, SHORTURL, REQUEST_TIME, REMOTE_ADDR, SERVER_PROTOCOL,
                 HTTPS, HTTP_USER_AGENT, HTTP_REFERRER):
        self.SHORTURL = SHORTURL
        self.REQUEST_TIME = REQUEST_TIME
        self.REMOTE_ADDR = REMOTE_ADDR
        self.SERVER_PROTOCOL = SERVER_PROTOCOL
        self.HTTPS = HTTPS
        self.HTTP_USER_AGENT = HTTP_USER_AGENT
        self.HTTP_REFERRER = HTTP_REFERRER

    def __repr__(self):
        return '<track {}>'.format(self.SHORTURL)


@app.route('/<string:short_url>')
def redirect_url(short_url):
    url = Links.query.filter_by(short_url=short_url).first()
    if url:
        redirect_url = url.long_url
        store_data(short_url)
    else:
        redirect_url = 'shorten'
    return redirect(redirect_url, code=302)


@app.route('/')
@app.route('/shorten')
def shorten():
    query = 'select * from links order by created desc'\
        ' fetch first 10 rows only'
    links = db.engine.execute(query)
    return render_template('shorten.html',
                           root_url=request.url_root,
                           links=list(links),
                           response=session.get('response'),
                           state=session.get('state'),
                           code=generate_code())


@app.route('/addlink', methods=['POST'])
def add_link():
    if request.method == 'POST':
        url = request.form['url']
        short_url = request.form['code']
        created = int(time.time())
        link = Links(short_url, url, created)
        try:
            db.session.add(link)
            db.session.commit()
            session['state'] = 'errorfree'
            session['response'] = request.url_root + short_url
        except:
            session['state'] = 'error'
            session['response'] = 'Could not assign "' \
                + short_url + '" to "' + url + '".'
        return redirect(url_for('shorten'))


@app.route('/career/')
def career(page=1):
    query = 'select count(*) from jobs'
    job = db.engine.execute(query)
    total = job.fetchone()[0]

    page, per_page, offset = get_page_args()
    sql = 'SELECT title, postdate, issuesid FROM jobs '\
          'ORDER BY postdate DESC LIMIT {} OFFSET {}'\
          .format(per_page, offset)
    data = db.engine.execute(sql)
    alljobs = list(data)
    getdate = [datetime.strptime(str(d[1]), '%Y-%m-%d') for d in alljobs]
    postdates = [d.strftime('%d-%m-%Y') for d in getdate]
    alldata = zip(alljobs, postdates)
    pagination = get_pagination(page=page,
                                per_page=per_page,
                                total=total,
                                record_name='jobs',
                                format_total=True,
                                format_number=True,
                                )
    return render_template('show-all.html',
                           jobs=alldata,
                           page=page,
                           per_page=per_page,
                           pagination=pagination)


@app.route('/career/detail/<string:id>')
def career_detail(id=None):
    query = 'select * from jobs where issuesid = {0}'.format(id)
    job = db.engine.execute(query)
    row = job.fetchone()
    content = Markup(markdown.markdown(row['content']))
    postdate = datetime.strptime(str(row['postdate']), '%Y-%m-%d')
    return render_template('detail.html',
                           job=row,
                           date='{:%d-%m-%Y}'.format(postdate),
                           content=content)


def generate_code():
    while True:
        rand = random.choices(string.ascii_lowercase +
                              string.ascii_uppercase +
                              string.digits, k=6)
        code = ''.join(rand)
        sql = "select count(*) from links where short_url = '{0}'".format(code)
        data = db.engine.execute(sql)
        result = data.fetchone()[0]
        if result == 0 :
            return code
            break


def store_data(short_url):
    request_time = int(time.time())
    remote_addr = request.environ['REMOTE_ADDR']
    server_protocol = request.environ['SERVER_PROTOCOL']
    https = ''
    http_user_agent = request.environ['HTTP_USER_AGENT']
    http_referer = request.headers.get('Referer')
    tracking = Track(short_url, request_time, remote_addr, server_protocol,
                     https, http_user_agent, http_referer)
    db.session.add(tracking)
    db.session.commit()


def get_css_framework():
    return current_app.config.get('CSS_FRAMEWORK', 'bootstrap3')


def get_link_size():
    return current_app.config.get('LINK_SIZE', 'sm')


def show_single_page_or_not():
    return current_app.config.get('SHOW_SINGLE_PAGE', False)


def get_pagination(**kwargs):
    kwargs.setdefault('record_name', 'records')
    return Pagination(css_framework=get_css_framework(),
                      link_size=get_link_size(),
                      show_single_page=show_single_page_or_not(),
                      **kwargs
                      )


if __name__ == '__main__':
    app.run()
