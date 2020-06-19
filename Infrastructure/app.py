#!/usr/bin/env python3

from aws_cdk import core

from audiobook.audiobook_stack import AudiobookStack


app = core.App()
AudiobookStack(app, "audiobook", env={'region': 'eu-west-2'})

app.synth()
