#!/usr/bin/env python3

from aws_cdk import core

from outline.outline_stack import OutlineStack


app = core.App()
OutlineStack(app, "outline")

app.synth()
