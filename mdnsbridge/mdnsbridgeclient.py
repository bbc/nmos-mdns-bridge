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

from __future__ import print_function
from __future__ import absolute_import

import requests
import random

from nmoscommon.nmoscommonconfig import config as _config
from nmoscommon.logger import Logger


class NoService(Exception):
    pass


class EndOfServiceList(Exception):
    pass


class IppmDNSBridge(object):
    def __init__(self, logger=None):
        self.logger = Logger("mdnsbridge", logger)
        self.services = {}
        self.config = {}
        self.config.update(_config)

    def getHref(self, srv_type, priority=None, api_ver=None, api_proto=None, api_auth=None):
        try:
            try:
                return self.getHrefWithException(srv_type, priority, api_ver, api_proto, api_auth)
            except EndOfServiceList:
                self.logger.writeInfo("End of DNS-SD service list, reloading")
                # Re-try after cache has been updated
                return self.getHrefWithException(srv_type, priority, api_ver, api_proto, api_auth)
        except NoService:
            self.logger.writeWarning(
                "No DNS-SD service for {}, priority={}, api_ver={}, api_proto={}, api_auth={}".format(
                    srv_type, priority, api_ver, api_proto, api_auth))
            return ""

    def getHrefWithException(self, srv_type, priority=None, api_ver=None, api_proto=None, api_auth=None):
        if priority is None:
            priority = self.config["priority"]

        if self.logger is not None:
            self.logger.writeDebug("IppmDNSBridge priority = {}".format(priority))

        # Check if type is in services. If not add it
        if srv_type not in self.services:
            self.services[srv_type] = []

        # Check if there are any of that type of service, if not do a request
        valid_services = self._getValidServices(srv_type, priority, api_ver, api_proto, api_auth)

        if len(valid_services) == 0:
            self.updateServices(srv_type)
            valid_services = self._getValidServices(srv_type, priority, api_ver, api_proto, api_auth)

            if len(valid_services) == 0:
                raise NoService
            else:
                raise EndOfServiceList

        # Randomise selection. Delete entry from the cached list of services and return it
        random.seed()
        index = random.randint(0, len(valid_services) - 1)
        service = valid_services[index]
        href = self._createHref(service)
        self.services[srv_type].remove(service)

        return href

    def _getValidServices(self, srv_type, priority, api_ver=None, api_proto=None, api_auth=None):
        current_priority = 99
        valid_services = []
        for service in self.services[srv_type]:
            if api_ver is not None and api_ver not in service["versions"]:
                continue
            if api_proto is not None and api_proto != service["protocol"]:
                continue
            if api_auth is not None and api_auth != service.get("authorization", False):
                continue
            if priority >= 100:
                if service["priority"] == priority:
                    valid_services.append(service)
            else:
                if service["priority"] < current_priority:
                    current_priority = service["priority"]
                    valid_services = []
                if service["priority"] == current_priority:
                    valid_services.append(service)

        return valid_services

    def _createHref(self, service):
        proto = service['protocol']
        if service.get('hostname') is not None and self.config["prefer_hostnames"]:
            address = service['hostname']
        else:
            address = service['address']
            if ":" in address:
                address = "[" + address + "]"
        port = service['port']
        return '{}://{}:{}'.format(proto, address, port)

    def updateServices(self, srv_type):
        req_url = "http://127.0.0.1/x-ipstudio/mdnsbridge/v1.0/" + srv_type + "/"
        try:
            # Request to localhost/x-ipstudio/mdnsbridge/v1.0/<type>/
            r = requests.get(req_url, timeout=0.5, proxies={'http': ''})
            if r is not None and r.status_code == 200:
                # If any results, put them in self.services
                self.services[srv_type] = []
                for dns_data in r.json()["representation"]:
                    if self.config["https_mode"] == "enabled" and dns_data["protocol"] == "https":
                        self.services[srv_type].append(dns_data)
                    elif self.config["https_mode"] != "enabled" and dns_data["protocol"] == "http":
                        self.services[srv_type].append(dns_data)
                    else:
                        self.logger.writeDebug(("Ignoring service with IP {} as protocol '{}' doesn't match the "
                                                "current mode").format(dns_data["address"], dns_data["protocol"]))
        except Exception as e:
            self.logger.writeWarning("Exception updating services: {}".format(e))


if __name__ == "__main__":  # pragma: no cover
    bridge = IppmDNSBridge()
    print(bridge.getHref("nmos-registration"))
