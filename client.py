# Copyright (C) 2024 SUSE LLC
# SPDX-License-Identifier: FSFAP

import requests
import yaml
from jinja2 import Template
import argparse
import subprocess

def ipmitool(host, user, password, command):
  """
  Executes an ipmitool command and returns the output.

  Args:
    host: The IPMI host address.
    user: The IPMI username.
    password: The IPMI password.
    command: The ipmitool command to execute.

  Returns:
    The output of the command.
  """
  try:
    result = subprocess.run(
        ["ipmitool", "-I", "lanplus", "-H", host, "-U", user, "-P", password] + command.split(),
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()
  except subprocess.CalledProcessError as e:
    print(f"Error executing IPMI command: {e}")
    return None


class BaremetalClient:
    def __init__(self, config_file, verbose):
        """
        Initializes the BaremetalClient with configuration from config.yaml.

        Args:
            config_file (str): Path to the YAML configuration file.
        """
        with open(config_file) as f:
            self.config = yaml.safe_load(f)
        self.base_url = self.config.get("base_url", "http://localhost:5000")  # Default to localhost
        self.verbose = verbose

    def boot(self, machine_alias, sol):
        host = self.config["machines"][machine_alias].get("ipmi_host")
        user = self.config["machines"][machine_alias].get("ipmi_user")
        passwd = self.config["machines"][machine_alias].get("ipmi_password")

        options=""
        if self.config["machines"][machine_alias].get("UEFI") == 1:
            options="options=efiboot"
            
        ipmitool(host, user, passwd, "chassis power off")
        ipmitool(host, user, passwd, "chassis bootdev pxe " + options )
        ipmitool(host, user, passwd, "chassis power status")
        ipmitool(host, user, passwd, "chassis power on")

        if sol:
            ipmitool(host, user, passwd, "sol activate")
        
        
    def set_bootscript(self, machine_alias, bootscript_name, **template_vars):
        """
        Sets the bootscript for a machine from config.yaml.
        Args:
            machine_alias (str): Alias of the machine in the configuration.
            bootscript_name (str): Name of the bootscript in the configuration.
            **template_vars: Variables to be used in the bootscript template.
        """
        machine_ip = self.config["machines"][machine_alias].get("ip")
        if not machine_ip:
            raise ValueError(f"Machine alias '{machine_alias}' not found in configuration.")

        password = self.config.get("password")
        openqa = self.config.get("openqa")
        arch = self.config["machines"][machine_alias]["arch"]
        
        template_vars["arch"] = arch
        template_vars["openqa"] = openqa
        template_vars["password"] = password
        
        bootscript_template = self.config["bootscripts"].get(bootscript_name)
        if not bootscript_template:
            raise ValueError(f"Bootscript '{bootscript_name}' not found in configuration.")

        # Render the bootscript template
        template = Template(bootscript_template)
        self.bootscript = template.render(**template_vars)

        # Make the API call to set the bootscript
        url = f"{self.base_url}/v1/bootscript/script.ipxe/{machine_ip}"
        response = requests.post(url, data=self.bootscript)
        response.raise_for_status()

        if self.verbose:
            print("Machine: ", machine_alias, " (IP: ", machine_ip, ", Arch: " , arch, "):\nurl:", url, " \n", self.bootscript )
        
    def get_bootscript(self, machine_alias):
        machine_ip = self.config["machines"][machine_alias]["ip"]
        if not machine_ip:
            raise ValueError(f"MAchine alias '{machine_alias}' not found in configuration.")
        url = f"{self.base_url}/v1/bootscript/script.ipxe/{machine_ip}"
        response = requests.get(url)
        response.raise_for_status
        if self.verbose:
            print(response.text)
        return response.text
        

parser=argparse.ArgumentParser(description='Baremetal Support Service client')
parser.add_argument('--machine', required=True, help="Configured machine alias in config.yaml")
parser.add_argument('--script', required=True, help="bootscript from config.yaml")
parser.add_argument('--version', help="Product version to use, i.e. 15-SP7")
parser.add_argument('--build', help="Build number to use, i.e. 47,1")
parser.add_argument('--verify', action='store_true', help="verify results on baremetal support service")
parser.add_argument('--verbose', action='store_true', help="enable verbose output")
parser.add_argument('--boot', action='store_true', help="boot machine using ipmitool")
parser.add_argument('--sol', action='store_true', help='connect to sol when done')

args = parser.parse_args()
client = BaremetalClient("config.yaml", args.verbose)
machine = args.machine
bootscript = args.script


template_vars = {
    'version': args.version,
    'build': args.build
}

client.set_bootscript(machine, bootscript, **template_vars)
if args.verify:
    check = client.get_bootscript(machine)
    if check == client.bootscript:
        print("verification ok")
    else:
        print("verification failed")
        print("requested:")
        print(client.bootscript)
        print("on baremetal support:")
        print(check)

if args.boot:
    client.boot(machine, args.sol)
