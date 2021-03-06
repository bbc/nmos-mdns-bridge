#!/usr/bin/python
#
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
from setuptools import setup
import os


def is_package(path):
    return (os.path.isdir(path) and os.path.isfile(os.path.join(path, '__init__.py')))


def find_packages(path, base=""):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package(dir):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages


packages = find_packages(".")
package_names = packages.keys()

# REMEMBER: If this list is updated, please also update stdeb.cfg and the RPM specfile
packages_required = [
    "gevent>=1.2.2",
    "nmoscommon>=0.12.0",
    "flask>=0.10.1",
    "cysystemd",
    "requests",
    "werkzeug>=0.14.1,<1.0.0"  # Echo pin from nmos-common to avoid Flask overriding it
]

setup(
    name="mdnsbridge",
    version="0.9.4",
    description="An API providing a DNS-SD/HTTP bridge for AMWA NMOS service types",
    url='https://github.com/bbc/nmos-mdns-bridge',
    author='Peter Brightwell',
    author_email='peter.brightwell@bbc.co.uk',
    license='Apache 2',
    packages=package_names,
    package_dir=packages,
    install_requires=packages_required,
    scripts=[],
    data_files=[
        ('/usr/bin', ['bin/nmos-mdnsbridge'])
    ],
    long_description="This API provides a DNS-SD/HTTP bridge for NMOS service types"
)
