from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_elasticache as cache,
)


class RedisStack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str,
                 vpc: ec2.Vpc, sg: ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        subnet_group = cache.CfnSubnetGroup(
            self,
            "OutlineSubnetGroup",
            cache_subnet_group_name="outline-subent-group",
            description="Subnet Group for Outline Redis",
            subnet_ids=vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE).subnet_ids,
        )

        redis_cluster = cache.CfnReplicationGroup(
            self,
            "OutlineRedis",
            replication_group_description="outline replication group",
            engine="redis",
            engine_version="6.x",
            cache_node_type="cache.r5.large",
            port=6379,
            num_node_groups=1,  # shard
            replicas_per_node_group=1,  # one replica
            cache_subnet_group_name=subnet_group.ref,
            security_group_ids=[sg.security_group_id],
            multi_az_enabled=True,
        )
        redis_cluster.add_depends_on(subnet_group)

        self._redis_url = f"{redis_cluster.attr_primary_end_point_address}:{redis_cluster.attr_primary_end_point_port}"

        core.CfnOutput(
            self,
            "Redis Primary Endpoint",
            value=self._redis_url
        )

    @property
    def redis_url(self):
        return self._redis_url

