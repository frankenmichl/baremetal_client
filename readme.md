# Baremetal Support Client

This is a client for the baremetal support service (https://github.com/os-autoinst/baremetal_support).
It is a very early version and by no means complete.

## Overview
This is a client and helper for use with the baremetal support service. With the help of jinja2-templates,
it simplifies creation of bootscripts and optionally booting the machines using the configured script 
using ipmitool.

## Requirements
There's not much needed. If your system doesn't have the needed packages you can simply run it in a virtual
environment:

python3 -m venv venv
. venv/bin/activate
pip -r requirements.txt

Most likely you can install the dependencies also via your system's package manager or already have them.

## Configuration
The client uses a configuration file "config.yaml". An example (config.yaml.sample) is provided
with the source code and contains examples.
There's currently no support for specifying the configuration on the command line. Everything has to be in the
config file. 

## Usage
$ python client.py --help
usage: client.py [-h] --machine MACHINE --script SCRIPT [--version VERSION] [--build BUILD] [--verify] [--verbose] [--boot] [--sol]

Baremetal Support Service client

options:
  -h, --help         show this help message and exit
  --machine MACHINE  Configured machine alias in config.yaml
  --script SCRIPT    bootscript from config.yaml
  --version VERSION  Product version to use, i.e. 15-SP7
  --build BUILD      Build number to use, i.e. 47,1
  --verify           verify results on baremetal support service
  --verbose          enable verbose output
  --boot             boot machine using ipmitool
  --sol              connect to sol when done
  
For example: 
$ python client.py --machine foo --script install --version 15-SP7 --build 47.1 --verify --verbose --boot --sol

This will configure a boot script "install" (from the config file), verify the baremetal support service has 
the script stored (useful for debugging), show verbose outputs. When done, we will reboot the machine and boot
from network (--boot) and finally attach a Serial over Lan session (--sol). 


## Contributing
Feel free to report issues, improve documentation or send pull requests :) 
