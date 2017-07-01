import enum
import os
import modconf
import ssl

class Conf(object):
    class Mode(enum.Enum):
        DEVELOP=1
        DEPLOY=2
        
        @classmethod
        def from_string(cls, s):
            if s == 'DEVELOP':
                return cls.DEVELOP
            elif s == 'DEPLOY':
                return cls.DEPLOY
            else:
                raise Exception('invalid mode: {}'.format(s))
    
   
    @classmethod
    def prepare(cls, mode_s, port=None, conf_dir=None, console=False):
        cls.MODE = cls.Mode.from_string(mode_s)

        cls.SCHEME = 'https'
        cls.SCHEME_WS = 'wss'
        cls.PORT = 8443
    
        cls.url = 'www.charlesrymal.com'
    
        cls.certfile = '/etc/letsencrypt/live/www.charlesrymal.com/fullchain.pem'
        cls.keyfile = '/etc/letsencrypt/live/www.charlesrymal.com/privkey.pem'
        
        try:
            cls.SSL_CONTEXT = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            cls.SSL_CONTEXT.load_cert_chain(cls.certfile, cls.keyfile)
        except:
            cls.SSL_CONTEXT = None
    
        cls.STATIC_DIR = '/var/www/ws_controller/static'

        if cls.MODE == cls.Mode.DEVELOP:
            cls.secret_key = 'secret'
            cls.PORT_SOCK = 10007
            cls.LOG_FILE = 'dev/log/ws_controller/debug.log'
        elif cls.MODE == cls.Mode.DEPLOY:
            cls.PORT_SOCK = 10008
            cls.LOG_FILE = '/var/log/ws_controller/debug.log'
        
        try:
            os.makedirs(os.path.dirname(cls.LOG_FILE))
        except: pass
        
        cls.LOGGING = {
                'version': 1,
                'disable_existing_loggers': False,
                'handlers': {
                    'file': {
                        'level': 'DEBUG',
                        'class': 'logging.FileHandler',
                        'filename': cls.LOG_FILE,
                        'formatter': 'basic'
                        },
                    'console':{
                        'level':'DEBUG',
                        'class':'logging.StreamHandler',
                        'formatter': 'basic'
                        },
                    },
                'loggers':{
                    '__main__': {
                        'handlers': ['file'],
                        'level': 'DEBUG',
                        'propagate': True,
                        },
                    'ws_storage': {
                        'handlers': ['file'],
                        'level': 'DEBUG',
                        'propagate': True,
                        },
                    'ws_sheets_server': {
                        'handlers': ['file'],
                        'level': 'DEBUG',
                        'propagate': True,
                        },
                    'ws_web_aiohttp': {
                        'handlers': ['file'],
                        'level': 'DEBUG',
                        'propagate': True,
                        },
                    },
                'formatters': {
                    "basic":{
                        "format":"%(asctime)s %(module)12s %(levelname)s %(message)s"
                        }
                    }
                }

        if console:
            cls.log_console()

        if port is not None:
            cls.PORT = port
        
        cls.CONF_DIR = conf_dir or '/etc/ws_controller/conf/'
        
        #cls.google_oauth2 = modconf.import_conf('google_oauth2', cls.CONF_DIR)

        #cls.PG = modconf.import_conf('postgresql', cls.CONF_DIR)

        #cls.ws_sheets_server = modconf.import_class('ws_sheets_server.tests.conf.simple', 'Conf', (mode_s,))

    @classmethod
    def url_root(cls):
        return '{}://localhost:{}'.format(cls.SCHEME, cls.PORT)

    @classmethod
    def ws_root(cls):
        return '{}://localhost:{}'.format(cls.SCHEME_WS, cls.PORT)

    @classmethod
    def log_console(cls):
        for l in cls.LOGGING['loggers'].values():
            l['handlers'] = ['console']

