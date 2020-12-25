class Config(object):
    DEBUG = True  # some Flask specific configs
    CACHE_TYPE = "simple"  # Flask-Caching related configs
    CACHE_DEFAULT_TIMEOUT = 0
    SQLALCHEMY_DATABASE_URI = 'sqlite:///lattice.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
