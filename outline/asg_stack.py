from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_autoscaling as autoscaling,
    aws_route53 as route53,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
)

from utils.userdata_maker import UserdataMaker


class ASGStack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str,
                 vpc: ec2.Vpc, sg: ec2.SecurityGroup, bucket: s3.Bucket,
                 db_url: str, redis_url: str,
                 domain_name: str, key_pair: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_data = UserdataMaker(db_url=db_url, redis_url=redis_url, bucket_name=bucket.bucket_name)

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
            user_data=user_data.data,
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

        outline_asg.scale_on_cpu_utilization(
            "OutlineCPUUtilization",
            target_utilization_percent=60
        )

        # The AutoScalingGroup must have been attached to
        # an Application Load Balancer in order to be able to call scale_on_request_count.
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
