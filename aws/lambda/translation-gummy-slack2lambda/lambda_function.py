#coding: utf-8
import json
import urllib
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(slack_event, context):
    logging.info(json.dumps(slack_event))
    
    if "challenge" in slack_event:
        return slack_event.get("challenge")

    client = boto3.client('lambda')
    response = client.invoke(
        FunctionName='translation-gummy-lambda2ec2',
        InvocationType='Event',
        LogType='Tail',
        Payload=json.dumps(slack_event),
    )
    logging.info(response)
    
    return "OK"