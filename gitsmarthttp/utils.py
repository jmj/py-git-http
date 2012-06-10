from os import path
import datetime

from tornado.options import options

import logging
log = logging.getLogger(__name__)

## Decorator to make sure the repo is valid.
def clense_path(fn):
    def wrapped(self, repo, *args, **kw):
        log.debug('Cleaning path: {}/{}'.format(options.base, repo))
        ## deref . and .., etc
        repo_path = path.abspath('{}/{}'.format(options.base, repo))

        if path.exists(repo_path) and repo_path.startswith(options.base):
            return fn(self, repo, *args, **kw)
        self.set_status(403)
        return
    return wrapped

def pkt_flush():
    return '0000'

def mk_pkt_line(line):
    return '{:04x}{}'.format(len(line), line)

def hdr_nocache(response):
        response.set_header('Cache-Control', 'no-cache, max-age=0, must-revalidate')
        response.set_header('Pragma', 'no-cache')
        response.set_header('Expires', 'Fri, 01 Jan 1980 00:00:00 GMT')
        response.set_header('Date',
                datetime.utcnow().strftime('%a, %d %b %G %T GMT'))
