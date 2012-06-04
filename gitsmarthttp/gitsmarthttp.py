#!/usr/bin/env python

import subprocess
import tempfile
import wsgiref
from datetime import datetime
import logging
log = logging.getLogger(__name__)

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.wsgi import WSGIApplication
from tornado.options import parse_command_line

#AppType = WSGIApplication
AppType = Application


base = '/tmp/repo'
git = '/usr/local/bin/git'
#git = '/usr/bin/git'
pack_ops = {
    'git-upload-pack': 'upload-pack',
    'git-receive-pack': 'receive-pack',
}

def pkt_flush():
    return '0000'

def mk_pkt_line(line):
    return '{:04x}{}'.format(len(line), line)

class rpc_service(RequestHandler):
    def post(self, repo, op):
        log.debug('rpc_service')

        indata = self.request.body

        self.set_header('Cache-Control', 'no-cache, max-age=0, must-revalidate')
        self.set_header('Pragma', 'no-cache')
        self.set_header('Expires', 'Fri, 01 Jan 1980 00:00:00 GMT')
        self.set_header('Date',
                datetime.utcnow().strftime('%a, %d %b %G %T GMT'))

        self.set_header('Content-Type', 'application/x-%s-result' % (op))

        o_fn, o_name = tempfile.mkstemp(dir='/tmp')

        proc = subprocess.Popen([git, pack_ops[op], '--stateless-rpc',
            '%s/%s' % (base, repo)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        proc.stdin.write(indata)
        proc.wait()

        while True:
            outdata = proc.stdout.read(8192)
            if outdata == '':
                return
            self.write(outdata)
            self.flush()

class get_objects(RequestHandler):
    def get(self):
        log.debug('get_objects')

class get_refs_info(RequestHandler):
    def get(self, repo):
        log.debug('get_refs_info')

        self.set_header('Content-type', 'application/x-%s-advertisement' % (
            self.get_argument('service')))

        ret = mk_pkt_line('# service=%s\n%s' % (
            self.get_argument('service'), pkt_flush()))

        ret = '%s%s\n' % (ret, subprocess.check_output([git,
            pack_ops[self.get_argument('service')],
            '--stateless-rpc', '--advertise-refs', '%s/%s' % (base, repo)]))
        self.write(ret.strip())

class get_pack_info(RequestHandler):
    def get(self):
        log.debug('get_pack_info')

class text_file(RequestHandler):
    def get(self, repo, path):
        log.debug('text_file: %s'% (path))

        self.set_header('Content-type', 'text/plain')
        with open('%s/%s/%s' % (base, repo, path)) as f:
            self.write(f.read())

application = AppType([
    (r'/(.*?)/(git-upload-pack|git-receive-pack)', rpc_service),
    (r'/(.*?)/objects/([0-9a-f]{2}/[0-9a-f]{38}$)', get_objects),
    (r'/(.*?)/info/refs', get_refs_info),
    (r'/(.*?)/packs', get_pack_info),
    (r'/(.*?)/(HEAD)', text_file),
    (r'/(.*?)/(objects/info/[^/]*$)', text_file),
    ], debug=True)

if __name__ == '__main__':
    parse_command_line()
    if isinstance(application, WSGIApplication):
        server = wsgiref.simple_server.make_server('', 8888, application)
        server.serve_forever()
    else:
        application.listen(8080)
        IOLoop.instance().start()
