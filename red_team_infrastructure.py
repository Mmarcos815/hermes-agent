#!/usr/bin/env python3
import json, os, subprocess
from pathlib import Path

class RedTeamInfrastructure:
    def __init__(self, config_dir="infrastructure/configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.inventory = []
    
    def generate_terraform(self, provider="aws", output_dir="infrastructure/terraform"):
        """Generate Terraform configs for C2 infrastructure."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        
        if provider == "aws":
            tf = f"""
provider "aws" {{
  region = "us-east-1"
}}

resource "aws_instance" "c2_server" {{
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  
  tags = {{
    Name = "c2-server"
  }}
}}

resource "aws_security_group" "c2_sg" {{
  name_prefix = "c2-sg"
  
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}
}}
"""
        elif provider == "azure":
            tf = """
provider "azurerm" {{
  features {{}}
}}

resource "azurerm_resource_group" "c2_rg" {{
  name     = "c2-resources"
  location = "East US"
}}

resource "azurerm_virtual_machine" "c2_vm" {{
  name                  = "c2-vm"
  location              = "East US"
  resource_group_name   = azurerm_resource_group.c2_rg.name
  vm_size               = "Standard_B1s"
}
"""
        
        output_file = output / f"{provider}.tf"
        output_file.write_text(tf)
        return output_file
    
    def generate_ansible(self, c2_type="sliver", output_dir="infrastructure/ansible"):
        """Generate Ansible playbook for C2 setup."""
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        
        if c2_type == "sliver":
            playbook = """
- name: Deploy Sliver C2
  hosts: c2_servers
  become: yes
  tasks:
    - name: Install dependencies
      apt:
        name: "wget,unzip"
        state: present
    - name: Download Sliver
      get_url:
        url: https://github.com/BishopFox/sliver/releases/latest/download/sliver-server_linux.zip
        dest: /tmp/sliver.zip
    - name: Install Sliver
      shell: |
        cd /opt && unzip /tmp/sliver.zip && chmod +x sliver-server
"""
        elif c2_type == "havoc":
            playbook = """
- name: Deploy Havoc C2
  hosts: c2_servers
  become: yes
  tasks:
    - name: Install dependencies
      apt:
        name: "git,build-essential"
        state: present
    - name: Clone Havoc
      git:
        repo: https://github.com/HavocFramework/Havoc.git
        dest: /opt/havoc
"""
        
        output_file = output / f"{c2_type}.yml"
        output_file.write_text(playbook)
        return output_file
    
    def create_inventory(self, name, ip, os_type="linux"):
        """Add server to inventory."""
        self.inventory.append({"name": name, "ip": ip, "os": os_type})
        return self.inventory
    
    def teardown(self, provider="aws"):
        """Generate teardown commands."""
        if provider == "aws":
            return "cd infrastructure/terraform && terraform destroy"
        elif provider == "azure":
            return "cd infrastructure/terraform && terraform destroy"
        return "Manual teardown required"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    
    p = sub.add_parser("terraform")
    p.add_argument("--provider", default="aws")
    p.add_argument("--output", default="infrastructure/terraform")
    
    p = sub.add_parser("ansible")
    p.add_argument("--type", default="sliver")
    p.add_argument("--output", default="infrastructure/ansible")
    
    p = sub.add_parser("inventory")
    p.add_argument("--name")
    p.add_argument("--ip")
    p.add_argument("--os", default="linux")
    
    p = sub.add_parser("teardown")
    p.add_argument("--provider", default="aws")
    
    args = parser.parse_args()
    infra = RedTeamInfrastructure()
    
    if args.cmd == "terraform":
        out = infra.generate_terraform(args.provider, args.output)
        print(f"Terraform: {out}")
    elif args.cmd == "ansible":
        out = infra.generate_ansible(args.type, args.output)
        print(f"Ansible: {out}")
    elif args.cmd == "inventory":
        inv = infra.create_inventory(args.name, args.ip, args.os)
        print(json.dumps(inv, indent=2))
    elif args.cmd == "teardown":
        print(infra.teardown(args.provider))
