#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: elasticache_tag
short_description: Manage Tags for ElastiCache
description:
    - Update tags for an ElastiCache Cluster (This is idempotent)
    - When adding tags, if a tag exists and is not in the dictionary, it will be removed.
    - Remove Tags from an ElastiCache Cluster.
version_added: "2.2"
author: Allen Sanabria (@linuxdynasty)
options:
  name:
    description:
      - "The name of the ElastiCache Cluster."
    required: true
  state:
    description:
      - "Add or Remove tags from an ElastiCache Cluster."
    required: false
    default: present
    choices: [ 'present', 'absent' ]
  tags:
    description:
      - "A dictionary of resource tags of the form: { tag1: value1, tag2: value2 }."
    required: true
    aliases: [ "resource_tags" ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Add tags:
- name: Add a couple of tags (This will remove any other tags, that are not in the tags dictionary, as well as update the tags that are in this dictionary)
  elasticache_tag:
    name: test-cache
    tags:
      Env: development
      Service: webapp
  register: tags

# Remove the Service tag:
- name: Remove a tag
  elasticache_tag:
    name: test-cache
    tags:
      Service: webapp
  register: tags
'''

RETURN = '''
name:
  description: The name of the ElastiCache Cluster.
  returned: always
  type: string
  sample: "test-stream"
arn:
  description: The Amazon Resource identifier of the ElastiCache Cluster.
  returned: always
  type: string
  sample: "arn:aws:elasticache:us-west-2:1234567898765:cluster:test"
tags:
  description: Dictionary containing all the tags associated with the Resource Name.
  returned: always
  type: dict
  sample: {
      "Name": "Splunk",
      "Env": "development"
  }
'''

try:
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def create_client(region, resource_name='ec2'):
    """ Create a new boto3 client for resource_name
    Args:
        region (str): The aws region you want to connect to.
        resource_name (str): Valid aws resource.
            default=ec2

    Basic Usage:
        >>> client, err_msg = create_client('us-west-2')

    Returns:
        Tuple (botocore.client.EC2, str)
    """
    client = None
    err_msg = ''
    try:
        session = (
            boto3.session.Session(region_name=region)
        )
        client = session.client(resource_name)
    except Exception as e:
        err_msg = str(e)

    return client, err_msg

def make_tags_in_proper_format(tags):
    """Take a dictionary of tags and convert them into the AWS Tags format.
    Args:
        tags (list): The tags you want applied.

    Basic Usage:
        >>> tags = [{'Key': 'env', 'Value': 'development'}]
        >>> make_tags_in_proper_format(tags)
        {
            "env": "development",
        }

    Returns:
        Dict
    """
    formatted_tags = dict()
    for tag in tags:
        formatted_tags[tag.get('Key')] = tag.get('Value')

    return formatted_tags

def make_tags_in_aws_format(tags):
    """Take a dictionary of tags and convert them into the AWS Tags format.
    Args:
        tags (dict): The tags you want applied.

    Basic Usage:
        >>> tags = {'env': 'development', 'service': 'web'}
        >>> make_tags_in_proper_format(tags)
        [
            {
                "Value": "web",
                "Key": "service"
             },
            {
               "Value": "development",
               "key": "env"
            }
        ]

    Returns:
        List
    """
    formatted_tags = list()
    for key, val in tags.items():
        formatted_tags.append({
            'Key': key,
            'Value': val
        })

    return formatted_tags

def get_tags(client, resource_name, check_mode=False):
    """Retrieve the tags for a resource.
    Args:
        client (botocore.client.EC2): Boto3 client.
        resource_name (str): The Amazon Resource Identifier.

    Kwargs:
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('elasticache')
        >>> resource_name = 'test-stream'
        >> get_tags(client, resource_name)

    Returns:
        Tuple (bool, str, dict)
    """
    err_msg = ''
    success = False
    params = {
        'ResourceName': resource_name,
    }
    results = dict()
    try:
        if not check_mode:
            results = (
                client.list_tags_for_resource(**params)['TagList']
            )
        else:
            results = [
                {
                    'Key': 'DryRunMode',
                    'Value': 'true'
                },
            ]
        success = True
    except botocore.exceptions.ClientError, e:
        err_msg = str(e)

    return success, err_msg, results

def tags_action(client, resource_name, tags, action='create', check_mode=False):
    """Create or delete multiple tags for a Resource Name.
    Args:
        client (botocore.client.EC2): Boto3 client.
        resource_name (str): The Amazon Resource Name.
        tags (list): List of dictionaries.
            examples.. [{Name: "", Values: [""]}]

    Kwargs:
        action (str): The action to perform.
            valid actions == create and delete
            default=create
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('elasticache')
        >>> resource_name = "arn:aws:elasticache:us-west-2:123456789876:cluster:test"
        >>> tags = [{'Name': 'env', 'Value': 'development'}]
        >>> tags_action(client, resource_name, tags)
        [True, '']

    Returns:
        List (bool, str)
    """
    success = False
    err_msg = ""
    params = {'ResourceName': resource_name}
    try:
        if not check_mode:
            if action == 'create':
                params['Tags'] = tags
                client.add_tags_to_resource(**params)
                success = True
            elif action == 'delete':
                params['TagKeys'] = tags.keys()
                client.remove_tags_from_resource(**params)
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)
        else:
            if action == 'create':
                success = True
            elif action == 'delete':
                success = True
            else:
                err_msg = 'Invalid action {0}'.format(action)

    except botocore.exceptions.ClientError, e:
        err_msg = str(e)

    return success, err_msg

def add(client, resource_name, tags, check_mode=False, diff_mode=False):
    """Add tags to a resource.
    Args:
        client (botocore.client.EC2): Boto3 client.
        resource_name (str): Resource Name of the resource you are modifying.
        tags (list): List of dictionaries.

    Kwargs:
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('elasticache')
        >>> resource_name = 'test'
        >>> tags = [{'env': 'test'}]
        >> add(client, resource_id)

    Returns:
        Tuple (bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    diff = dict()
    retrieve_success, retrieve_msg, current_tags = (
        get_tags(client, resource_name)
    )
    if diff_mode:
        diff['before'] = make_tags_in_proper_format(current_tags)
        diff['after'] = tags
        success = True
    else:
        current_tags = make_tags_in_proper_format(current_tags)
        tags_to_update = dict()
        for key in tags.keys():
            if current_tags.has_key(key):
                if current_tags[key] != tags[key]:
                    tags_to_update[key] = tags[key]
            else:
                tags_to_update[key] = tags[key]
        if tags_to_update:
            tags = make_tags_in_aws_format(tags)
            success, err_msg = (
                tags_action(
                    client, resource_name, tags, 'create', check_mode
                )
            )
            if success:
                changed = True
                err_msg = (
                    'Tags {0} updated'.format(make_tags_in_proper_format(tags))
                )
        else:
            success = True
            changed = False
            err_msg = 'Nothing to update'
        _, _, new_tags = (
            get_tags(client, resource_name)
        )
        tags = make_tags_in_proper_format(new_tags)
    return success, changed, err_msg, tags, diff

def remove(client, resource_name, tags, check_mode=False, diff_mode=False):
    """Remove tags from a resource.
    Args:
        client (botocore.client.EC2): Boto3 client.
        resource_name (str): Resource Name of the resource you are modifying.
        tags (list): List of dictionaries.

    Kwargs:
        check_mode (bool): This will pass DryRun as one of the parameters to the aws api.
            default=False

    Basic Usage:
        >>> client = boto3.client('elasticache')
        >>> resource_name = 'test'
        >>> tags = [{'env': 'test'}]
        >> remove(client, resource_id)

    Returns:
        Tuple (bool, str, dict)
    """
    success = False
    changed = False
    err_msg = ''
    diff = dict()
    retrieve_success, retrieve_msg, current_tags = (
        get_tags(client, resource_name)
    )
    if diff_mode:
        diff['before'] = make_tags_in_proper_format(current_tags)
        diff['after'] = make_tags_in_proper_format(current_tags)
        for tag in tags:
            diff['after'].pop(tag)
        success = True
    else:
        current_tags = make_tags_in_proper_format(current_tags)
        tags_to_delete = dict()
        for key in tags.keys():
            if current_tags.has_key(key):
                tags_to_delete[key] = tags[key]
        if tags_to_delete:
            success, err_msg = (
                tags_action(
                    client, resource_name, tags_to_delete, 'delete', check_mode
                )
            )
            if success:
                changed = True
        else:
            success = True
            err_msg = (
                'Tags {0} do not exist for resource {1}'
                .format(tags, resource_name)
            )
        _, _, new_tags = (
            get_tags(client, resource_name)
        )
        tags = make_tags_in_proper_format(new_tags)
    return success, changed, err_msg, tags, diff

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name = dict(default=None, required=True, type='str'),
            tags = dict(default=None, required=True, type='dict', aliases=['resource_tags']),
            state = dict(default='present', choices=['present', 'absent']),
        )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    name = module.params.get('name')
    state = module.params.get('state')
    tags = module.params.get('tags')

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    check_mode = module.check_mode
    diff_mode = False
    try:
        region, ec2_url, aws_connect_kwargs = (
            get_aws_connection_info(module, boto3=True)
        )
        client = (
            boto3_conn(
                module, conn_type='client', resource='elasticache',
                region=region, endpoint=ec2_url, **aws_connect_kwargs
            )
        )
    except botocore.exceptions.ClientError, e:
        err_msg = 'Boto3 Client Error - {0}'.format(str(e.msg))
        module.fail_json(
            success=False, changed=False, result={}, msg=err_msg
        )

    iam_client, err_msg = create_client(region, 'iam')
    if err_msg:
        module.fail_json(
            success=False, changed=False, result={}, msg=err_msg
        )
    account_id = iam_client.list_users()['Users'][0]['Arn'].split(':')[4]
    arn = (
        "arn:aws:elasticache:{0}:{1}:cluster:{2}"
        .format(region, account_id, name)
    )

    if state == 'present':
        success, changed, err_msg, results, diff = (
            add(client, arn, tags, check_mode, diff_mode)
        )
    elif state == 'absent':
        success, changed, err_msg, results, diff = (
            remove(client, arn, check_mode, diff_mode)
        )
    exit_results = dict()
    exit_results['success'] = success
    exit_results['changed'] = changed
    exit_results['err_msg'] = err_msg
    exit_results['tags'] = results
    exit_results['arn'] = arn
    exit_results['name'] = name
    if diff_mode:
        exit_results['diff'] = diff

    if success:
        module.exit_json(**exit_results)
    else:
        module.fail_json(**exit_results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
