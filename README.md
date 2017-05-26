# ioant-examples
This repository holds self-contained device and entity examples. The examples are divided according to platform support.

- Generic: projects that can be run on multiple platforms.
- Espressif: projectts for e.g. esp8266.
- Raspberrypi: Projects that requires something inherent to the raspberrpi, e.g. a pi-camera

## Devices and Entities
Both devices and entities operate within the IOAnt platform. The main differences between the two are the following:
- **Devices**: Interact with the physical world by measuring or actuating. They should be viewed as simple, containing as little logic as possible. Devices are only aware of themselves.

- **Entities**: Act as decision makers within the platform. They contain application-logic and are aware of other devices and entities. An example would be an entity tasked for regulating the indoor temperature of a house. The entity will subscribe on multiple measurement-streams, use an algorithm to make a decision, and publish a message to a device in charge of operating a hot-water valve on a heater.

## How to run the examples
All examples require that you have a working python 2.7 environment. It is recommended to also have a virtual environment setup, but this is not mandatory. With python installed, the next step is to install the IOAnt pypi-package. All examples require this package to work.

```shell
# Install ioant package by using the PIP package manager
pip install ioant
```
Verify that you have ioant library installed by running pip freeze and find it in the list.

```shell
# List installed libraries
pip freeze
```

Finally install the protobuf compiler (version 3 or later) by running:

```shell
# List installed libraries
sudo apt-get install protobuf-compiler
```
### Note!
Some examples contain a Platformio project which require that you to install Platformio. Follow the official Platformio install instructions:
- [Install instructions Platformio (official)](http://platformio.org/get-started/ide?install)
