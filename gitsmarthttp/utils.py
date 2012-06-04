from os import path
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



