from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: azure_keyvault_secret
    author:
        - Hai Cao <t-haicao@microsoft.com>
    version_added: 2.7
    requirements:
        - requests
        - azure
        - msrest
    short_description: Read secret from Azure Key Vault.
    description:
      - This lookup returns the content of secret saved in Azure Key Vault.
      - When ansible host is MSI enabled Azure VM, user don't need provide any credential to access to Azure Key Vault.
    options:
        _terms:
            description: Secret name, version can be included like secret_name/secret_version.
            required: True
        vault_url:
            description: Url of Azure Key Vault.
            required: True
        client_id:
            description: Client id of service principal that has access to the Azure Key Vault
        secret:
            description: Secret of the service principal.
        tenant_id:
            description: Tenant id of service principal.
    notes:
        - If version is not provided, this plugin will return the latest version of the secret.
        - If ansible is running on Azure Virtual Machine with MSI enabled, client_id, secret and tenant isn't required.
        - For enabling MSI on Azure VM, please refer to this doc https://docs.microsoft.com/en-us/azure/active-directory/managed-service-identity/
        - After enabling MSI on Azure VM, remember to grant access of the Key Vault to the VM by adding a new Acess Policy in Azure Portal.
        - If MSI is not enabled on ansible host, it's required to provide a valid service principal which has access to the key vault.
"""

EXAMPLE = """
- name: Look up secret when ansible host is MSI enabled Azure VM
  debug: msg="the value of this secret is {{lookup('azure_keyvault_secret','testSecret/version',vault_url='https://yourvault.vault.azure.net')}}"
- name: Look up secret when ansible host is general VM
  vars:
    url: 'https://yourvault.vault.azure.net'
    secretname: 'testSecret/version'
    client_id: '123456789'
    secret: 'abcdefg'
    tenant: 'uvwxyz'
  debug: msg="the value of this secret is {{lookup('azure_keyvault_secret',secretname,vault_url=url, cliend_id=client_id, secret=secret, tenant_id=tenant)}}"
# Example below creates an Azure Virtual Machine with SSH public key from key vault using 'azure_keyvault_secret' lookup plugin.
- name: Create Azure VM
  hosts: localhost
  connection: local
  no_log: True
  vars:
    resource_group: myResourceGroup
    vm_name: testvm
    location: eastus
    ssh_key: "{{ lookup('azure_keyvault_secret','myssh_key') }}"
  - name: Create VM
    azure_rm_virtualmachine:
      resource_group: "{{ resource_group }}"
      name: "{{ vm_name }}"
      vm_size: Standard_DS1_v2
      admin_username: azureuser
      ssh_password_enabled: false
      ssh_public_keys:
        - path: /home/azureuser/.ssh/authorized_keys
          key_data: "{{ ssh_key }}"
      network_interfaces: "{{ vm_name }}"
      image:
        offer: UbuntuServer
        publisher: Canonical
        sku: 16.04-LTS
        version: latest
"""

RETURN = """
  _raw:
    description: secret content string
"""
import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.append(parent_dir)

import utils

from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        token = utils.acquire_token()
        vault_url = kwargs.pop('vault_url', None)

        if vault_url is None:
            raise AnsibleError('Failed to get valid vault url.')
        if token:
            return utils.lookup_secret_msi(token, terms, vault_url)
        else:
            return utils.lookup_secret_non_msi(terms, vault_url, kwargs)
