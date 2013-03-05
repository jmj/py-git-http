from os import path
from datetime import datetime

from bottle import abort

import subprocess

import logging
log = logging.getLogger(__name__)
#log.basicConfig(level=log.DEBUG)

repo_base='/tmp/repo'

## Decorator to make sure the repo is valid.
def clense_path(fn):
    def wrapped(self, repo, *args, **kw):
        log.debug('Cleaning path: {}/{}'.format(repo_base, repo))
        ## deref . and .., etc
        repo_path = path.abspath('{}/{}'.format(repo_base, repo))

        if path.exists(repo_path) and repo_path.startswith(repo_base):
            return fn(self, repo, *args, **kw)
        abort(403, 'Unauthorized')
        return
    return wrapped

def mk_pkt_line(line):
    return '{0:04x}{1}'.format(len(line)+4, line)

def hdr_nocache(response):
        response.set_header('Cache-Control', 'no-cache, max-age=0, must-revalidate')
        response.set_header('Pragma', 'no-cache')
        response.set_header('Expires', 'Fri, 01 Jan 1980 00:00:00 GMT')
        response.set_header('Date',
                datetime.utcnow().strftime('%a, %d %b %G %T GMT'))

# TODO: This should be implemented as a stream to keep mem usage down
def pack_objects(repo, objects):
    gitproc = subprocess.Popen(['/usr/local/bin/git', 'pack-objects',
        '--stdout'], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
        stderr=subprocess.PIPE, cwd=repo.git_dir)

    for o in objects:
        gitproc.stdin.write('{0}\n'.format(o))
    gitproc.stdin.close()

    yield gitproc.stderr.read()
    yield gitproc.stdout.read()
