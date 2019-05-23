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

import unittest
import mock
import six
from gevent import signal


with mock.patch("mdnsbridge.mdnsbridgeservice.monkey"):
    from mdnsbridge.mdnsbridgeservice import HOST, PORT, mDNSBridgeService
    from mdnsbridge.mdnsbridge import mDNSBridgeAPI, APINAME, APINAMESPACE, APIVERSION


class TestmDNSBridgeService(unittest.TestCase):
    @mock.patch('mdnsbridge.mdnsbridgeservice.Facade')
    @mock.patch("mdnsbridge.mdnsbridgeservice.NODE_API_PRESENT", True)
    def setUp(self, Facade):
        self.UUT = mDNSBridgeService(domain=mock.sentinel.domain)
        Facade.assert_called_once_with("{}/{}".format(APINAME, APIVERSION))
        self.assertEqual(self.UUT.facade, Facade.return_value)

    @mock.patch('gevent.signal')
    @mock.patch('gevent.sleep')
    @mock.patch('mdnsbridge.mdnsbridgeservice.mDNSBridge')
    @mock.patch('mdnsbridge.mdnsbridgeservice.HttpServer')
    @mock.patch('mdnsbridge.mdnsbridgeservice.daemon')
    def assert_run_starts_runs_and_stops_as_expected(
        self, n, daemon, HttpServer, mDNSBridge, sleep,
        gevent_signal, http_server_fails_with_exception=None
            ):
        HttpServer.return_value.started.is_set.side_effect = [False, False, False, True]
        HttpServer.return_value.failed = http_server_fails_with_exception

        responses = [None for _ in range(0, n)]
        _responses = [x for x in responses]

        def sleep_then_kill(t):
            if len(_responses) > 0:
                return _responses.pop(0)
            else:
                self.UUT.stop()
                return None

        sleep.side_effect = sleep_then_kill

        if http_server_fails_with_exception is None:
            self.UUT.run()
        else:
            with self.assertRaises(http_server_fails_with_exception):
                self.UUT.run()

        six.assertCountEqual(self, gevent_signal.mock_calls, [mock.call(signal.SIGINT, mock.ANY),
                                                              mock.call(signal.SIGTERM, mock.ANY)])

        self.handlers = {sig: handler for (sig, handler) in (call[1] for call in gevent_signal.mock_calls)}

        mDNSBridge.assert_called_once_with(domain=mock.sentinel.domain)
        HttpServer.assert_called_once_with(mDNSBridgeAPI, PORT, HOST, api_args=[mDNSBridge.return_value])
        HttpServer.return_value.start.assert_called_once_with()
        self.assertListEqual(HttpServer.return_value.started.wait.mock_calls, [mock.call() for _ in range(0, 3)])

        if http_server_fails_with_exception is not None:
            self.UUT.facade.register_service.assert_not_called()
            daemon.notify.assert_not_called()
            self.UUT.facade.heartbeat_service.assert_not_called()
            self.UUT.facade.unregister_service.assert_not_called()
            HttpServer.return_value.stop.assert_not_called()
            mDNSBridge.return_value.stop.assert_not_called()
        else:
            self.UUT.facade.register_service.assert_called_once_with(
                "http://" + HOST + ":" + str(PORT), "{}/{}/{}/".format(APINAMESPACE, APINAME, APIVERSION)
            )
            daemon.notify.assert_called_once_with("READY=1")
            self.assertListEqual(
                self.UUT.facade.heartbeat_service.mock_calls, [mock.call() for x in range(0, len(responses)//5)]
            )
            self.UUT.facade.unregister_service.assert_called_once_with()
            HttpServer.return_value.stop.assert_called_once_with()
            mDNSBridge.return_value.stop.assert_called_once_with()

    def test_run_one_iteration(self):
        self.assert_run_starts_runs_and_stops_as_expected(1)

    def test_run_13_iterations(self):
        self.assert_run_starts_runs_and_stops_as_expected(13)

    def test_signal_handling_of_SIGINT(self):
        self.assert_run_starts_runs_and_stops_as_expected(1)

        with mock.patch.object(self.UUT, 'stop') as stop:
            self.handlers[signal.SIGINT]()
            stop.assert_called_once_with()

    def test_signal_handling_of_SIGTERM(self):
        self.assert_run_starts_runs_and_stops_as_expected(1)

        with mock.patch.object(self.UUT, 'stop') as stop:
            self.handlers[signal.SIGTERM]()
            stop.assert_called_once_with()

    def test_run_fails_if_webserver_fails_to_start(self):
        self.assert_run_starts_runs_and_stops_as_expected(1, http_server_fails_with_exception=Exception)
