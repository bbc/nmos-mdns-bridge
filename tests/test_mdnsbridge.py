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
import json

from mdnsbridge.mdnsbridge import VALID_TYPES, APINAMESPACE, APINAME, APIVERSION, mDNSBridgeAPI, mDNSBridge


class StubWebAPI(object):
    pass


class AbortException(Exception):
    def __init__(self, code, *args, **kwargs):
        self.code = code
        super(AbortException, self).__init__(*args, **kwargs)


class TestmDNSBridgeAPI(unittest.TestCase):

    def setUp(self):
        self.APIBASE = "/{}/{}/{}/".format(APINAMESPACE, APINAME, APIVERSION)
        self.mock_mdns_get_services()
        # Expse Werkzeug test client to test API
        flaskr = mDNSBridgeAPI(self.mdns)
        flaskr.app.config['TESTING'] = True
        self.client = flaskr.app.test_client()

    def mock_mdns_get_services(self):
        self.mdns = mock.MagicMock()
        # the mock mdns needs to mock the get_services method
        # make it reflect what it is passed

        def behaviour(passedValue):
            return passedValue
        self.mdns.get_services = behaviour

    def inspect_endpoint(self, path, expected, resourceName):
        # Get reponse from test client, compare to expected
        rv = self.client.get(path)
        actual = json.loads(rv.data)
        message = ("{} resource at '/' should return "
                   "{}, got {}").format(resourceName, expected, actual)
        self.assertEqual(actual, expected, msg=message)

    def test_namespace_resource(self):
        self.inspect_endpoint(
            path='/',
            expected=[APINAMESPACE + '/'],
            resourceName="Namespace"
        )

    def test_apinamespace_resource(self):
        self.inspect_endpoint(
            path='/{}/'.format(APINAMESPACE),
            expected=[APINAME + '/'],
            resourceName="API Namespace"
        )

    def test_version_resource(self):
        myPath = '/{}/{}/'.format(APINAMESPACE, APINAME)
        self.inspect_endpoint(
            path=myPath,
            expected=[APIVERSION + '/'],
            resourceName="Version"
        )

    def test_base_resource(self):
        myExpected = {
            "resources": [
                "nmos-query/",
                "nmos-registration/",
                "nmos-security/"
            ]
        }
        self.inspect_endpoint(
            path=self.APIBASE,
            expected=myExpected,
            resourceName="Base"
        )

    def test_type_resource(self):
        myExpected = {
            "representation": "nmos-query"
        }
        myPath = self.APIBASE + "nmos-query/"
        self.inspect_endpoint(
            path=myPath,
            expected=myExpected,
            resourceName="Base"
        )

    def test_invalid_types(self):
        myPath = self.APIBASE + "potato/"
        rv = self.client.get(myPath)
        expected = 404
        actual = rv.status_code
        message = ("Type resource should result in a 404 for invalid"
                   "type 'potato', but resulted  in {}").format(actual)
        self.assertEqual(expected, actual, msg=message)


class TestmDNSBridge(unittest.TestCase):
    @mock.patch('mdnsbridge.mdnsbridge.MDNSEngine')
    def setUp(self, MDNSEngine):
        self.UUT = mDNSBridge(domain=mock.sentinel.domain)
        self.assertItemsEqual(MDNSEngine.return_value.callback_on_services.mock_calls,
                              [mock.call("_" + type + "._tcp", mock.ANY, registerOnly=False, domain=mock.sentinel.domain) for type in VALID_TYPES])
        self.callbacks = {regtype.split('.')[0][1:]: f for (regtype, f) in (call[1] for call in MDNSEngine.return_value.callback_on_services.mock_calls)}

    def assert_registered_callback_correctly_handles_data_from_mdns(self, type, action, name, address=None, prefer_ipv6=False, expect_no_add=False, priority=100):
        expected = {'protocol': 'http',
                    'name': name,
                    'versions': ['v1.0', 'v1.1', 'v1.2'],
                    'priority': priority,
                    'address': address,
                    'txt': {'api_ver': 'v1.0,v1.1,v1.2', 'api_proto': 'http', 'pri': str(priority)},
                    'port': mock.sentinel.port}
        with mock.patch('nmoscommon.nmoscommonconfig.config', {'prefer_ipv6': prefer_ipv6}):
            self.callbacks[type]({"type": "_" + type + "._tcp",
                                  "action": action,
                                  "txt": {"pri": str(priority), "api_ver": "v1.0,v1.1,v1.2", "api_proto": "http"},
                                  "name": name,
                                  "address": address,
                                  "port": mock.sentinel.port, })
        if action == "add" and not expect_no_add:
            self.assertIn(expected, self.UUT.get_services(type))
        else:
            self.assertListEqual([entry for entry in self.UUT.get_services(type) if entry["name"] == name], [])

    def test_nmos_query_callback_add_ipv4_on_ipv4_system(self):
        """Should add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add", mock.sentinel.name, "192.168.0.1")

    def test_nmos_query_callback_add_ipv6_on_ipv4_system(self):
        """Should not add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add", mock.sentinel.name, "bbc1:bbc2::bbc4", expect_no_add=True)

    def test_nmos_query_callback_add_ipv4_on_ipv6_system(self):
        """Should not add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add", mock.sentinel.name, "192.168.0.1", prefer_ipv6=True, expect_no_add=True)

    def test_nmos_query_callback_add_ipv6_on_ipv6_system(self):
        """Should add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add", mock.sentinel.name, "bbc1:bbc2::bbc4", prefer_ipv6=True)

    def test_nmos_query_callback_can_update_after_adding(self):
        """Should add the given resource to the local store and then replace it."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add", mock.sentinel.name, "192.168.0.1", priority=100)
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add", mock.sentinel.name, "192.168.0.1", priority=200)

    def test_nmos_query_callback_can_remove_after_adding(self):
        """Should add the given resource to the local store and then remove it again."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add", mock.sentinel.name, "192.168.0.1")
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "remove", mock.sentinel.name)

    def test_nmos_registration_callback_add_ipv4_on_ipv4_system(self):
        """Should add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "add", mock.sentinel.name, "192.168.0.1")

    def test_nmos_registration_callback_add_ipv6_on_ipv4_system(self):
        """Should not add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "add", mock.sentinel.name, "bbc1:bbc2::bbc4", expect_no_add=True)

    def test_nmos_registration_callback_add_ipv4_on_ipv6_system(self):
        """Should not add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "add", mock.sentinel.name, "192.168.0.1", prefer_ipv6=True, expect_no_add=True)

    def test_nmos_registration_callback_add_ipv6_on_ipv6_system(self):
        """Should add the given resource to the local store."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "add", mock.sentinel.name, "bbc1:bbc2::bbc4", prefer_ipv6=True)

    def test_nmos_registration_callback_can_remove_after_adding(self):
        """Should add the given resource to the local store and then remove it again."""
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "add", mock.sentinel.name, "192.168.0.1")
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "remove", mock.sentinel.name)

    def test_get_service_fails_with_invalid_type(self):
        """There's no such thing as an nmos-potato, the mdnsbridge ought to know that."""
        self.assertIsNone(self.UUT.get_services("nmos-potato"))

    def test_stop_stops_mdns_engine(self):
        """Stopping the bridge should stop the underlying mdns engine."""
        self.UUT.mdns.stop.assert_not_called()
        self.UUT.stop()
        self.UUT.mdns.stop.assert_called_once_with()
