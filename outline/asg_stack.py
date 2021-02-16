import secrets
import boto3

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_autoscaling as autoscaling,
    aws_route53 as route53,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
)


class ASGStack(core.NestedStack):

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
        user_data.add_commands(
            "sudo curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo")
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
            user_data.add_commands(
                f"sudo sed -i 's=$outline_domain=outline.{domain_name}=' /etc/nginx/conf.d/outline.conf")

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
            user_data.add_commands(
                f"sudo sed -i 's=$s3_bucket_url=s3.{region}.amazonaws.com=' /home/ec2-user/env.outline")
            credentials = boto3.Session(profile_name=profile_name).get_credentials()
            user_data.add_commands(
                f"sudo sed -i 's=$aws_access_key={credentials.access_key}=' /home/ec2-user/env.outline")
            user_data.add_commands(
                f"sudo sed -i 's=$aws_secret_key={credentials.secret_key}=' /home/ec2-user/env.outline")

        # docker
        user_data.add_commands("sudo systemctl start docker")
        user_data.add_commands("sudo docker pull outlinewiki/outline")
        user_data.add_commands(
            "sudo docker run --rm --env-file=/home/ec2-user/env.outline outlinewiki/outline yarn sequelize:migrate")
        user_data.add_commands(
            "sudo docker run -p 3000:3000 --env-file=/home/ec2-user/env.outline -d outlinewiki/outline")
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

        block_device = autoscaling.BlockDevice(
            device_name="/dev/xvda",
            volume=autoscaling.BlockDeviceVolume.ebs(
                volume_size=16,
                volume_type=ec2.EbsDeviceVolumeType.GP2,
                delete_on_termination=True,
            )
        )

        outline_asg = autoscaling.AutoScalingGroup(
            self,
            "OutlineASG",
            auto_scaling_group_name="outline-asg",
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.BURSTABLE3,
                instance_size=ec2.InstanceSize.XLARGE
            ),
            machine_image=amzn_linux,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=sg,
            block_devices=[block_device],
            key_name=key_pair,
            user_data=user_data,
            min_capacity=1,
            max_capacity=10,
        )

        # Integrate ALB
        self._alb = elbv2.ApplicationLoadBalancer(
            self,
            "OutlineALB",
            load_balancer_name="OutlineALB",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=sg,
            internet_facing=True,
        )

        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "TomatoBridgeDomain",
            domain_name=domain_name
        )

        outline_certificate = acm.Certificate(
            self,
            "RegionalOutlineCertificate",
            domain_name=f"outline.{domain_name}",
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        https_listener = self._alb.add_listener(
            "OutlineALBHTTPSListener",
            protocol=elbv2.ApplicationProtocol.HTTPS,
            port=443,
            open=False,
            certificates=[outline_certificate],
        )

        https_listener.add_targets(
            "OutlineInstance",
            target_group_name="OutlineALBTargetGroup",
            protocol=elbv2.ApplicationProtocol.HTTP,
            port=80,
            targets=[outline_asg],
            health_check=elbv2.HealthCheck(
                enabled=True,
                path="/status"
            )
        )

        # The AutoScalingGroup must have been attached to
        # an Application Load Balancer in order to be able to call this.
        outline_asg.scale_on_request_count(
            "OutlineRequestCount",
            target_requests_per_minute=100,
        )

        http_listener = self._alb.add_listener(
            "OutlineALBHTTPListener",
            protocol=elbv2.ApplicationProtocol.HTTP,
            port=80,
            open=False,
        )

        http_listener.add_action(
            "OutlineALBHTTPAction",
            action=elbv2.ListenerAction.redirect(
                port="443",
                protocol="HTTPS",
                permanent=True,
            )
        )

    @property
    def alb(self):
        return self._alb
