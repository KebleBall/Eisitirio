import site, os, sys
site.addsitedir(os.path.realpath(__file__).replace('kebleball','lib/python2.7/site-packages'))
sys.path.append(os.path.realpath(__file__))

from kebleball import app as application

