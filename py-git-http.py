#!/usr/bin/env python

import subprocess
from logging import warning

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler

base = '/tmp/repo'
git = '/usr/local/bin/git'
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
        warning('rpc_service')

        indata = self.request.body
        warning(indata)

        self.set_header('Content-Type', 'application/x-%s-result' % (op))
        self.set_header('Pragma', 'no-cache')
        self.set_header('Cache-Control', 'no-cache, max-age=0, must-revalidate')

        proc = subprocess.Popen(' '.join([git, pack_ops[op], '--stateless-rpc',
            '%s/%s' % (base, repo), ' | /usr/bin/tee /tmp/g.out']),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        proc.stdin.write(indata)

        warning('Sending data:')
        while True:
            outdata = proc.stdout.read(8192)
            if outdata == '':
                warning('Done')
                return
            warning('---->%s' % (outdata))
            self.write(outdata)
            self.flush()
#        self.write(bytes('0008NAK\n'))

class get_objects(RequestHandler):
    def get(self):
        warning('get_objects')

class get_refs_info(RequestHandler):
    def get(self, repo):
        warning('get_refs_info: %s'% (repo))
        warning(self.get_argument('service'))
        self.set_header('Content-type', 'application/x-%s-advertisement' % (
            self.get_argument('service')))

        ret = mk_pkt_line('# service=%s\n%s' % (
            self.get_argument('service'), pkt_flush()))

        ret = '%s%s\n' % (ret, subprocess.check_output([git,
            pack_ops[self.get_argument('service')],
            '--stateless-rpc', '--advertise-refs', '%s/%s' % (base, repo)]))

        self.write(ret)

class get_pack_info(RequestHandler):
    def get(self):
        warning('get_pack_info')

class text_file(RequestHandler):
    def get(self, repo, path):
        warning('text_file: %s'% (path))
        self.set_header('Content-type', 'text/plain')
        with open('%s/%s/%s' % (base, repo, path)) as f:
            self.write(f.read())

application = (Application([
    (r'/(.*?)/(git-upload-pack|git-receive-pack)', rpc_service),
    (r'/(.*?)/objects/([0-9a-f]{2}/[0-9a-f]{38}$)', get_objects),
    (r'/(.*?)/info/refs', get_refs_info),
    (r'/(.*?)/packs', get_pack_info),
    (r'/(.*?)/(HEAD)', text_file),
    (r'/(.*?)/(objects/info/[^/]*$)', text_file),
    ]))

if __name__ == '__main__':
    application.listen(8080)
    IOLoop.instance().start()
