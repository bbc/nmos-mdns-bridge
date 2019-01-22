#!/usr/bin/python

import gevent
import signal
from systemd import daemon
from nmoscommon.httpserver import HttpServer
from nmoscommon.facade import Facade
from .mdnsbridge import mDNSBridge, mDNSBridgeAPI, APINAME, APIVERSION, APINAMESPACE
from gevent import monkey
monkey.patch_all()

HOST = "127.0.0.1"
PORT = 12352


class mDNSBridgeService(object):
    def __init__(self, domain=None):
        self.running = False
        self.registered = False
        self.facade = Facade("{}/{}".format(APINAME, APIVERSION))
        self.domain = domain

    def start(self):
        if self.running:
            gevent.signal(signal.SIGINT, self.sig_handler)
            gevent.signal(signal.SIGTERM, self.sig_handler)

        self.mdns_bridge = mDNSBridge(domain=self.domain)
        self.http_server = HttpServer(mDNSBridgeAPI, PORT, HOST, api_args=[self.mdns_bridge])
        self.http_server.start()
        while not self.http_server.started.is_set():
            print("Waiting for httpserver to start...")
            self.http_server.started.wait()

        if self.http_server.failed is not None:
            raise self.http_server.failed

        print("Running on port: {}".format(self.http_server.port))

    def run(self):
        self.running = True
        self.start()
        self.facade.register_service("http://" + HOST + ":" + str(PORT),
                                     "{}/{}/{}/".format(APINAMESPACE, APINAME, APIVERSION))
        daemon.notify("READY=1")
        itercount = 0
        while self.running:
            itercount += 1
            gevent.sleep(1)
            if itercount == 5:  # 5 seconds
                self.facade.heartbeat_service()
                itercount = 0
        self.facade.unregister_service()
        self._cleanup()

    def stop(self):
        self.running = False

    def _cleanup(self):
        self.http_server.stop()
        self.mdns_bridge.stop()
        print("Stopped main()")

    def sig_handler(self):
        print("Pressed ctrl+c")
        self.stop()


if __name__ == "__main__":  # pragma: no cover

    service = mDNSBridgeService()
    service.start()

    try:
        while True:
            gevent.sleep(1)
    except Exception:
        service.stop()
