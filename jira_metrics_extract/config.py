import os
import yaml
from pydicti import odicti

from .cycletime import StatusTypes

class ConfigError(Exception):
    pass

# From http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=odicti):
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping
    )

    return yaml.load(stream, OrderedLoader)

def force_list(val):
    return val if isinstance(val, (list, tuple,)) else [val]

def config_to_options(data):
    config = ordered_load(data, yaml.SafeLoader)
    options = {
        'connection': {
            'domain': os.environ.get('JIRA_DOMAIN', None),
            'username': os.environ.get('JIRA_USERNAME', None),
            'password': os.environ.get('JIRA_PASSWORD', None),
            'token': os.environ.get('JIRA_TOKEN', None)
        },
        'settings': {
            'queries': [],
            'query_attribute': None,
            'fields': {},
            'known_values': {},
            'statusmapping':[],
            'cycle': [],

            'max_results': 1000,
            'quantiles': [0.3, 0.5, 0.75, 0.85, 0.95],
            'charts_from': None,
            'charts_to': None
        }
    }

    # Parse and validate Connection

    if 'connection' in config:
        options['connection'].update(config['connection'])

    if 'domain' not in options['connection']:
        raise ConfigError("No `Domain` set in the `Connection` section")

    # Cach Jira query to file?
    if 'Cache Jira' in config:
        options['settings']['cache_jira'] = config['Cache Jira']
    else:
        options['settings']['cache_jira'] = None


    # Parse Queries (list of Criteria) and/or a single Criteria

    def _parse_query_config(c):
        return {
            'value': c.get('value', None),
            'project': c.get('project', None),
            'issue_types': force_list(c.get('issue types', [])),
            'valid_resolutions': force_list(c.get('valid resolutions', [])),
            'jql_filter': c.get('jql', None)
        }

    if 'queries' in config:
        options['settings']['query_attribute'] = config['queries'].get('attribute', None)
        for query in config['queries']['criteria']:
            options['settings']['queries'].append(
                _parse_query_config(query)
            )

    if 'criteria' in config:
        options['settings']['queries'].append(
            _parse_query_config(config['criteria'])
        )

    if len(options['settings']['queries']) == 0:
        raise ConfigError("No `Criteria` or `Queries` section found")

    # Parse Workflow. Assume first status is backlog and last status is complete.

    if 'workflow' not in config:
        raise ConfigError("`Workflow` section not found")

    if len(config['workflow'].keys()) < 2:
        raise ConfigError("`Workflow` section must contain at least two statuses")

    # If it in the config file get column state mappings
    if 'Workflow StatusTypes Mapping' in config:
        options['settings']['statusmapping'] = dict(config['Workflow StatusTypes Mapping'])

    for name, statuses in config['workflow'].items():
        statuses = force_list(statuses)

        try:
            status = options['settings']['statusmapping'].get(name)
        except AttributeError:
            status = 'committed'

        options['settings']['cycle'].append({
        "name": name,
        #"type": StatusTypes.accepted,
        "type": status,
        "statuses": statuses
        })

    if not 'Workflow StatusTypes Mapping' in config:
        # First one is always of status backlog
        options['settings']['cycle'][0]['type'] = StatusTypes.backlog
        # Last one is always of status complete
        options['settings']['cycle'][-1]['type'] = StatusTypes.complete

    # Parse attributes (fields)

    if 'attributes' in config:
        options['settings']['fields'] = dict(config['attributes'])

    if 'known values' in config:
        for name, values in config['known values'].items():
            options['settings']['known_values'][name] = force_list(values)

    if 'max results' in config:
        options['settings']['max_results'] = config['max results']
    if 'quantiles' in config:
        options['settings']['quantiles'] = force_list(config['quantiles'])
    if 'charts from' in config:
        options['settings']['charts_from'] = config['charts from']
    if 'charts to' in config:
        options['settings']['charts_to'] = config['charts to']

    return options
