from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as elbv2_targets
)


class ALBStack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str,
                 vpc: ec2.Vpc, sg: ec2.SecurityGroup, ins: ec2.Instance,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        outline_certificate_arn = ssm.StringParameter.from_string_parameter_attributes(
            self, "OutlineCertificateARNStringParameter", parameter_name="regional-outline-certificate-arn"
        ).string_value

        outline_certificate = elbv2.ListenerCertificate.from_arn(outline_certificate_arn)

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
            targets=[elbv2_targets.InstanceTarget(instance=ins)],
            health_check=elbv2.HealthCheck(
                enabled=True,
                path="/status"
            )
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
