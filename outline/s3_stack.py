from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_iam as iam,
)


class S3Stack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str,
                 vpc: ec2.Vpc, domain_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = f"outline-{'-'.join(domain_name.split('.'))}"

        # S3 CORS rule
        s3_cors_update_rule = s3.CorsRule(
            allowed_headers=["*"],
            allowed_methods=[s3.HttpMethods.PUT, s3.HttpMethods.POST],
            allowed_origins=[f"https://outline.{domain_name}"],
            exposed_headers=[]
        )

        s3_cors_list_rule = s3.CorsRule(
            allowed_headers=[],
            allowed_methods=[s3.HttpMethods.GET],
            allowed_origins=["*"],
            exposed_headers=[]
        )

        self._storage_bucket = s3.Bucket(
            self,
            "StorageBucket",
            bucket_name=bucket_name,
            cors=[s3_cors_update_rule, s3_cors_list_rule],
        )

        self._storage_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.AccountRootPrincipal()],
                actions=[
                    "s3:GetObjectAcl",
                    "s3:DeleteObject",
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:PutObjectAcl"
                ],
                resources=[
                    f"arn:aws:s3:::{bucket_name}",
                    f"arn:aws:s3:::{bucket_name}/*"
                ],
                conditions={
                    "StringEquals": {
                        "aws:sourceVpc": [
                            vpc.vpc_id
                        ]
                    }
                }
            )
        )

        core.CfnOutput(
            self,
            "Bucket URL",
            value=self._storage_bucket.bucket_regional_domain_name
        )

    @property
    def s3_bucket(self):
        return self._storage_bucket
