# NMOS MDNS Bridge

This API provides a zeroconf/HTTP bridge for NMOS service types. The API will present itself at [http://localhost:12352/x-ipstudio/mdnsbridge/v1.0/](http://localhost:12352/x-ipstudio/mdnsbridge/v1.0/).

## Installing with Python

Before installing this library please make sure you have installed the [NMOS Common Library](https://github.com/bbc/nmos-common), on which this utility depends.

```
pip install setuptools
sudo python setup.py install
```

## Running

On systems using systemd for service management (e.g Ubuntu >= 16.04) mdnsbridge may be run as a service. To enable the service create a symbolic link and start the service as follows:

```
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

## Debian Packaging

Debian packaging files are provided for internal BBC R&D use.
These packages depend on packages only available from BBC R&D internal mirrors, and will not build in other environments. For use outside the BBC please use python installation method.

