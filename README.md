
# Outline Wiki on AWS

## prerequisite

### CDK
This is a CDK project for Python.

To install CDK, Refer to link below
https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html

### direnv
This is a tool that can load and unload environment variables depending on the current directory.

To install direnv, Refer to link below
https://direnv.net/docs/installation.html


## Deploy CDK
```shell
$ cd outline_on_aws
```

To manually create a virtualenv on MacOS and Linux:
```shell
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.
```shell
$ source .venv/bin/activate
```
To deactivate
```shell
$ deactivate
```

Once the virtualenv is activated, you can install the required dependencies.
```shell
$ pip install -r requirements.txt
```




At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
