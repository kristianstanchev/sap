#!/usr/bin/env python3
import os
from python_path import PythonPath
from landscape_tools import Context, bosh

with PythonPath(f"{os.environ['IAC_COMPONENT_DIR']}/lib"):
    from credhub import Credhub

class InvalidWorkerCount(Exception):
    pass

class WorkersChecker:
    def __init__(self):
        self.context = Context.load()
        self.credhub = Credhub(ctx=self.context)
        self.bosh_cli = self.bosh_login()

    def bosh_login(self):
        label = "workers_check_script"
        # Provision BOSH user
        script_path = self.context.context.imports.bosh.scripts.provision_client
        user_creds = bosh.provision_bosh_user(script_path, label)
        bosh_user = user_creds["client_id"]
        bosh_password = user_creds["client_secret"]

        # Get BOSH director connection info
        bosh_ip = self.context.context.imports.bosh.director.hostname_or_ip
        bosh_port = self.context.context.imports.bosh.director.port
        bosh_ca = self.credhub.cmds.getimportedcredential(
            ".context.imports.bosh.director.ca_cert"
        )
        # Initialize BOSH CLI
        bosh_cli = bosh.BoshCli(
            url=f"https://{bosh_ip}:{bosh_port}",
            ca_cert=bosh_ca,
            client=bosh_user,

            client_secret=bosh_password,
        )
        return bosh_cli
        # self.bosh = bosh.Bosh(cli=bosh_cli)


    def fetch_vms(self):
        vm_data = self.bosh_cli._vms(deployment_name="concourse", print_command=False) # извиква метод _vms като му подава атрибути, първия е задължителен. втория е за да не ми принтира некви глупости
        return vm_data["Tables"][0]["Rows"]
    
    def count_bosh_vms(self, bosh_workers_data) ->  int:
        count_vms = 0
        for bosh_vm in bosh_workers_data:
            vm_name = bosh_vm["instance"]
            vm_state = bosh_vm["process_state"]
            if vm_name.startswith("worker-product-cf/") and vm_state == "running":
                count_vms += 1
        return count_vms
    
    def execute(self):
        context_workers_count = int(self.context.context.config.worker_product_cf.instances)
        bosh_workers_data = self.fetch_vms()
        valid_workers_count = self.count_bosh_vms(bosh_workers_data=bosh_workers_data)
        print(f"this is the workers count in the config: {context_workers_count}")
        print(f"this is the workers count in running state: {valid_workers_count}")
        if context_workers_count != valid_workers_count:
            raise InvalidWorkerCount("Fail - The workers count doesn't match")
    
        print("Success, the workers count match")
            
        
if __name__ == "__main__":
    WorkersCheker().execute()
        