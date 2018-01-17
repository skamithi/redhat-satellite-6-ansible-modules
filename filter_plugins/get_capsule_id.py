#!/usr/bin/python

import unittest


def get_capsule_id(capsule_details, capsule_name, feature_name):
    """
    Parse the Capsule output info to get the capsule id
    return None if  capsule name selected does not have
    """
    capsule_entries = capsule_details.get('ansible_facts').get('satellite').get('capsules')
    for _capsule in capsule_entries:
        if _capsule.get('name').lower() == capsule_name.lower() and \
           feature_name.lower() in _capsule.get('features'):
            return int(_capsule.get('id'))
    return None


class FilterModule(object):
    """ This plugin module takes in ansible fact data from the satellite_facts module  and
    searches through the capsule data to return an ID. 2 arguments are required
    - capsule name
    - feature name
    Example:
       capsule_info | get_capsule_id('satellite.linuxsimba.local', 'realm')

    In the above example user wants to find the capsule id of a capsule called 'satellite.linuxsimba.local' and
    also ensure that it supports the 'realm' feature. If the capsule does not support realms then None is returned
    and the task fails.

    """

    def filters(self):
        return {
            'get_capsule_id': get_capsule_id
        }


class TestGetCapsuleID(unittest.TestCase):
    """
    test case for this filter plugin. to execute
    run ``python get_capsule_id.py``
    """
    def test_get_capsule_id(self):
        data = [{
            "name": "capsule1",
            "features": ["realm", "boogie"],
            "id": 2
        }, {
            "name": "capsule2",
            "features": ["boogie"],
            "id": 3
            }
        ]
        data = {'satellite': {'capsules': data}}
        self.assertEqual(get_capsule_id(data, 'capsule1', 'realm'), 2)
        self.assertEqual(get_capsule_id(data, 'capsule2', 'realm'), None)


if __name__ == '__main__':
    unittest.main()
