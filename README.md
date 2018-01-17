# Red Hat Satellite 6.x Ansible Modules

This repo contains Ansible Modules and filters for managing
a Red Hat Satellite 6.X server

Red Hat Satellite 6.X provides a REST API. This REST API
is the backbone of this git repository


## Modules

* ``satellite_facts``: Collects facts about Red Hat Satellite
* ``satellite_realms``: Creates and modify Red Hat Satellite Realms

## Filters

* ``get_capsule_id``: Given a ``capsule name`` and satellite feature, this filter returns a matching capsule ID.

## Examples

A sample playbook called ``test_playbook.yml`` is included to showcase the modules

## License

MIT


## Notes

Not sure how much time I will have to complete this project. It will
depend on how many Satellite provisioning projects I get.
