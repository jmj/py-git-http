import bottle
from bottle import route, run, static_file, request, response

import os
import subprocess
import logging

base = '/tmp/repo'
git = '/usr/bin/git'

pack_ops = {
    'git-upload-pack': 'upload-pack',
    'git-receive-pack': 'receive-pack',
}

bottle.debug(True)

@route('/<repo>/objects/<obj_path:re:[0-9a-f]{2}/[0-9a-f]{38}$>', method='GET')
def get_objects(repo=None, obj_path=None):
    logging.warning('get_objects(%s, %s)' % (repo, obj_path))
    logging.warning('get_objects(): %s/%s/objects/%s' % (base, repo, obj_path))
    response.content_type = 'application/x-git-loose-object'
    return static_file(obj_path, root='/%s/%s/objects' % (base, repo))

@route('/<repo>/<op:re:git-upload-pack|git-receive-pack>', method='POST')
def service_call(repo=None, op=None):
    pass

@route('/<repo>/info/refs', method='GET')
def get_refs_info(repo=None):
    response.content_type = 'application/x-%s-advertisement' % (
        request.GET.get('service', 'git-unknown'))
    ret = '''001e# service=%s\n0000%s\n''' % (
        request.GET.get('service', 'git-unknown'),
        subprocess.check_output([git,
            pack_ops[request.GET.get('service', None)],
            '--stateless-rpc', '--advertise-refs', '%s/%s' % (base, repo)]))

    ## This works, but it's dumb mode.  Need above for smart
    #with file('%s/%s/info/refs' % (base, repo)) as git_file:
    #    ret = ''.join(git_file.readlines())
    return ret


@route('/<repo>/<fpath:re:^packs$>', method='GET')
def get_pack_info(repo=None, fpath=None):
    with file('/tmp/b.out', 'a') as f:
        f.write('packs\n')


def wtf(repo=None, fpath=None):
    with file('/tmp/b.out', 'a') as f:
        f.write('wtf()\n')

@route('/<repo>/<fpath:re:HEAD>', method='GET')
@route('/<repo>/<fpath:re:^objects/info/[^/]*$', method='GET')
def text_file(repo=None, fpath=None):
        response.content_type = 'text/plain'
        return static_file(fpath, root='%s/%s' % (base, repo))




run(host='localhost', port=8080)
