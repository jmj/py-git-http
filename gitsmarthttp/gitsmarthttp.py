#from pudb import set_trace; set_trace()

from gevent import monkey
monkey.patch_all()


from bottle import run, request, response, static_file
from bottle import Bottle

from utils import clense_path, mk_pkt_line, hdr_nocache, Git

import errno
import logging as log
log.basicConfig(level=log.DEBUG)


app = Bottle()

repo_base = '/tmp/repo'

# TODO: clense_path needs to check for None
@clense_path
@app.get('/<repo>/info/refs')
def get_refs(repo):

    log.debug('service={0}'.format(request.query['service']))


    git = Git('{0}/{1}'.format(repo_base, repo))


    hdr_nocache(response)
    response.set_header('X-Powered-By', 'Me')

    yield mk_pkt_line('# service={0}\n'.format(request.query['service']))
    yield '0000'

    response.set_header('Content-Type',
            'application/x-{0}-advertisement'.format(request.query['service']))


    if request.query['service'] == 'git-upload-pack':
        p = git.upload_pack('--stateless-rpc', '--advertise-refs')
    elif request.query['service'] == 'git-receive-pack':
        p = git.receive_pack('--stateless-rpc', '--advertise-refs')

    p.wait()
    log.debug('reading')
    while True:
        try:
            l = p.stdout.read(8192)
            if l == '':
                break
            log.debug(l)
            yield l.strip()
        except OSError as e:
            if e.errno == errno.EBADF:
                break
            else:
                raise

@clense_path
@app.get('/<repo>/HEAD')
def get_head(repo):
    return static_file('HEAD', root='{0}/{1}'.format(repo_base, repo))

@clense_path
@app.post('/<repo>/<op:re:git-(upload|receive)-pack>')
def rpc_op(repo, op):
    log.debug('rpc_op: {0}'.format(op))
    git = Git('{0}/{1}'.format(repo_base, repo))

    response.set_header('Content-type',
            'application/x-{0}-result'.format(op))
    hdr_nocache(response)

    if op == 'git-upload-pack':
        p = git.upload_pack('--stateless-rpc')
    elif op == 'git-receive-pack':
        p = git.receive_pack('--stateless-rpc')

    log.debug('starting RPC: {0}'.format(request.body))
    p.stdin.write(request.body.read())
    log.debug('WTF')
    p.wait()
    log.debug('Git done')

    log.debug('getting data')
    while True:
        try:
            l = p.stdout.read(8192)
            if l == '':
                break
            log.debug(l)
            yield l
        except OSError as e:
            if e.errno == errno.EBADF:
                break
            else:
                raise

@app.route('/<foo:path>')
def index(foo=None):
    log.debug('requested: {0} {1}'.format(request.method, foo))
    log.debug('\theaders:')
    for h,v in request.headers.items():
        log.debug('\t\t{0}:{1}'.format(h, v))
    log.debug('\tArgs:')
    for h,v in request.query.items():
        log.debug('\t\t{0}:{1}'.format(h, v))

    return 'foo'



if __name__ == '__main__':
    run(app, host='0.0.0.0', port=9000, server='gevent')
