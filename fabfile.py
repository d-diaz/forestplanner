from fabric.api import *

vars = {
    'app_dir': '/usr/local/apps/land_owner_tools/lot',
    'venv': '/usr/local/venv/lot',
    'sitename': 'localhost:8080'
}

env.forward_agent = True
env.key_filename = '~/.vagrant.d/insecure_private_key'

try:
    from fab_vars import *
    fab_vars_exists = True
except ImportError:
    fab_vars_exists = False


def dev():
    """ Use development server settings """
    servers = ['vagrant@127.0.0.1:2222']
    env.hosts = servers
    return servers


def stage():
    """ Use production server settings """
    try:
        if fab_vars_exists:
            env.key_filename = AWS_KEY_FILENAME_STAGE
            servers = AWS_PUBLIC_DNS_STAGE
            env.hosts = servers
            vars['sitename'] = AWS_SITENAME_STAGE
            return servers
        else:
            raise Exception("\nERROR: Cannot import file fab_vars.py. Have you created one from the template fab_vars.py.template?\n")
    except Exception as inst:
        print inst
    


def prod():
    """ Use production server settings """
    try:
        if fab_vars_exists:
            env.key_filename = AWS_KEY_FILENAME_PROD
            servers = AWS_PUBLIC_DNS_PROD
            env.hosts = servers
            vars['sitename'] = AWS_SITENAME_PROD
            return servers
        else:
            raise Exception("\nERROR: Cannot import file fab_vars.py. Have you created one from the template fab_vars.py.template?\n")
    except Exception as inst:
        print inst



def test():
    """ Use test server settings """
    servers = ['ninkasi']
    env.hosts = servers
    return servers


def all():
    """ Use all servers """
    env.hosts = dev() + prod() + test()


def _install_requirements():
    run('cd %(app_dir)s && %(venv)s/bin/pip install -r ../requirements.txt' % vars)


def _install_django():
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py syncdb --noinput && \
                           %(venv)s/bin/python manage.py migrate --noinput && \
                           %(venv)s/bin/python manage.py install_media -a && \
                           %(venv)s/bin/python manage.py enable_sharing --all && \
                           %(venv)s/bin/python manage.py site %(sitename)s && \
                           %(venv)s/bin/python manage.py install_cleangeometry' % vars)


def _recache():
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py clear_cache && \
                           %(venv)s/bin/python manage.py precache' % vars)

def create_superuser():
    """ Create the django superuser (interactive!) """
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py createsuperuser' % vars)


def import_data():
    """ Fetches and installs data fixtures (WARNING: 5+GB of data; hence not checking fixtures into the repo) """
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py import_data' % vars)


def init():
    """ Initialize the forest planner application """
    _install_requirements()
    _install_django()
    _install_starspan()
    _recache()
    #restart_services()


def restart_services():
    run('sudo service uwsgi restart && sudo service nginx restart')
    run('sudo service supervisor status')
    run('sudo service redis-server status')
    run('sudo service postgresql status')
    run('sudo supervisorctl restart all')
    run('sudo supervisorctl status')


def install_media():
    """ Run the django install_media command """
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py install_media' % vars)


def copy_media():
    """ Just copy the basic front end stuff. Speed! """
    run('rsync -rtvu /usr/local/apps/land_owner_tools/media/common/ /usr/local/apps/land_owner_tools/mediaroot/common' % vars)


def runserver():
    """ Run the django dev server on port 8000 """
    run('cd %(app_dir)s && %(venv)s/bin/python manage.py runserver 0.0.0.0:8000' % vars)


def update():
    """ Sync with master git repo """
    run('cd %(app_dir)s && git fetch && git merge origin/master' % vars)


def _install_starspan():
    run('mkdir -p ~/src && cd ~/src && \
        if [ ! -d "starspan" ]; then git clone git://github.com/Ecotrust/starspan.git; fi && \
        cd starspan && \
        if [ ! `which starspan` ]; then ./configure && make && sudo make install; fi')


def deploy():
    """
    Deploy to a staging/production environment
    """
    for s in env.hosts:
        if 'vagrant' in s:
            raise Exception("You can't deploy() to local dev, just use `init restart_services`")
    update()
    init()
    restart_services()
