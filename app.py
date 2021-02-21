#!/usr/bin/env python3

import os

from aws_cdk import core
from outline.vpc_stack import VPCStack
from outline.s3_stack import S3Stack
from outline.db_stack import DBStack
from outline.redis_stack import RedisStack
from outline.asg_stack import ASGStack
from outline.route53_stack import Route53Stack

account = os.environ["CDK_ACCOUNT"]
region = os.environ["CDK_REGION"]
domain_name = os.environ["DOMAIN_NAME"]
tag = os.environ["TAG"]
key_pair = os.environ["KEY_PAIR"]

app = core.App()

outline_stack = core.Stack(
    app,
    "Outline",
    env=core.Environment(account=account, region=region),
    tags={"Owner": tag}
)

vpc_stack = VPCStack(
    outline_stack,
    "VPC"
)

s3_stack = S3Stack(
    outline_stack,
    "S3",
    vpc=vpc_stack.vpc,
    domain_name=domain_name,
)
s3_stack.add_dependency(vpc_stack)

redis_stack = RedisStack(
    outline_stack,
    "Redis",
    vpc=vpc_stack.vpc,
    sg=vpc_stack.sg
)
redis_stack.add_dependency(vpc_stack)

db_stack = DBStack(
    outline_stack,
    "DB",
    vpc=vpc_stack.vpc,
    sg=vpc_stack.sg
)
db_stack.add_dependency(vpc_stack)

asg_stack = ASGStack(
    outline_stack,
    "ASG",
    vpc=vpc_stack.vpc,
    sg=vpc_stack.sg,
    bucket=s3_stack.s3_bucket,
    db_url=db_stack.db_url,
    redis_url=redis_stack.redis_url,
    domain_name=domain_name,
    key_pair=key_pair
)
asg_stack.add_dependency(s3_stack)
asg_stack.add_dependency(db_stack)
asg_stack.add_dependency(redis_stack)

route53_stack = Route53Stack(
    outline_stack,
    "Route53",
    domain_name=domain_name,
    alb=asg_stack.alb
)
route53_stack.add_dependency(asg_stack)

app.synth()
