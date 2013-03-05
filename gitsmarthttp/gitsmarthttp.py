#from pudb import set_trace; set_trace()
from bottle import run, request, response, abort, static_file
from bottle import Bottle

from git.repo import Repo
from git.objects import Object as Gitobject

from utils import clense_path, mk_pkt_line, hdr_nocache, pack_objects

import logging as log
log.basicConfig(level=log.DEBUG)


app = Bottle()

repo_base = '/tmp/repo'

#ul_caps = 'multi_ack thin-pack side-band side-band-64k ofs-delta shallow no-progress include-tag multi_ack_detailed agent=pygit2/{0}'.format(pygit2.__version__)
ul_caps = 'multi_ack thin-pack side-band side-band-64k ofs-delta shallow no-progress include-tag multi_ack_detailed agent=git/1.8.0'

## Temp to clean up logging
@app.route('/favicon.ico')
def icon():
    abort(401, 'foo')


# TODO: clense_path needs to check for None
@clense_path
@app.get('/<repo>/info/refs')
def get_refs(repo):
    log.debug('service={0}'.format(request.query['service']))

    r = Repo('{0}/{1}'.format(repo_base, repo))

    ret = [mk_pkt_line('# service={0}\n'.format(request.query['service']))]
    ret.append('0000')

    hdr_nocache(response)
    response.set_header('X-Powered-By', 'Me')

    if request.query['service'] == 'git-upload-pack':
        response.set_header('Content-Type',
                'application/x-git-upload-pack-advertisement')
        ret.append(mk_pkt_line('{0} HEAD{1}\n'.format(
            r.head.object.hexsha, ul_caps)))

    for ref in r.references:
    #for ref_name in r.listall_references():
        ret.append(mk_pkt_line('{0} {1}\n'.format(
            ref.object.hexsha, ref.path)))


    ret.append('0000')
    log.debug('----------')
    log.debug(ret)
    log.debug('----------')
    return ''.join(ret)

@clense_path
@app.get('/<repo>/HEAD')
def get_head(repo):
    return static_file('HEAD', root='{0}/{1}'.format(repo_base, repo))

@clense_path
@app.post('/<repo>/git-upload-pack')
def upload_pack(repo):

    r = Repo('{0}/{1}'.format(repo_base, repo))

    request_body = request.body
    wanted_objs = list()
    while True:
        datalen = request_body.read(4)
        log.debug('datalen: {0}'.format(datalen))
        if datalen == '0000':
            continue

        want = request_body.read(int(datalen, 16)-4)
        want = want.strip()
        log.debug('want: {0}'.format(want))

        if want == 'done':
            break

        wanted_objs.append(Gitobject.new(r, want[5:]))
        log.debug(wanted_objs)

    cnt = 0
    yield mk_pkt_line('NAK\n')
    for line in pack_objects(r, [o.hexsha for o in wanted_objs]):
        log.debug(cnt)
        cnt +=1
        yield mk_pkt_line('\x01{0}'.format(line))


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
    run(app, host='0.0.0.0', port=9000)
