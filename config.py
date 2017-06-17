import os

class BaseConfig(object):
    DEBUG = True
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600 # session life time second
    SECRET_KEY = os.urandom(24)
    CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = '' # config database uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_REGISTERABLE = True
