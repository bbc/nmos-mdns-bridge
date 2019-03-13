# NMOS MDNS Bridge

A DNS-SD to HTTP bridging service.

## Introduction

This API provides a zeroconf/HTTP bridge for NMOS service types. The API will present itself at [http://localhost:12352/x-ipstudio/mdnsbridge/v1.0/](http://localhost:12352/x-ipstudio/mdnsbridge/v1.0/).

## Installation

### Requirements

*   Linux (untested on Windows and Mac)
*   Python 2.7
*   Python Pip
*   [NMOS Common](https://github.com/bbc/nmos-common)

### Steps

```bash
# Install Python setuptools
$ pip install setuptools

# Install the library
$ sudo python setup.py install
```

## Configuration

The mDNS Bridge makes use of a configuration file provided by the [NMOS Common Library](https://github.com/bbc/nmos-common). Please see that repository for configuration details.

## Usage

On systems using systemd for service management (e.g Ubuntu >= 16.04) mdnsbridge may be run as a service. To enable the service create a symbolic link and start the service as follows:

```bash
sudo ln -s /lib/systemd/system/mdnsbridge.service /etc/systemd/system/multi-user.target.wants/mdnsbridge.service
sudo systemctl start mdnsbridge
```

### Non-blocking

Alternatively mdnsbridge may be run from a Python script. Run the following script to start the mDNS Brdige in a non-blocking manner, and then stop it again at a later point:

```Python
    from mdnsbridge.mdnsbridgeservice import mDNSBridgeService

    service = mDNSBridgeService()
    service.start()

    # Do something else until ready to stop

    service.stop()
```

### Blocking

It is also possible to run mDNS Bridge in a blocking manner:

```Python
    from mdnsbridge.mdnsbridgeservice import mDNSBridgeService

    service = mDNSBridgeService()
    service.run() # Runs forever
```

## Development

### Testing

```bash
# Run the tests
$ make test
```

### Packaging

Packaging files are provided for internal BBC R&amp;D use.
These packages depend on packages only available from BBC R&amp;D internal mirrors, and may not work in other environments. For use outside the BBC please use python installation method.

```bash
# Debian packaging
$ make deb

# RPM packaging
$ make rpm
```

## Versioning

We use [Semantic Versioning](https://semver.org/) for this repository

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

Please ensure you have run the test suite before submitting a Pull Request, and include a version bump in line with our [Versioning](#versioning) policy.

## License

See [LICENSE.md](LICENSE.md)
