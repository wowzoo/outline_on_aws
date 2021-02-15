from aws_cdk import (
    core,
    aws_ec2 as ec2,
)


class VPCStack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cidr = "172.30.0.0/16"

        self._vpc = ec2.Vpc(
            self,
            "OutlineVPC",
            max_azs=2,
            cidr=cidr,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE,
                    name="Private",
                    cidr_mask=24
                )
            ],
            nat_gateways=2,
            gateway_endpoints={
                "S3": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.S3
                )
            }
        )

        self._sg = ec2.SecurityGroup(
            self,
            "OutlineSecurityGroup",
            vpc=self._vpc,
            description="Security Group for Outline",
            security_group_name="OutlineSecurityGroup"
        )

        self._sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="SSH"
        )

        self._sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP"
        )

        self._sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS"
        )

        self._sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL"
        )

        self._sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(6379),
            description="Redis"
        )

        core.CfnOutput(
            self,
            "VPC ID",
            value=self._vpc.vpc_id
        )

        core.CfnOutput(
            self,
            "Security Group ID",
            value=self._sg.security_group_id
        )

    @property
    def vpc(self):
        return self._vpc

    @property
    def sg(self):
        return self._sg
