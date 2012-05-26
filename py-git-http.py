import bottle
from bottle import route, run, static_file, request, response

import os
import subprocess

base = '/tmp/repo'
git = '/usr/local/bin/git'

pack_ops = {
    'git-upload-pack': 'upload-pack',
}

bottle.debug(True)

@route('/<repo>/info/refs', method='GET')
def get_refs_info(repo=None):
    response.content_type = 'application/x-%s-advertisement' % (
        request.GET.get('service', 'git-unknown'))
    ret = '# service=%s\n%s' % (request.GET.get('service', 'git-unknown'),
        subprocess.check_output([git,
            pack_ops[request.GET.get('service', None)],
            '--stateless-rpc', '--advertise-refs', '%s/%s' % (base, repo)]))
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
    if not os.path.isdir('%s/%s' % (base, repo)):
        with file('/tmp/b.out', 'a') as f:
            f.write('text_file(): WTF')
        return
    else:
        response.content_type = 'text/plain'
        with file('%s/%s/%s' % (base, repo, fpath)) as git_file:
            ret = ''.join(git_file.readlines())

        return ret




run(host='localhost', port=8080)
