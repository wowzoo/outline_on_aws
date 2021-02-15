
# Outline Wiki on AWS
This project uses various AWS services.

 * VPC
 * Aurora PostgreSQL
 * Elasticache Redis
 * S3
 * EC2
 * Application Load Balancer
 * Route53

## Prerequisite

### Domain
Private Domain which is registered at Route53

### AWS Account
Create AWS Account, then Install AWS CLI and configure it.
To install and configure AWS CLI, Refer to 
https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html

### CDK
This is a CDK project for Python.

To install CDK, Refer to 
https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html

### direnv
This is a tool that can load and unload environment variables depending on the current directory.

To install direnv, Refer to 
https://direnv.net/docs/installation.html


## Deploy CDK
```shell
$ cd outline_on_aws
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
$ cdk deploy Outline
```

To deactivate virtual environment
```shell
$ deactivate
```
