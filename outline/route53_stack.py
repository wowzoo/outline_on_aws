from aws_cdk import (
    core,
    aws_route53 as route53,
    aws_route53_targets as alias,
    aws_elasticloadbalancingv2 as elbv2,
)


class Route53Stack(core.NestedStack):

    def __init__(self, scope: core.Construct, construct_id: str,
                 domain_name: str, alb: elbv2.ApplicationLoadBalancer,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hosted_zone = route53.HostedZone.from_lookup(
            self,
            "TomatoBridgeDomain",
            domain_name=domain_name
        )

        route53.ARecord(
            self,
            "AliasRecord",
            zone=hosted_zone,
            record_name=f"outline.{domain_name}",
            target=route53.RecordTarget.from_alias(alias.LoadBalancerTarget(alb))
        )
