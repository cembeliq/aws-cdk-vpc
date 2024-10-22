from aws_cdk.aws_ec2 import RouterType, CfnSecurityGroup

# basic VPC configs
VPC = 'vpc-pintusukses'

INTERNET_GATEWAY = 'pintusukses-internet-gateway'

KEY_PAIR_NAME = 'pintusukses-ap-southeast-3-key'

REGION = 'ap-southeast-3'

# route tables
PUBLIC_ROUTE_TABLE = 'public-pintusukses-rtb'
PRIVATE_ROUTE_TABLE = 'private-pintusukses-rtb'

# subnets and instances
PUBLIC_SUBNET = 'pintusukses-public-subnet'
PRIVATE_SUBNET = 'pintusukses-private-subnet'

ROUTE_TABLES_ID_TO_ROUTES_MAP = {
    PUBLIC_ROUTE_TABLE: [
        {
            'destination_cidr_block': '0.0.0.0/0',
            'gateway_id': INTERNET_GATEWAY,
            'router_type': RouterType.GATEWAY
        }
    ],
    PRIVATE_ROUTE_TABLE: [
        {
            'destination_cidr_block': '0.0.0.0/0',  # Route all other traffic
            'router_type': RouterType.NAT_GATEWAY,
            'subnet_id': PUBLIC_SUBNET  # Specify the public subnet ID
        },
    ],
}

# security groups
SECURITY_GROUP_WEB = 'pintusukses-web-sg'
SECURITY_GROUP_API = 'pintusukses-api-sg'

SECURITY_GROUP_ID_TO_CONFIG = {
    SECURITY_GROUP_WEB: {
        'group_description': 'Security Group of the pintusukses web',
        'group_name': SECURITY_GROUP_WEB,
        'security_group_ingress': [
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=80, to_port=80
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=80, to_port=80
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=443, to_port=443
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=443, to_port=443
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=22, to_port=22
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=22, to_port=22
            ),
        ],
        'tags': [{'key': 'Name', 'value': SECURITY_GROUP_WEB}]
    },
    SECURITY_GROUP_API: {
        'group_description': 'Security of the pintusukses api',
        'group_name': SECURITY_GROUP_API,
        'security_group_ingress': [
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=80, to_port=80
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=80, to_port=80
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=443, to_port=443
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=443, to_port=443
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=22, to_port=22
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ipv6='::/0', from_port=22, to_port=22
            ),
            CfnSecurityGroup.IngressProperty(
                ip_protocol='TCP', cidr_ip='0.0.0.0/0', from_port=3306, to_port=3306
            ),
        ],
        'tags': [{'key': 'Name', 'value': SECURITY_GROUP_API}]
    },
}


PUBLIC_INSTANCE = 'pintusukses-public-instance'
PRIVATE_INSTANCE = 'pintusukses-private-instance'

# AMI ID of the ubuntu 22.04
AMI = 'ami-081205ca71b3f3635'

SUBNET_CONFIGURATION = {
    PUBLIC_SUBNET: {
        'availability_zone': 'ap-southeast-3a', 'cidr_block': '10.0.1.0/24', 'map_public_ip_on_launch': True,
        'route_table_id': PUBLIC_ROUTE_TABLE,
        'instances': {
            PUBLIC_INSTANCE: {
                'disable_api_termination': False,
                'key_name': KEY_PAIR_NAME,
                'image_id': AMI,
                'instance_type': 't3.micro',
                'security_group_ids': [SECURITY_GROUP_WEB],
                'tags': [
                    {'key': 'Name', 'value': PUBLIC_INSTANCE},
                ],
            },
        }
    },
    PRIVATE_SUBNET: {
        'availability_zone': 'ap-southeast-3b', 'cidr_block': '10.0.2.0/24', 'map_public_ip_on_launch': False,
        'route_table_id': PRIVATE_ROUTE_TABLE,
        'instances': {
            PRIVATE_INSTANCE: {
                'disable_api_termination': False,
                'key_name': KEY_PAIR_NAME,
                'image_id': AMI,
                'instance_type': 't3.micro',
                'security_group_ids': [SECURITY_GROUP_API],
                'tags': [
                    {'key': 'Name', 'value': PRIVATE_INSTANCE},
                ],
            },
        }
    }
}