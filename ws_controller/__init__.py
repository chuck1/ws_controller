__version__ = '0.1b0'

import functools
import logging
import logging.config
import os
import sys
import shutil

import aiohttp
import aiohttp.web
import sys
import json
import requests_oauthlib
import ssl
import modconf
import argparse
import asyncio
import pickle
import base64
import subprocess

import async_patterns.protocol

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(__file__)

class PacketResponse:
    def __init__(self, response_to):
        self.response_to = response_to

class PacketRegister:
    def __init__(self, key, state, host):
        self.key = key
        self.state = state
        self.host = host
    async def __call__(self, proto):
        app = proto.app
        
        if key == app['conf'].secret_key:
            app['oauth'][self.state] = self.host

        proto.write(PacketResponse(self.message_id))

class ServerClientProtocol(async_patterns.protocol.Protocol):
    def __init__(self, loop, app):
        super(ServerClientProtocol, self).__init__(loop)
        self.app = app
        self.config_manager = app['config_manager']

class ConfigManager:
    def __init__(self):
        self.__configs = {}
    def register(self, id_, c):
        self.__configs[id_] = c
    def get(self, id_):
        return self.__configs.get(id_, None)

async def handler_google_oauth2_response(request):
    app = request.app
    conf = app['conf']
    
    state = request.GET['state']

    forward_host = app['oauth'][state]

    logger.debug('handler google response')

    #authorization_response = request.scheme + '://' + request.host + request.path_qs
    forward_response = request.scheme + '://' + forward_host + request.path_qs
    
    return aiohttp.web.HTTPFound(forward_response)

async def handler_google_oauth2_response1(request):
    app = request.app
    conf = app['conf']
    
    session = await aiohttp_session.get_session(request)
    logger.info('session={}'.format(session))
    
    authorization_response = request.scheme + '://' + request.host + request.path_qs
    
    #state = request.match_info.get('state')
    
    state = request.GET['state']
    
    (oauth, next_url) = request.app['oauth'][state]
    
    logger.debug('google response')
    logger.debug('state = {}'.format(state))
    logger.debug('next  = {}'.format(next_url))

    token = oauth.fetch_token(
            'https://accounts.google.com/o/oauth2/token',
            authorization_response=authorization_response,
            # Google specific extra parameter used for client
            # authentication
            client_secret=conf.google_oauth2.client_secret)

    r = oauth.get('https://www.googleapis.com/oauth2/v1/userinfo').json()

    session['oauth_token'] = token
    session['picture'] =  r['picture']

    userid = r['id']

    logger.info(str(r))

    response = aiohttp.web.HTTPFound(next_url)

    db_engine = request.app['db_engine']
    
    if (await ws_web_aiohttp.security.db_auth.check_credentials(db_engine, userid)):
        await aiohttp_security.remember(request, response, userid)
        return response

    return web.HTTPUnauthorized(
            body=b'Auth failed')

async def on_startup(app):
    # start socket server
    coro = app.loop.create_server(
            functools.partial(ServerClientProtocol, app.loop, app),
            'localhost', 
            app['conf'].PORT_SOCK)
    
    logger.debug('start server')
    server = await coro

async def setup_app(conf_mod, conf_dir, d, port=None):

    conf = modconf.import_class(conf_mod, 'Conf', ('DEVELOP' if d else 'DEPLOY', port, conf_dir), folder=conf_dir)

    logging.config.dictConfig(conf.LOGGING)

    #redis_pool = await aioredis.create_pool(('localhost', 6379))

    #app = aiohttp.web.Application(middlewares=[
    #    aiohttp_session.session_middleware(aiohttp_session.redis_storage.RedisStorage(redis_pool))])
    app = aiohttp.web.Application()
 
    app['conf'] = conf
   
    app.on_startup.append(on_startup)

    app['oauth'] = {}

    app['conf'] = modconf.import_class(conf_mod, 'Conf', ('DEVELOP' if d else 'DEPLOY', port))

    logging.config.dictConfig(app['conf'].LOGGING)
    
    # config manager
    app['config_manager'] = ConfigManager()
    app['config_manager'].register('import_class', modconf.import_class)

    # routes
    app.router.add_get('/google_oauth2_response', handler_google_oauth2_response)

    logger.debug('starting web app')

    return app

def runserver(args):
    loop = asyncio.get_event_loop()
    
    app = loop.run_until_complete(setup_app(args.conf_mod, args.conf_dir, args.d, args.p))

    aiohttp.web.run_app(
            app, 
            port=app['conf'].PORT, 
            ssl_context=app['conf'].SSL_CONTEXT)

def install(args):
    # copy systemd file
    shutil.copyfile(
            os.path.join(BASE_DIR, 'ws_controller.service'),
            os.path.join('/lib/systemd/system', 'ws_controller.service'))

    config_dir_dst = '/etc/ws_controller/conf'

    # make etc directory
    try:
        os.makedirs(config_dir_dst)
    except: pass
    
    # copy default config file
    shutil.copyfile(
            os.path.join(BASE_DIR, 'tests/conf/simple.py'),
            os.path.join(config_dir_dst, 'simple.py'))

    p = subprocess.Popen(('systemctl', 'daemon-reload'))
    p.communicate()
    p = subprocess.Popen(('systemctl', 'restart', 'ws_controller.service'))
    p.communicate()

def main(argv):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    def help_(args):
        parser.print_help()

    parser.set_defaults(func=help_)

    parser_runserver = subparsers.add_parser('runserver')
    parser_runserver.add_argument('--conf_dir')
    parser_runserver.add_argument('conf_mod')
    parser_runserver.add_argument('-d', action='store_true')
    parser_runserver.add_argument('-p', type=int, help='port')
    parser_runserver.set_defaults(func=runserver)

    parser_install = subparsers.add_parser('install')
    parser_install.set_defaults(func=install)

    args = parser.parse_args(argv[1:])
    args.func(args)


