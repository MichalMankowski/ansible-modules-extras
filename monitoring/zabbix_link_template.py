#!/usr/bin/python

# (c) 2016, Michal Mankowski <michal.mankowski () intel.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible.module_utils.basic import *
try:
    from pyzabbix import ZabbixAPI
    HAS_ZABBIX = True
except ImportError:
    HAS_ZABBIX = False

DOCUMENTATION = '''
---
module: zabbix_update
short_description: Link/unlink given hosts list with given templates list
description:
  - Link/unlink given hosts list with given templates list

version_added: "2.3"
author: "Michal Mankowski (@MichalMankowski)"
requirements:
  - "python >= 2.6"
  - "pyzabbix >= 0.7.2"
options:
  server_url:
     description:
         - Address of zabbix server
     required: True
  login_user:
     description:
         - name of user to login to zabbix
     required: True
  login_password:
     description:
         - password for user to login to zabbix
     reuqierd: True
  host:
     description:
         - list of hosts to update
     required: True
     aliases: ['hosts']
  template:
     description:
         - list of templates to link/unlink
     required: True
     aliases: ['templates']
  state:
     description:
         - state present link list of templates, absent unlink list of templates
     required: False
     choices: [ present, absent]
     default: "present"
'''

EXAMPLES = '''
---
- name: link templates
  local_action:
    module: zabbix_update
    server_url: "http://127.0.0.1"
    username: "test"
    password: "test"
    template:
    - "Template App HTTP Service"
    - "Template App LDAP Service"
    host:
    - "Zabbix server"
    - "Linux server"
    state: present
'''

RETURN = '''
#defaults
'''


def link_templates(template_ids, host_ids, state, zapi, check_mode):
    for host in host_ids:
        for template in template_ids:
            if state == "present" and not check_mode:
                zapi.host.massadd(hosts=host, templates=template)
            elif state == "absent" and not check_mode:
                zapi.host.update(hostid=host, templates_clear=template)


def get_resource_ids(zabbix_resources, filter_list, filter_field, result_field):
    filtered_results = [item for item in zabbix_resources if item[filter_field] in filter_list]
    diff = set(filter_list).difference(set([item[filter_field] for item in filtered_results]))
    if len(diff):
        raise Exception("Resources not found: {}".format(", ".join(diff)))
    return [item[result_field] for item in filtered_results]


def main():
    fields = {
        "server_url": {"required": True, "type": "str"},
        "login_user": {"required": True, "type": "str"},
        "login_password": {"required": True, "type": "str", "no_log": True},
        "template": {"required": True, "type": "list", "aliases": ['templates']},
        "host": {"required": True, "type": "list", "aliases": ['hosts']},
        "state": {
            "default": "present",
            "choices": ['present', 'absent'],
            "type": "str"
        },
    }

    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)
    if not HAS_ZABBIX:
        module.fail_json(msg="Missing required lib pyzabbix")

    login_user = module.params['login_user']
    login_password = module.params['login_password']
    state = module.params['state']
    server_url = module.params['server_url']

    # login to zabbix api
    try:
        zapi = ZabbixAPI(server_url)
        zapi.login(login_user, login_password)
        check_mode = module.check_mode
        # get host id and template , then link them to each other
        host_ids = get_resource_ids(zapi.host.get(), module.params['host'], 'name', 'hostid')
        template_ids = get_resource_ids(zapi.template.get(), module.params['template'], 'host', 'templateid')
        link_templates(template_ids, host_ids, state, zapi, check_mode)
        module.exit_json(changed=True)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
