from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import set_state
from charms.reactive import remove_state
from charms.reactive import hook

from charmhelpers.core import hookenv
from charmhelpers.core.templating import render
from charmhelpers.core.hookenv import config, status_set
from charmhelpers.core.host import restart_on_change, service_stop
#from charms.templating.jinja2 import render

import base64
import os
import pwd
import grp


@hook('install')
@hook('start')
@hook('config-changed')
def install_filecharm():
    status_set('maintenance', 'Installing file charm.')
    render_filecharm_template()


@hook('update-status')
def update():
    filepath = config().get('filename')
    if not os.path.exists(filepath):
        render_filecharm_template()


@when('config.changed.contents')
@when('config.changed.filepath')
def render_filecharm_template():
    filepath = config().get('filename')
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError as e:
            hookenv.log('unable to create directory {0}: {1}'.format(directory,e))
            exit(1)

    filecontents = base64.b64decode(config().get('contents')).decode('utf8')
    mode = int(config().get('mode'),8)
    owner = config().get('owner').split(':')
    connections = render(source='',
                         config_template=filecontents,
                         target=filepath,
                         context=config(),
                         perms=mode,
                         owner=owner[0],
                         group=owner[1])
    if config().get('command'):
        try:
            os.system(config().get('command'))
        except OSError as e:
            hookenv.log('failed to run command "{0}": {1}'.format(command,e))
            exit(1)

    if connections:
        status_set('active', 'Filecharm ready.')


@when('config.changed.owner')
def update_permissions():
    filepath = config().get('filename')
    owner = config().get('owner').split(':')
    uid = pwd.getpwnam(owner[0]).pw_uid
    gid = grp.getgrnam(owner[1]).gr_gid
    if os.path.exists(filepath):
        os.chown(filepath, uid, gid)


@when('config.changed.mode')
def update_mode():
    filepath = config().get('filename')
    mode = int(config().get('mode'),8)
    if os.path.exists(filepath):
        os.chmod(filepath,mode)


@hook('stop')
def remove_filecharm():
    try:
        filepath = config().get('filename')
        os.remove(filepath)
    except OSError:
        pass


