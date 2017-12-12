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

def route_decorator(path):
    def decorate_function(f):
        f.mock_path = path
        return f
    return decorate_function

class StubWebAPI(object):
    pass

class AbortException(Exception):
    def __init__(self, code, *args, **kwargs):
        self.code = code
        super(AbortException, self).__init__(*args, **kwargs)

with mock.patch('nmoscommon.webapi.WebAPI', StubWebAPI):
    with mock.patch('nmoscommon.webapi.route', side_effect=route_decorator) as route:
        from mdnsbridge.mdnsbridge import *

class TestmDNSBridgeAPI(unittest.TestCase):
    def setUp(self):
        self.mdns = mock.MagicMock(name="mdns")
        self.mdns.get_services.side_effect = lambda path : getattr(self.mdns.get_services, path)
        self.UUT = mDNSBridgeAPI(self.mdns)

    def test_init(self):
        self.assertItemsEqual(route.mock_calls,
                                  [mock.call('/'),
                                   mock.call("/{}/".format(APINAMESPACE)),
                                   mock.call("/{}/{}/".format(APINAMESPACE, APINAME)),
                                   mock.call('/{}/{}/{}/'.format(APINAMESPACE, APINAME, APIVERSION)),
                                   mock.call('/{}/{}/{}/<path>/'.format(APINAMESPACE, APINAME, APIVERSION))])

    def assert_method_has_path_and_returns(self, method, path, expected, args=[], kwargs={}):
        """This method is a fixture to check a method of mDNSBridgeAPI has the right path associated to it, and gives the right return value when called. The expected param can either be the expected return, or the expected exception to be raised."""
        self.assertEqual(getattr(self.UUT, method).mock_path, path, msg="method {} was inserted into the webapi with the incorrect path: {}, when expected {}".format(method, getattr(self.UUT, method).mock_path, path))

        def raise_on_abort(code):
            raise AbortException(code)

        with mock.patch('mdnsbridge.mdnsbridge.abort', side_effect=raise_on_abort):
            try:
                rval = getattr(self.UUT,method)(*args, **kwargs)
            except AbortException as e:
                self.assertIsInstance(expected, AbortException, msg="Got an abort with code {} when expecting a clean return, whilst calling {} with arguments: {}".format(e.code, method, repr(args)))
                self.assertEqual(e.code, expected.code, msg="Got an abort with code {} when expecting an abort with {} whilst calling {} with arguments {}".format(e.code, expected.code, method, repr(args)))
            else:
                self.assertEqual(rval, expected, msg="method {} returned: {}, when expected {}".format(method, repr(rval), repr(expected)))

    def test_namespace_resource(self):
        self.assert_method_has_path_and_returns('namespace_resource', '/', [APINAMESPACE + '/'])

    def test_name_resource(self):
        self.assert_method_has_path_and_returns('name_resource', "/{}/".format(APINAMESPACE), [APINAME + '/'])

    def test_version_resource(self):
        self.assert_method_has_path_and_returns('version_resource', "/{}/{}/".format(APINAMESPACE, APINAME), [APIVERSION + '/'])

    def test_base_resource(self):
        self.assert_method_has_path_and_returns('base_resource', "/{}/{}/{}/".format(APINAMESPACE, APINAME, APIVERSION), {"resources": [value + "/" for value in VALID_TYPES]})

    def test_type_resource(self):
        for path in VALID_TYPES:
            self.assert_method_has_path_and_returns('type_resource', "/{}/{}/{}/<path>/".format(APINAMESPACE, APINAME, APIVERSION), {"representation": getattr(self.mdns.get_services,path)}, args=[path,])

        INVALID_TYPES = [ "potato", ]
        for path in INVALID_TYPES:
            self.assert_method_has_path_and_returns('type_resource', "/{}/{}/{}/<path>/".format(APINAMESPACE, APINAME, APIVERSION), AbortException(404), args=[path,])

class TestmDNSBridge(unittest.TestCase):
    @mock.patch('mdnsbridge.mdnsbridge.MDNSEngine')
    def setUp(self, MDNSEngine):
        self.UUT = mDNSBridge(domain=mock.sentinel.domain)
        self.assertItemsEqual(MDNSEngine.return_value.callback_on_services.mock_calls,
                                      [ mock.call("_" + type + "._tcp", mock.ANY, registerOnly=False, domain=mock.sentinel.domain) for type in VALID_TYPES ])
        self.callbacks = { regtype.split('.')[0][1:] : f for (regtype, f) in ( call[1] for call in MDNSEngine.return_value.callback_on_services.mock_calls ) }

    def assert_registered_callback_correctly_handles_data_from_mdns(self, type, action, name, address=None, prefer_ipv6 = False, expect_no_add=False, priority=100):
        expected = {'protocol': 'http',
                    'name': name,
                    'versions': ['v1.0', 'v1.1', 'v1.2'],
                    'priority': priority,
                    'address': address,
                    'txt': {'api_ver': 'v1.0,v1.1,v1.2', 'api_proto': 'http', 'pri': str(priority)},
                    'port': mock.sentinel.port }
        with mock.patch('nmoscommon.nmoscommonconfig.config', { 'prefer_ipv6' : prefer_ipv6 }):
            self.callbacks[type]({"type"   : "_" + type + "._tcp",
                                "action" : action,
                                "txt"    : { "pri" : str(priority), "api_ver" : "v1.0,v1.1,v1.2", "api_proto" : "http" },
                                "name"   : name,
                                "address": address,
                                "port"   : mock.sentinel.port,})
        if action == "add" and not expect_no_add:
            self.assertIn(expected, self.UUT.get_services(type))
        else:
            self.assertListEqual([ entry for entry in self.UUT.get_services(type) if entry["name"] == name ], [])


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
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-query', "add",    mock.sentinel.name, "192.168.0.1")
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
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "add",    mock.sentinel.name, "192.168.0.1")
        self.assert_registered_callback_correctly_handles_data_from_mdns('nmos-registration', "remove", mock.sentinel.name)

    def test_get_service_fails_with_invalid_type(self):
        """There's no such thing as an nmos-potato, the mdnsbridge ought to know that."""
        self.assertIsNone(self.UUT.get_services("nmos-potato"))

    def test_stop_stops_mdns_engine(self):
        """Stopping the bridge should stop the underlying mdns engine."""
        self.UUT.mdns.stop.assert_not_called()
        self.UUT.stop()
        self.UUT.mdns.stop.assert_called_once_with()
