import boto3
import json

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_logs as logs,
    aws_secretsmanager as sm,
)


class DBStack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str,
                 vpc: ec2.Vpc, sg: ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(
            SecretId="outline-db"
        )

        db_credential = json.loads(response["SecretString"])
        username = db_credential['username']
        password = db_credential['password']

        db_cluster = rds.DatabaseCluster(
            self,
            "OutlineDB",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_11_9
            ),
            instance_props=rds.InstanceProps(
                vpc=vpc,
                enable_performance_insights=True,
                performance_insight_retention=rds.PerformanceInsightRetention.DEFAULT,
                # instance_type=ec2.InstanceType("db.r5.large"),
                instance_type=ec2.InstanceType.of(
                    instance_class=ec2.InstanceClass.MEMORY5,
                    instance_size=ec2.InstanceSize.LARGE,
                ),
                publicly_accessible=False,
                security_groups=[sg],
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE
                )
            ),
            cloudwatch_logs_retention=logs.RetentionDays.ONE_WEEK,
            cluster_identifier="outline-db",
            credentials=rds.Credentials.from_secret(
                secret=sm.Secret.from_secret_name_v2(
                    self,
                    "OutlineDBSecret",
                    secret_name="outline-db"
                ),
                username=username
            ),
            default_database_name="outline"
        )

        core.CfnOutput(
            self,
            "Aurora PostgreSQL Socket Address",
            value=f"{db_cluster.cluster_endpoint.socket_address}"
        )

        self._db_url = f"{username}:{password}@{db_cluster.cluster_endpoint.socket_address}"

    @property
    def db_url(self):
        return self._db_url


