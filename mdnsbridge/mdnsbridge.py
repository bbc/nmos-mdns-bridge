#!/usr/bin/python

# Copyright 2017 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gevent
import time
from nmoscommon.webapi import WebAPI, route
from nmoscommon.mdns import MDNSEngine

from flask import abort
from nmoscommon import nmoscommonconfig

VALID_TYPES = ["nmos-query", "nmos-registration", "nmos-security"]

APINAMESPACE = "x-ipstudio"
APINAME = "mdnsbridge"
APIVERSION = "v1.0"
APIBASE = "/{}/{}/{}/".format(APINAMESPACE, APINAME, APIVERSION)


class mDNSBridgeAPI(WebAPI):
    def __init__(self, mdns):
        self.mdns = mdns
        super(mDNSBridgeAPI, self).__init__()

    @route("/")
    def namespace_resource(self):
        return [APINAMESPACE + '/']

    @route("/{}/".format(APINAMESPACE))
    def name_resource(self):
        return [APINAME + '/']

    @route("/{}/{}/".format(APINAMESPACE, APINAME))
    def version_resource(self):
        return [APIVERSION + '/']

    @route(APIBASE)
    def base_resource(self):
        return {"resources": [value + "/" for value in VALID_TYPES]}

    @route(APIBASE + '<path>/')
    def type_resource(self, path):
        if path not in VALID_TYPES:
            abort(404)
        return {"representation": self.mdns.get_services(path)}


class mDNSBridge(object):
    def __init__(self, domain=None):
        self.mdns = MDNSEngine()
        self.mdns.start()
        self.services = {}
        self.domain = domain
        self.timeout = 0
        self._update_callback()

    def _update_callback(self):
        # Timeout is a workaround for the fact a unicast DNS query is only issued on startup
        # This ensures we check if avahi's cache has expired regularly, and if so a new query will be issued
        # In the worst case we'll breach the DNS record's TTL by the number of seconds set below
        self.timeout = time.time() + 60
        for type in VALID_TYPES:
            if type not in self.services:
                self.services[type] = []
            try:
                self.mdns.callback_on_services("_" + type + "._tcp", self._mdns_callback, registerOnly=False, domain=self.domain)
            except Exception:
                pass  # This is a workaround for now. Need a mechanism to remove callbacks before adding more

    def _mdns_callback(self, data):
        srv_type = data["type"][1:].split(".")[0]
        if data["action"] == "add":
            priority = 0
            versions = ["v1.0"]
            protocol = "http"
            if "pri" in data["txt"]:
                if data["txt"]["pri"].isdigit() and data["txt"]["pri"] >= 100:
                    priority = int(data["txt"]["pri"])
            if "api_ver" in data["txt"]:
                versions = data["txt"]["api_ver"].split(",")
            if "api_proto" in data["txt"]:
                protocol = data["txt"]["api_proto"]
            service_entry = {
                "name": data["name"], "address": data["address"], "port": data["port"], "txt": data["txt"],
                "priority": priority, "versions": versions, "protocol": protocol
            }
            for service in self.services[srv_type]:
                if service["name"] == data["name"] and service["address"] == data["address"]:
                    service.update(service_entry)
                    return
            if nmoscommonconfig.config.get('prefer_ipv6', False) is False:
                if ":" not in data["address"]:
                    self.services[srv_type].append(service_entry)
            else:
                if not data["address"].startswith("fe80::") and "." not in data["address"]:
                    self.services[srv_type].append(service_entry)
            # TODO: Due to issues with python requests library, IPv6 link local addresses are not compatable with requests.request().
            # Therefore, IPv6 Global addresses must be used for nodes to register with pipeline manager through ipppython aggregator.py
            # Below code will allow link-local addresses to be used if requests bug is fixed
            # else:
            #     service_entry["address"] = str(data["address"])+str("%%")+str(if_indextoname(data["interface"]))
            #     self.services[srv_type].append(service_entry)

        elif data["action"] == "remove":
            for service in self.services[srv_type]:
                if service["name"] == data["name"]:
                    self.services[srv_type].remove(service)
                    break

    def get_services(self, type):
        if type not in VALID_TYPES:
            return None
        elif time.time() > self.timeout:
            self._update_callback()
        return self.services[type]

    def stop(self):
        self.mdns.stop()


if __name__ == "__main__":  # pragma: no cover
    mdns = mDNSBridge()
    try:
        while True:
            print("*** mDNS ***")
            print(mdns.get_services("nmos-query"), "\n")
            gevent.sleep(1)
    except:
        mdns.stop()
