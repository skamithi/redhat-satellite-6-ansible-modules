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
module: satellite_facts
short_description: Gather facts about a Satellite Server
description:
  - Gather facts from a Satellite Server 6.X server
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
    gather_subsets:
        description:
            - list of facts of list. Options are
            - "all,domain,host,location,capsule,operatingsystem,smart_proxy,organization"
        default: all
'''

EXAMPLES = '''
# Gather All Satellite Facts
satellite_facts:
    url_username: "{{ vault_satellite_user }}"
    url_password: "{{ vault_satellite_pass }}"

# Only Gather smart proxies and domains
satellite_facts:
    url_username: "{{ vault_satellite_user }}"
    url_password: "{{ vault_satellite_pass }}"
    gather_subsets:
        - smart_proxy
        - domain
'''

RETURN = '''
satellite:
    services:
        - service: candlepin
          status: true
        - service: candlepin_auth
          status: true
    ....
    capsules:
        - name:
          id:
          features: []
    locations:
      ....(array of locations)
    domains:
     ....(array of domains)
    hosts:
     ...(array of hosts)
    operatingsystems:
    ...(array of operatingsystems)
    smart_proxies:
    ...(array of smart proxies)
'''

from ansible.module_utils.six import iteritems
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class SatelliteFacts(object):
    def __init__(self, module):

        self.module = module
        self.name = "red hat satellite"
        self.status = {
            "candlepin": None,
            "candlepin_auth": None,
            "foreman_tasks": None,
            "pulp": None,
            "pulp_auth": None
        }

        self.facts = {}

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

    def get_hosts(self):
        """
        get host list
        """
        self.facts['hosts'] = self.url('/api/hosts')

    def get_organizations(self):
        """
        get org list
        """
        self.facts['organizations'] = self.url('/api/organizations')

    def get_domains(self):
        """
        Get Domains
        """
        self.facts['domains'] = self.url('/api/domains')

    def get_smart_proxy(self):
        """
        Get Smart Proxy
        """
        self.facts['smart_proxies'] = self.url('/api/smart_proxies')

    def get_locations(self):
        """
        Get Locations
        """
        self.facts['locations'] = self.url('/api/locations')

    def get_status(self):
        """
        Get Status from /api/status from Satellite
        """
        status_result = self.url('/katello/api/ping')
        self.facts['services'] = []
        for k, v in iteritems(status_result.get('services')):
            _status = True if (v.get('status') == 'ok') else False
            self.facts['services'].append({'service': k, 'status': _status})

    def get_capsule_info(self):
        """
        List Capsule Information
        """
        capsule_facts = self.facts['capsules'] = []
        capsule_summary = self.url('/katello/api/capsules')
        for _entry in capsule_summary:
            capsule_details = self.url("/katello/api/capsules/%s" % (_entry.get('id')))
            features = []

            for _feature in capsule_details.get('features'):
                features.append(_feature.get('name').lower())

            capsule = {
                "features": features,
                "locations": capsule_details.get('location'),
                "id": capsule_details.get('id'),
                "organizations": capsule_details.get('organizations'),
                "name": capsule_details.get('name')
            }
            capsule_facts.append(capsule)

    def get_operatingsystems(self):
        """
        list operating system details
        """
        os_facts = self.facts['operatingsystems'] = []
        os_summary = self.url('/api/operatingsystems')
        for _entry in os_summary:
            os_details = self.url("/api/operatingsystems/%s" % (_entry.get('id')))
            os_facts.append(os_details)

    def get_facts(self):
        """
        Generate all facts to the self.facts dict
        """
        gather_subsets = self.module.params.get('gather_subsets')
        if 'all' in gather_subsets:
            self.get_status()
        if set(['all', 'smart_proxy']).issubset(gather_subsets):
            self.get_smart_proxy()
        if set(['all', 'capsule']).issubset(gather_subsets):
            self.get_capsule_info()
        if set(['all', 'location']).issubset(gather_subsets):
            self.get_locations()
        if set(['all', 'domain']).issubset(gather_subsets):
            self.get_domains()
        if set(['all', 'host']).issubset(gather_subsets):
            self.get_hosts()
        if set(['all', 'operatingsystem']).issubset(gather_subsets):
            self.get_operatingsystems()
        if set(['all', 'organization']).issubset(gather_subsets):
            self.get_organizations()
        return {'satellite': self.facts}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(default='localhost', type='str'),
            url_username=dict(required=True, type='str'),
            url_password=dict(required=True, type='str',
                          no_log=True),
            gather_subsets=dict(default=['all'], type='list')
        ),
        supports_check_mode=False
    )

    module.params['gather_subsets'] = \
        set(module.params['gather_subsets']) | set(['all'])

    # disable checking cert and force basic auth. may change in the future
    module.params['force_basic_auth'] = True
    module.params['validate_certs'] = False

    satellite_facts = SatelliteFacts(module)

    result = {}
    result['changed'] = False
    result['name'] = satellite_facts.name

    result['ansible_facts'] = satellite_facts.get_facts()

    module.exit_json(**result)


if __name__ == '__main__':
    main()
