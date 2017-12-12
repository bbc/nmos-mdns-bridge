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
