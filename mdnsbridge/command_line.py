#!/usr/bin/python

import os
import gevent.monkey
import json
gevent.monkey.patch_all()

from mdnsbridgeservice import mDNSBridgeService

def load_config():
    extra_config = dict()
    try:
        config_file = "/etc/ipppython/config.json"
        if os.path.isfile(config_file):
            f = open(config_file, 'r')
            extra_config = json.loads(f.read())
    except Exception as e:
        print "Exception loading config: {}".format(e)
    return extra_config

def main():
    cfg = load_config()
    if 'domain' in cfg:
        domain = cfg['domain']
    else:
        domain = None
    service = mDNSBridgeService(domain=domain)
    service.run()
