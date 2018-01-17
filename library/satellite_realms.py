#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018 Stanley Karunditu <stanley@linuxsimba.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: satellite_realms
short_description: Configure Red Hat Satellite 6.X realms
description:
  - Configure Red Hat Satellite 6.X realms
author: Stanley Karunditu (@linuxsimba)
options:
    hostname:
        description:
            - FQDN or IP of Satellite Server. This only needs to be
            - set when running the module using "connection:local"
        default: localhost
    url_username:
        description:
            - Username to access satellite REST API resources
        required: true
    url_password:
        description:
            - Password to access satellite Rest API resources
        required: true
    realm_name:
        description:
            - Name of the Satellite Realm
            required: true
    realm_capsule_id:
        description:
            - ID of capsule that has the Realm Feature
        required: true
    realm_type:
        description:
            - Realm Type. Can be either "Red Hat Identity Management"
            - or "Active Directory"
        choices: ["Red Hat Identity Management", "Active Directory"]
        default: "Red Hat Identity Management"
    realm_organization_ids:
        description:
            - Realm Organization. Input a list of organization IDs
        required: True
    realm_location_ids:
        description:
            - Realm Location. Input a list of location IDs
        required: False
    state:
        description:
            - Create or remove a Realm
        default: present
        choices: ['present', 'absent']

'''

EXAMPLES = '''
# Set a Realm. First gather capsule info first.
satellite_facts:
    url_username: "{{ vault_satellite_user }}"
    url_password: "{{ vault_satellite_pass }}"
    gather_subsets:
        - capsule
        - organization
    register: satellite_info

# Use get_capsule_id Ansible filter which takes 2 arguments
# get_capsule_id(<capsule name>, <feature>).
# If the capsule has that feature then
# it returns that ID
satellite_realms:
    url_username: "{{ vault_satellite_user }}"
    url_password: "{{ vault_satellite_pass }}"
    realm_name: "first realm"
    realm_capsule_id: satellite_info | get_capsule_id('satellite.linuxsimba.local', 'Realm')
    realm_type: "Active Directory"
    state: present

'''

from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class SatelliteRealm(object):
    def __init__(self, module):

        self.module = module
        self.msg = ''
        self.changed = False

    def delete_object(self, uri):
        url = "https://%s%s/%s" % (self.module.params.get('hostname'),
                                   uri, self.module.params.get('realm_name'))
        resp, info = fetch_url(self.module, url, data=None,headers={"Content-type": "application/json"},
                               method="DELETE")
        if info.get('exception'):
            self.module.fail_json(msg=info.get('exception'))
        if info.get('status') == 404:
            return (False,'Realm already removed')
        if info.get('status') == 200:
            return (True, "Realm %s removed" % (self.module.params.get('realm_name')))

    def url(self, uri):
        _url = "https://%s%s" % (self.module.params.get('hostname'), uri)
        resp, info = fetch_url(self.module,
                               _url,
                               data=None,
                               headers={'Content-type': 'application/json'},
                               method="GET")
        if info.get('exception'):
            self.module.fail_json(msg=info.get('exception'))
        body = resp.read()
        body = self.module.from_json(body.strip())
        if body.get('page') and body.get('total'):
            page_num = int(body.get('page'))
            total_pages = int(body.get('total'))
            while (page_num <= total_pages):
                new_page_num = int(body.get('page')) + 1
                _uri = uri.split('?')[0] + "?page=" + str(new_page_num)
                body = body.get('results')
                return body + self.url(_uri)
            return []
        return body

    def does_realm_exist(self):
        realms = self.url('/api/realms')
        for _entry in realms:
            if _entry.get('name') == self.module.params.get('realm_name'):
                self.msg = _entry
                return True
        return False

    def create_realm(self):
        uri = '/api/realms'
        _data = {
            "name": self.module.params.get('realm_name'),
            "realm_proxy_id": self.module.params.get('realm_capsule_id'),
            "realm_type": self.module.params.get('realm_type'),
            "organization_ids": self.module.params.get('realm_organization_ids'),
            "location_ids": self.module.params.get('realm_location_ids')
        }

        _url = "https://%s%s" % (self.module.params.get('hostname'), uri)
        resp, info = fetch_url(self.module,
                               _url,
                               data=self.module.jsonify(_data),
                               headers={'Content-type': 'application/json'},
                               method="POST")
        if info.get('exception'):
            self.module.fail_json(msg=info.get('exception'))
        body = resp.read()
        body = self.module.from_json(body.strip())
        self.msg = body
        self.changed = True

    def set_realm(self):
        if not self.does_realm_exist():
            self.create_realm()
        return (self.changed, self.msg)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(default='localhost', type='str'),
            url_username=dict(required=True, type='str'),
            url_password=dict(required=True, type='str',
                          no_log=True),
            realm_name=dict(required=True, type='str'),
            realm_type=dict(default="Red Hat Identity Management", type='str',
                            choices=["Red Hat Identity Management",
                                     "Active Directory"]),
            realm_capsule_id=dict(required=True, type='int'),
            realm_organization_ids=dict(required=True, type='list'),
            realm_location_ids=dict(required=False, type='list', default=[]),
            state=dict(default='present', type=str)
        ),
        supports_check_mode=False
    )

  # disable checking cert and force basic auth. may change in the future
    module.params['force_basic_auth'] = True
    module.params['validate_certs'] = False

    satellite_realm = SatelliteRealm(module)
    results = {}
    results['changed'] = False
    if module.params.get('state') == 'present':
        (results['changed'], results['msg']) = satellite_realm.set_realm()
    else:
        (results['changed'], results['msg']) = satellite_realm.delete_object('/api/realms')
    module.exit_json(**results)


if __name__ == '__main__':
    main()
