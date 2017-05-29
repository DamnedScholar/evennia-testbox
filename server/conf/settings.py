"""
Evennia settings file.

The available options are found in the default settings file found
here:

D:\github\evennia\evennia\settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Testbox"
# A list of ports the Evennia telnet server listens on Can be one or many.
TELNET_PORTS = [4010]
# The webserver sits behind a Portal proxy. This is a list
# of tuples (proxyport,serverport) used. The proxyports are what
# the Portal proxy presents to the world. The serverports are
# the internal ports the proxy uses to forward data to the Server-side
# webserver (these should not be publicly open)
WEBSERVER_PORTS = [(8010, 5011)]
# Ports to use for SSH
SSH_PORTS = [8032]
# Ports to use for SSL
SSL_PORTS = [4011]
# The game server opens an AMP port so that the portal can
# communicate with it. This is an internal functionality of Evennia, usually
# operating between two processes on the same machine. You usually don't need to
# change this unless you cannot use the default AMP port/host for
# whatever reason.
AMP_HOST = 'localhost'
AMP_PORT = 5010
AMP_INTERFACE = '127.0.0.1'
# Server-side websocket port to open for the webclient.
WEBSOCKET_CLIENT_PORT = 8001
# This is a security setting protecting against host poisoning
# attacks.  It defaults to allowing all. In production, make
# sure to change this to your actual host addresses/IPs.
ALLOWED_HOSTS = ["*"]
# How long time (in seconds) a user may idle before being logged
# out. This can be set as big as desired. A user may avoid being
# thrown off by sending the empty system command 'idle' to the server
# at regular intervals. Set <=0 to deactivate idle timeout completely.
# IDLE_TIMEOUT = 259200 would make three days.
IDLE_TIMEOUT = -1

######################################################################
# Django web features
######################################################################


# The secret key is randomly seeded upon creation. It is used to sign
# Django's cookies. Do not share this with anyone. Changing it will
# log out all active web browsing sessions. Game web client sessions
# may survive.
SECRET_KEY = 'Y*K]@~XvL?Q-CPZOHjnx(gFR=!#mJ;8l/W<Uu>9:'

INSTALLED_APPS += ('django.contrib.humanize',
                   'django_nyt',
                   'mptt',
                   'sekizai',
                   'sorl.thumbnail',
                   'wiki',
                   'wiki.plugins.attachments',
                   'wiki.plugins.notifications',
                   'wiki.plugins.images',
                   'wiki.plugins.macros')

INSTALLED_APPS += ('web.character',
                   'sr5.systemview')

# Probably need to remove this.
DEBUG = True

TEMPLATE_CONTEXT_PROCESSORS = ['sekizai.context_processors.sekizai',
                               'django.core.context_processors.debug']
