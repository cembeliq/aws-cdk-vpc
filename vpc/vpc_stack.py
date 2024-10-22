from constructs import Construct
from aws_cdk import Stack
from aws_cdk.aws_ec2 import (
    Vpc,
    CfnRouteTable,
    RouterType,
    CfnRoute,
    CfnInternetGateway,
    CfnVPCGatewayAttachment,
    CfnSubnet,
    CfnSubnetRouteTableAssociation,
    CfnSecurityGroup,
    CfnInstance,
    CfnEIP,
    CfnNatGateway,
)

from .config import (  # Import your config
    VPC,
    INTERNET_GATEWAY,
    ROUTE_TABLES_ID_TO_ROUTES_MAP,
    SECURITY_GROUP_ID_TO_CONFIG,
    SUBNET_CONFIGURATION,
)


class VpcStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create VPC
        self.bifrost_vpc = Vpc(
            self,
            VPC,
            cidr="10.0.0.0/16",
            nat_gateways=0,
            subnet_configuration=[],
            enable_dns_support=True,
            enable_dns_hostnames=True,
        )

        self.internet_gateway = self.attach_internet_gateway()

        self.subnet_id_to_subnet_map = {}
        self.route_table_id_to_route_table_map = {}
        self.security_group_id_to_group_map = {}
        self.instance_id_to_instance_map = {}

        self.create_route_tables()
        self.create_security_groups()

        self.create_subnets()
        self.create_subnet_route_table_associations()

        self.create_routes()
        self.create_instances()

    def create_route_tables(self):
        """Create Route Tables"""
        for route_table_id in ROUTE_TABLES_ID_TO_ROUTES_MAP:
            self.route_table_id_to_route_table_map[route_table_id] = CfnRouteTable(
                self,
                route_table_id,
                vpc_id=self.bifrost_vpc.vpc_id,
                tags=[{"key": "Name", "value": route_table_id}],
            )

    def create_routes(self):
        """Create routes of the Route Tables"""
        for route_table_id, routes in ROUTE_TABLES_ID_TO_ROUTES_MAP.items():
            for i, route in enumerate(routes):  # Use enumerate for index

                kwargs = {
                    **route,
                    "route_table_id": self.route_table_id_to_route_table_map[
                        route_table_id
                    ].ref,
                }

                if route.get("router_type") == RouterType.GATEWAY:
                    kwargs["gateway_id"] = self.internet_gateway.ref
                elif route.get("router_type") == RouterType.NAT_GATEWAY:
                    kwargs["nat_gateway_id"] = self.create_nat_gateway(
                        route["subnet_id"]
                    ).ref
                    del kwargs["subnet_id"]  # Remove subnet_id after using it

                del kwargs["router_type"]  # Remove router_type before creating the route

                CfnRoute(self, f"{route_table_id}-route-{i}", **kwargs)

    def attach_internet_gateway(self) -> CfnInternetGateway:
        """Create and attach internet gateway to the VPC"""
        internet_gateway = CfnInternetGateway(self,INTERNET_GATEWAY)
        CfnVPCGatewayAttachment(
            self,
            "internet-gateway-attachment",
            vpc_id=self.bifrost_vpc.vpc_id,
            internet_gateway_id=internet_gateway.ref,
        )

        return internet_gateway

    def create_subnets(self):
        """Create subnets of the VPC"""
        for subnet_id, subnet_config in SUBNET_CONFIGURATION.items():
            subnet = CfnSubnet(
                self,
                subnet_id,
                vpc_id=self.bifrost_vpc.vpc_id,
                cidr_block=subnet_config["cidr_block"],
                availability_zone=subnet_config["availability_zone"],
                tags=[{"key": "Name", "value": subnet_id}],
                map_public_ip_on_launch=subnet_config["map_public_ip_on_launch"],
            )

            self.subnet_id_to_subnet_map[subnet_id] = subnet

    def create_subnet_route_table_associations(self):
        """Associate subnets with route tables"""
        for subnet_id, subnet_config in SUBNET_CONFIGURATION.items():
            route_table_id = subnet_config["route_table_id"]

            CfnSubnetRouteTableAssociation(
                self,
                f"{subnet_id}-{route_table_id}",
                subnet_id=self.subnet_id_to_subnet_map[subnet_id].ref,
                route_table_id=self.route_table_id_to_route_table_map[
                    route_table_id
                ].ref,
            )

    def create_security_groups(self):
        """Creates all the security groups"""
        for (
            security_group_id,
            sg_config,
        ) in SECURITY_GROUP_ID_TO_CONFIG.items():
            self.security_group_id_to_group_map[security_group_id] = CfnSecurityGroup(
                self, security_group_id, vpc_id=self.bifrost_vpc.vpc_id, **sg_config
            )

    def create_instances(self):
        """Creates all EC2 instances"""
        for subnet_id, subnet_config in SUBNET_CONFIGURATION.items():
            subnet = self.subnet_id_to_subnet_map[subnet_id]

            self.create_instances_for_subnet(subnet, subnet_config.get("instances", {}))

    def create_instances_for_subnet(
        self, subnet: CfnSubnet, instance_id_to_config_map: {str: dict}
    ):
        """Creates EC2 instances in a subnet"""
        for instance_id, instance_config in instance_id_to_config_map.items():
            instance = self.create_instance(subnet, instance_id, instance_config)
            self.instance_id_to_instance_map[instance_id] = instance

    def create_instance(
        self, subnet: CfnSubnet, instance_id: str, instance_config: dict
    ) -> CfnInstance:
        """Creates a single EC2 instance"""
        security_group_ids = instance_config["security_group_ids"]
        del instance_config["security_group_ids"]

        return CfnInstance(
            self,
            f"{instance_id}-instance",
            **{
                **instance_config,
                "subnet_id": subnet.ref,
                "security_group_ids": [
                    self.security_group_id_to_group_map[security_group_id].ref
                    for security_group_id in security_group_ids
                ],
            },
        )

    def create_nat_gateway(self, subnet_id: str) -> CfnNatGateway:
        """Creates a NAT Gateway in the specified subnet"""
        subnet = self.subnet_id_to_subnet_map[subnet_id]
        eip = CfnEIP(self, f"NATGatewayEIP-{subnet_id}")
        nat_gateway = CfnNatGateway(
            self,
            f"NATGateway-{subnet_id}",
            allocation_id=eip.attr_allocation_id,
            subnet_id=subnet.ref,
        )
        return nat_gateway