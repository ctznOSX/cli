from __future__ import unicode_literals

import getpass
import datetime
from os import stat
from sys import exit
from glob import glob
from pwd import getpwuid
from shutil import rmtree
from os.path import isdir,join,sep
from titantools.system import shell_out
import urllib2, urllib, httplib, json

MONITOR_PATH = '/var/lib/ctznosx/monitors/'

# TODO: Install checksum check on package
def install(args):
    PREFIX = "[ Monitor::Install ] "

    # Check if it's already installed
    if does_monitor_exist(args[0]):
        print PREFIX, "This monitor already exists"       
        exit(2)


    # Check if it's a valid URL
    print PREFIX, "Locating monitor: %s" % args[0]
    if validate_repo(args[0]):

        # Let's clone it and chown it
        print PREFIX, "Found monitor: '%s'" % args[0].rsplit('/', 1)[1].split('.')[0]
        shell_out("cd %s && sudo git clone %s" % (MONITOR_PATH, args[0]))
        shell_out("sudo chown -R _ctznosx %s" % MONITOR_PATH)

        # Check that it exists, which means it installed successfully
        if does_monitor_exist(args[0]):
            print PREFIX,"Monitor successfully installed"
        else:
            print PREFIX,"There was an error installing the monitor"

    else:
        print PREFIX, "That is not a valid module, not installing anything"
        exit(1)
    

def does_monitor_exist(monitor):
    # Parse out the monitor from URL assuming Github
    monitor = monitor.rsplit('/', 1)[-1].split(".")[0]

    if isdir(join(MONITOR_PATH, monitor)):
        return True
    else:
        return False 

def remove(args):

    PREFIX = "[ Monitor::Remove ] "

    if getpass.getuser() != 'root':
        print PREFIX, "Please run this with elevated permissions"
        exit(1)
    
    if does_monitor_exist(args[0]):
        monitor_path = join(MONITOR_PATH, args[0])
        
        owner = find_owner(monitor_path)
        if "_ctznosx" != owner:
            print PREFIX,"Unable to remove, invalid permissions"
            exit(128)
        else:
            rmtree(monitor_path)

        # Make sure it doesnt exist still
        if does_monitor_exist(args[0]):
            print PREFIX,"Removing monitor failed"
        else:
            print PREFIX,"Successfully remove monitor"

    else:
        print PREFIX,"Could not find a monitor by the name of '%s'" % args[0]
        exit(1)

def list(args):
    print "The following ctznOSX monitors are installed:\n"

    monitors = [monitor for monitor in glob( join(MONITOR_PATH,"*") ) if monitor.find('README.md') is -1]

    if len(monitors) == 0:
        print "None"
        exit()
        
    for monitor in monitors:
        stats = stat(monitor)        
        
        monitor_name = monitor.rsplit('/', 1)[1]
        install_date = datetime.datetime.fromtimestamp(
            int(stats.st_mtime)
        ).strftime('%d-%b %y @ %H:%M:%S')

        sourced_from = shell_out("git -C %s remote -v" % monitor)

        print "{}\n\tInstalled on: {}\n\tSourced From:   {}".format(monitor_name, install_date, sourced_from.replace("\n", "\n\t\t\t"))

def find_owner(filename):
    return getpwuid(stat(filename).st_uid).pw_name

# Send the request
def validate_repo( target ):
    result = shell_out("git ls-remote %s" % target)
    if "HEAD" in result:
        return True

    return False