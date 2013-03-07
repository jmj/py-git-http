from os import path
from datetime import datetime

from bottle import abort

import gevent_subprocess as subprocess

import logging
log = logging.getLogger(__name__)

repo_base='/tmp/repo'

def mk_pkt_line(line):
    return '{0:04x}{1}'.format(len(line)+4, line)

def hdr_nocache(response):
        response.set_header('Cache-Control',
                'no-cache, max-age=0, must-revalidate')
        response.set_header('Pragma', 'no-cache')
        response.set_header('Expires', 'Fri, 01 Jan 1980 00:00:00 GMT')
        response.set_header('Date',
                datetime.utcnow().strftime('%a, %d %b %G %T GMT'))

class PathCleanerPlugin(object):
    name = 'PathCleaner'
    api = 2

    def __init__(self, repo_base):
        self.repo_base = repo_base

    def apply(self, callback, context):
        log.debug('PathCleaner.apply()')
        conf = context.config.get('PathCleaner') or {}
        repo_base = conf.get('repo_base', self.repo_base)

        def wrapped(repo, *args, **kw):
            ## deref . and .., etc
            repo_path = path.abspath('{}/{}'.format(repo_base, repo))

            if path.exists(repo_path) and repo_path.startswith(repo_base):
                return callback(repo, *args, **kw)
            abort(403, 'Unauthorized')
        return wrapped


class Git(object):
    def __init__(self, repo, path='/usr/local/bin/git', *opts):
        self._repo = repo
        self._git = path
        self._opts = opts
        self._exe = list(opts)
        self._exe.insert(0, self._git)

    def __getattr__(self, name):
        name = name.replace('_', '-')

        exe = list(self._exe)
        exe.append(name)

        def proc(*opts):
            exe.extend(opts)
            exe.append(self._repo)
            log.debug(exe)
            proc = subprocess.Popen(exe, stdout=subprocess.PIPE,
                stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd=self._repo)
            return proc
        return proc

