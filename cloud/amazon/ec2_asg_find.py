#!/usr/bin/env python
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

DOCUMENTATION = '''
---
module: ec2_asg_find
short_description: Find autoscale groups.
description:
    - Find autoscale groups by name and retrieve the properties of each one.
version_added: "0.1"
author: Allen Sanabria <asanabria@linuxdynasty.org>
options:
  name:
    description:
      - The prefix or name of the auto scale groups you are searching for.
    required: true
  no_result_action:
    description:
      - If no results are return, you can either fail or succeed.
    required: false
    default: fail
    choices: [ 'success', 'fail' ]
  limit_results:
    description:
      - Fail if the number of results surpass this limit.
    required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Find a an AutoScaleGroup with name
- local_action:
    module: ec2_asg_find
    name: public-webserver-asg
  register: asg

# Fail if no AutoScaleGroups are found with name.
- local_action:
    module: ec2_asg_find
    name: public-webserver-asg
    no_result_action: fail
  register: asg

# Fail if more than the limit of 3 AutoScaleGroups is found.
- local_action:
    module: ec2_asg_find
    name: public-webserver-asg
    no_result_action: fail
    limit_results: 3
  register: asg
'''

RETURN = '''
autoscaling_group_arn:
    description: The Amazon ARN name of the ASG
    returned: success
    type: string
    sample: "arn:aws:autoscaling:us-west-2:722373842436:autoScalingGroup:10787c52-0bcb-427d-82ba-c8e4b008ed2e:autoScalingGroupName/public-webapp-production-1",
availability_zones:
    description: List of Availabily Zones that are a part of this ASG.
    returned: success
    type: list
    sample: ["us-west-2a", "us-west-2b", "us-west-2a"]
created_time:
    description: The time this ASG was created.
    returned: success
    type: string
    sample: "2015-11-25T00:05:36.309Z"
default_cooldown:
    description: The default_cooldown time.
    returned: success
    type: int
    sample: 300
desired_capacity:
    description: The number of EC2 instances that should be running in this group.
    returned: success
    type: int
    sample: 3
health_check_period:
    description: Length of time in seconds after a new EC2 instance comes into service that Auto Scaling starts checking its health.
    returned: success
    type: int
    sample: 30
health_check_type:
    description: The service you want the health status from, Amazon EC2 or Elastic Load Balancer.
    returned: success
    type: str
    sample: "ELB"
instance_id:
    description: The ID of the Amazon EC2 instance you want to use to create the Auto Scaling group.
    returned: success
    type: str
    sample: "i-es22ad25"
instances:
    description: List of EC2 instances and its status as it relates to the ASG.
    returned: success
    type: list
    sample: [
        {
            "ProtectedFromScaleIn": "false",
            "availability_zone": "us-west-2a",
            "group_name": None,
            "health_status": "Healthy",
            "instance_id": "i-es22ad25",
            "launch_config_name": "public-webapp-production-1",
            "lifecycle_state": "InService"
        }
    ]
launch_config_name:
    description: Name of launch configuration.
    returned: success
    type: str
    sample: "public-webapp-production-1"
load_balancers:
    description: List of load balancers.
    returned: success
    type: list
    sample: ["elb-webapp-prod"]
max_size:
    description: Maximum size of group
    returned: success
    type: int
    sample: 3
min_size:
    description: Minimum size of group
    returned: success
    type: int
    sample: 1
name:
    description: Name of autoscaling group.
    returned: success
    type: str
    sample: "public-webapp-production-1"
NewInstancesProtectedFromScaleIn:
    description: Are new instances protected from the scale in policy
    returned: success
    type: boolean
    sample: "false"
placement_group:
    description: Physical location of your cluster placement group created in Amazon EC2.
    returned: success
    type: str
    sample: None
tags:
    description: List of Tags
    returned: success
    type: list
    sample: [
        {
            "key": "Name",
            "value": "public-webapp-production-1"
        },
        {
            "key": "env",
            "value": "production"
        }
    ]
termination_policies:
    description: A list of termination policies.
    returned: success
    type: str
    sample: ["Default"]
'''

try:
    import boto.ec2.autoscale
    HAS_BOTO=True
except ImportError:
    HAS_BOTO=False

ASG_KEYS = [
    'default_cooldown', 'instances', 'health_check_period', 'created_time',
    'availability_zones', 'desired_capacity', 'max_size',
    'placement_group', 'NewInstancesProtectedFromScaleIn', 'tags',
    'autoscaling_group_arn', 'min_size', 'vpc_zone_identifier',
    'load_balancers', 'launch_config_name', 'name', 'termination_policies',
    'instance_id', 'health_check_type'
]

INSTANCE_KEYS = [
    'lifecycle_state', 'availability_zone', 'health_status', 'group_name',
    'instance_id', 'ProtectedFromScaleIn', 'launch_config_name'
]

TAG_KEYS = ['key', 'value']

def search(asgs, name):
    """
    Args:
        asgs (ResultSet): List of AutoScalingGroup instances.
        name (str): The name or prefix of the ASG you are looking for.

    Basic Usage:
        >>> conn = boto.ec2.autoscale.connect_to_region("us-west-2")
        >>> asgs = conn.get_all_groups()
        >>> results = search(asgs, "prod-web-app")

    Returns:
        List
    """
    matched_asgs = []
    if len(asgs) > 0:
        for asg in asgs:
            asg = dict((attr, getattr(asg, attr)) for attr in ASG_KEYS)
            matched =  re.search(r'^' + name, asg.get('name'))
            if matched:
                matched_asgs.append(asg)
    return matched_asgs

def convert_into_dict(objects, object_keys=None):
    """
    Args:
        objects (ResultSet): List of objects.

    Kwargs:
        object_keys (list): List of keys you want to pull from the object.

    Basic Usage:
        >>> conn = boto.ec2.autoscale.connect_to_region("us-west-2")
        >>> asgs = conn.get_all_groups()
        >>> tags = convert_into_dict(asgs[0].tags, object_keys=TAG_KEYS)

    Returns:
        List
    """
    results = []
    if len(objects) > 0:
        for instance  in objects:
            instance = dict(
                (attr, getattr(instance, attr)) for attr in object_keys
            )
            results.append(instance)
    return results

def convert_tags_into_dict(tags):
    return convert_into_dict(tags, object_keys=TAG_KEYS)

def convert_instances_into_dict(instances):
    return convert_into_dict(instances, object_keys=INSTANCE_KEYS)

def convert_string_into_list(subnet_ids):
    """
    Args:
        subnet_ids (str): List of subnet ids in a string format

    Basic Usage:
        >>> subnet_ids = "us-west-2a,us-west-2b,us-west-2c"
        >>> subnet_ids_in_list = convert_string_into_list(subnet_ids)

    Returns:
        List
        [
            "us-west-2c",
            "us-west-2b",
            "us-west-2a"
        ]
    """
    subnet = re.compile(r'^subnet-[a-z0-9]+')
    formatted_subnets = []
    if subnet.search(subnet_ids):
        formatted_subnets = subnet_ids.split(',')
    return formatted_subnets

def find_asgs(name, conn):
    """
    Args:
        name (str): The name of the asg you are looking for.
        conn (boto.ec2.autoscale.AutoScaleConnection): Valid ASG Connection.

    Basic Usage:
        >>> name = 'public-webapp-production'
        >>> conn = boto.ec2.autoscale.connect_to_region("us-west-2")
        >>> results = find_asgs(name, conn)

    Returns:
        List
        [
            {
                "NewInstancesProtectedFromScaleIn": "false",
                "autoscaling_group_arn": "arn:aws:autoscaling:us-west-2:631972842436:autoScalingGroup:10787c52-0bcb-427d-82ba-c8e4b008ed2e:autoScalingGroupName/public-webapp-production-1",
                "availability_zones": [
                    "us-west-2c",
                    "us-west-2b",
                    "us-west-2a"
                ],
                "created_time": "2015-11-25T00:05:36.309Z",
                "default_cooldown": 300,
                "desired_capacity": 2,
                "enabled_metrics": [],
                "health_check_period": 300,
                "health_check_type": "ELB",
                "instance_id": None,
                "instances": [
                    {
                        "ProtectedFromScaleIn": "false",
                        "availability_zone": "us-west-2a",
                        "group_name": None,
                        "health_status": "Healthy",
                        "instance_id": "i-fc22ad25",
                        "launch_config_name": "public-webapp-production-1",
                        "lifecycle_state": "InService",
                    }
                ],
                "launch_config_name": "public-webapp-production-1",
                "load_balancers": [
                    "public-webapp-production"
                ],
                "max_size": 3,
                "min_size": 2,
                "name": "public-webapp-production-1",
                "placement_group": None,
                "tags": [
                    {
                        "key": "Name",
                        "value": "public-webapp-production-1"
                    },
                    {
                        "key": "env",
                        "value": "production"
                    }
                ],
                "termination_policies": [
                    "Default"
                ],
                "vpc_zone_identifier": [
                    "subnet-7243820e",
                    "subnet-355ea943",
                    "subnet-1354911d"
                ]
            }
        ]
    """
    asgs = []
    matched_asgs = []
    asg_groups = conn.get_all_groups()
    matched_asgs = search(asg_groups, name)
    for asg in matched_asgs:
        asg['tags'] = convert_tags_into_dict(asg['tags'])
        asg['instances'] = (
            convert_instances_into_dict(asg['instances'])
        )
        asg['vpc_zone_identifier'] = (
            convert_string_into_list(asg['vpc_zone_identifier'])
        )
        asgs.append(asg)

    return asgs

def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(
                required=True, type='str'
            ),
            limit_results=dict(
                required=False, type='int', default=0
            ),
            no_result_action = dict(
                required=False, type='str', default='fail',
                choices = ['success', 'fail']
            ),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec)
    asg_name = module.params.get('name')
    no_result_action = module.params.get('no_result_action')
    limit_results = module.params.get('limit_results')
    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    try:
        conn = connect_to_aws(boto.ec2.autoscale, region, **aws_connect_params)
        if not conn:
            msg = (
                "failed to connect to AWS for the given region: {0}".
                format(str(region))
            )
            module.fail_json(msg=msg)
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))

    results = find_asgs(asg_name, conn)
    if limit_results > 0 and len(results) > limit_results:
        asg_names = map(lambda asg: asg.get('name'), results)
        msg = (
            "More than {0} ASG with name={1} found.".
            format(str(limit_results), name)
        )
        module.fail_json(msg=msg, asg_names=asg_names)

    elif no_result_action == 'fail' and not results:
        msg = "No results found for {0}.".format(name)
        module.fail_json(msg=msg)

    elif not results and no_result_action == 'success':
        output = {
            "changed" : False,
            "rc" : 0,
            "results": results
        }

    elif results:
        output = {
            "changed" : True,
            "rc" : 0,
            "results": results
        }

    module.exit_json(**output)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
