
# Outline Wiki on AWS
This project is for deploying [outline wiki] on AWS.
It uses various AWS Services.

 * VPC
 * Aurora PostgreSQL
 * Elasticache Redis
 * S3
 * EC2
 * Application Load Balancer
 * Route53
 * Certificate Manager
 * Secrets Manager

## Prerequisite

### Domain
Private Domain which is registered at Route53

### AWS Account
Create AWS Account, then Install AWS CLI and configure it.
To install and configure AWS CLI, Refer to [AWS CLI Install]

### EC2 Key Pairs
Go to AWS EC2 console and create EC2 Key Pairs.

### Database Credentials
Go to AWS Secrets Manger console and create database credentials. 

Secret name should be **outline-db**

Store a new secret -> Other type of secrets -> Plaintext 

Create json like this. 
```json
{
  "username": "xxxxx",
  "password": "xxxxx"
}
```

### CDK
This is a CDK project for Python.
To install CDK, Refer to [CDK Getting Started]

### direnv
This is a tool that can load and unload environment variables depending on the current directory.
To install direnv, Refer to [Direnv Installation]

### Slack App
This project uses slack auth for authentication.
To create application at slack, Refer to [Create App]

When configuring the Client ID, add a redirect URL under "OAuth & Permissions"

ex) https://**URL**/auth/slack.callback

* URL : this is the URL registered at Route53
* Client ID : this is SLACK_KEY in .envrc
* Client Secret : this is SLACK_SECRET in .envrc

## Create .envrc
direnv looks up .envrc and apply it's variables on environment

.envrc must have these variables
```shell
# AWS Account number
export CDK_ACCOUNT=111111111111
# Region where to deploy service
export CDK_REGION=ap-northeast-2
# profile name which is set when configuring AWS CLI
export AWS_PROFILE=default
# Tag for AWS Services
export TAG=xxxxxxx
# Key pair name for EC2
export KEY_PAIR=xxxxxxx
# Private Domain name
export DOMAIN_NAME=xxxx.xxx
# Slack key and secret
export SLACK_KEY=1111111.111111
export SLACK_SECRET=xxxxxxxx
```

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

[outline wiki]: https://github.com/outline/outline
[AWS CLI Install]: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html
[CDK Getting Started]: https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html
[Direnv Installation]: https://direnv.net/docs/installation.html
[Create App]: https://api.slack.com/apps
