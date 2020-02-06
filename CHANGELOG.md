# NMOS mDNS Bridge Library Changelog

## 0.9.3
- Fix `api_auth` value error in `mdns_callback`

## 0.9.2
- Add `api_auth` parameter to MDNS Client

## 0.9.1
- Alter executable to run using Python3, alter `stdeb` to replace python 2 package, call `cleanup` in stop()

## 0.9.0
- Add method to raise an exception when no service found or when end of list reached

## 0.8.1
- Handle case where txt data includes a boolean

## 0.8.0
- Signal authorization support in API

## 0.7.3
- Fix python3 errors

## 0.7.2
- Move NMOS packages from recommends to depends

## 0.7.1
- Use facade class from nmosnode if present

## 0.7.0
- Add mDNS bridge client library from nmos-common

## 0.6.4
- Fix missing files in Python 3 Debian package

## 0.6.3
- Add support for Python 3

## 0.6.2
- Changed service type from 'nmos-security' to 'nmos-auth'

## 0.6.1
- Fix bug in surfacing priorities 1 through 99

## 0.6.0
- Add ability to surface hostnames in the API

## 0.5.2
- Fix read from incorrect config file

## 0.5.1
- Remove periodic re-query for unicast DNS which is no longer required

## 0.5.0
- Addition of 'nmos-register' mDNS service type

## 0.4.0
- Addition of 'nmos-security' mDNS service type
