#!/usr/bin/env python3

import os

from aws_cdk import core
from outline.vpc_stack import VPCStack
from outline.s3_stack import S3Stack
from outline.db_stack import DBStack
from outline.redis_stack import RedisStack
from outline.ec2_stack import EC2Stack
from outline.alb_stack import ALBStack
from outline.route53_stack import Route53Stack

account = os.environ["CDK_ACCOUNT"]
region = os.environ["CDK_REGION"]
domain_name = os.environ["DOMAIN_NAME"]
slack_key = os.environ["SLACK_KEY"]
slack_secret = os.environ["SLACK_SECRET"]
tag = os.environ["TAG"]
key_pair = os.environ["KEY_PAIR"]
profile_name = os.environ["AWS_PROFILE"]

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

ec2_stack = EC2Stack(
    outline_stack,
    "EC2",
    vpc=vpc_stack.vpc,
    sg=vpc_stack.sg,
    bucket=s3_stack.s3_bucket,
    region=region,
    profile_name=profile_name,
    domain_name=domain_name,
    db_url=db_stack.db_url,
    redis_url=redis_stack.redis_url,
    key_pair=key_pair,
    slack_key=slack_key,
    slack_secret=slack_secret,
)
ec2_stack.add_dependency(s3_stack)
ec2_stack.add_dependency(db_stack)
ec2_stack.add_dependency(redis_stack)

alb_stack = ALBStack(
    outline_stack,
    "ALB",
    vpc=vpc_stack.vpc,
    sg=vpc_stack.sg,
    ins=ec2_stack.instance
)
alb_stack.add_dependency(ec2_stack)

route53_stack = Route53Stack(
    outline_stack,
    "Route53",
    domain_name=domain_name,
    alb=alb_stack.alb
)
route53_stack.add_dependency(alb_stack)

app.synth()
