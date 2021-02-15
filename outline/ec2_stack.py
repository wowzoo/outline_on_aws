import secrets
import boto3

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_s3 as s3,
)


class EC2Stack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str,
                 vpc: ec2.Vpc, sg: ec2.SecurityGroup, bucket: s3.Bucket,
                 profile_name: str, db_url: str, redis_url: str,
                 region: str, domain_name: str, key_pair: str,
                 slack_key: str, slack_secret: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_data = ec2.UserData.for_linux()
        user_data.add_commands("sudo curl -sL https://rpm.nodesource.com/setup_14.x | sudo bash -")
        user_data.add_commands("sudo yum install -y nodejs")
        user_data.add_commands("sudo curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo")
        user_data.add_commands("sudo yum install -y yarn")
        user_data.add_commands("sudo amazon-linux-extras install -y docker")
        user_data.add_commands("sudo amazon-linux-extras install -y nginx1")

        # nginx
        user_data.add_commands("sudo rm /etc/nginx/nginx.conf")

        with open("resources/nginx/nginx.conf") as f:
            nginx_conf_data = f.read()
            user_data.add_commands(f"sudo echo '{nginx_conf_data}' > /etc/nginx/nginx.conf")

        with open("resources/nginx/outline.conf") as f:
            outline_conf_data = f.read()
            user_data.add_commands(f"sudo echo '{outline_conf_data}' > /etc/nginx/conf.d/outline.conf")
            user_data.add_commands(f"sudo sed -i 's=$outline_domain=outline.{domain_name}=' /etc/nginx/conf.d/outline.conf")

        user_data.add_commands("sudo systemctl start nginx")

        # outline config
        with open("resources/env.outline") as f:
            outline_env_data = f.read()
            user_data.add_commands(f"sudo echo '{outline_env_data}' > /home/ec2-user/env.outline")
            user_data.add_commands(f"sudo sed -i 's=$secret_key={secrets.token_hex(32)}=' /home/ec2-user/env.outline")
            user_data.add_commands(f"sudo sed -i 's=$utils_secret={secrets.token_hex(32)}=' /home/ec2-user/env.outline")
            # db/redis
            user_data.add_commands(f"sudo sed -i 's=$db_url={db_url}=' /home/ec2-user/env.outline")
            user_data.add_commands(f"sudo sed -i 's=$redis_url={redis_url}=' /home/ec2-user/env.outline")
            # domain url
            user_data.add_commands(f"sudo sed -i 's=$outline_domain=outline.{domain_name}=' /home/ec2-user/env.outline")
            # slack
            user_data.add_commands(f"sudo sed -i 's=$slack_key={slack_key}=' /home/ec2-user/env.outline")
            user_data.add_commands(f"sudo sed -i 's=$slack_secret={slack_secret}=' /home/ec2-user/env.outline")
            # s3 bucket
            user_data.add_commands(f"sudo sed -i 's=$aws_region={region}=' /home/ec2-user/env.outline")
            user_data.add_commands(f"sudo sed -i 's=$s3_bucket_name={bucket.bucket_name}=' /home/ec2-user/env.outline")
            user_data.add_commands(f"sudo sed -i 's=$s3_bucket_url=s3.{region}.amazonaws.com=' /home/ec2-user/env.outline")
            credentials = boto3.Session(profile_name=profile_name).get_credentials()
            user_data.add_commands(f"sudo sed -i 's=$aws_access_key={credentials.access_key}=' /home/ec2-user/env.outline")
            user_data.add_commands(f"sudo sed -i 's=$aws_secret_key={credentials.secret_key}=' /home/ec2-user/env.outline")

        # docker
        user_data.add_commands("sudo systemctl start docker")
        user_data.add_commands("sudo docker pull outlinewiki/outline")
        user_data.add_commands("sudo docker run --rm --env-file=/home/ec2-user/env.outline outlinewiki/outline yarn sequelize:migrate")
        user_data.add_commands("sudo docker run -p 3000:3000 --env-file=/home/ec2-user/env.outline -d outlinewiki/outline")
        user_data.add_commands("sudo usermod -aG docker ec2-user")

        # ssh locale error fix
        user_data.add_commands("echo LANG=en_US.utf-8 | sudo tee /etc/environment")
        user_data.add_commands("echo LC_ALL=en_US.utf-8 | sudo tee -a /etc/environment")

        # instance
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            cpu_type=ec2.AmazonLinuxCpuType.X86_64,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
            virtualization=ec2.AmazonLinuxVirt.HVM,
        )

        block_device = ec2.BlockDevice(
            device_name="/dev/xvda",
            volume=ec2.BlockDeviceVolume.ebs(
                volume_size=16,
                volume_type=ec2.EbsDeviceVolumeType.GP2,
                delete_on_termination=True,
            )
        )

        self._instance = ec2.Instance(
            self,
            "OutlineInstance",
            instance_name="outline-server",
            # instance_type=ec2.InstanceType("t3.xlarge"),
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.BURSTABLE3,
                instance_size=ec2.InstanceSize.XLARGE
            ),
            machine_image=amzn_linux,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            block_devices=[block_device],
            security_group=sg,
            key_name=key_pair,
            user_data=user_data
        )
        self._instance.instance.ebs_optimized = True

    @property
    def instance(self):
        return self._instance
