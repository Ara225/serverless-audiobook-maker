import json
from os import environ
import boto3
from boto3.dynamodb.conditions import Attr
def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    if 'local' == environ.get('APP_STAGE'):
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
        table = dynamodb.Table("audiobooksDB")
    else:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(environ["TABLE_NAME"])
    message = json.loads(event["Records"][0]["Sns"]["Message"])
    if message['taskStatus'] != "COMPLETED":
        print(event)
        raise Exception("Task is not completed")
    response = table.scan(
       FilterExpression=Attr("audioURLs").contains(message["outputUri"].replace("s3://", ""))
    )
    # While there are more items to evaluate and we haven't found the right one yet
    while response['Items'] == [] and response.get("LastEvaluatedKey"):
        response = table.query(
           ExclusiveStartKey=response["LastEvaluatedKey"],
           FilterExpression=Attr("audioURLs").contains(message["outputUri"].replace("s3://", ""))
        )
    if response['Items'] == []:
        raise Exception("No matching items found in database")
    item = json.loads(response['Items'][0])
    client = boto3.client('ecs')
    ec2 = boto3.resource('ec2')
    vpc = ec2.Vpc(environ["VPC_ID"]) 
    response = client.run_task(
                cluster=environ["CLUSTER_ARN"],
                launchType='FARGATE',
                networkConfiguration={
                    'awsvpcConfiguration': {
                        'subnets': [i.id for i in vpc.subnets.all()],
                        'assignPublicIp': 'ENABLED'
                    }
                },
                overrides={
                    'containerOverrides': [
                        {
                            'name': environ["CONTAINER_NAME"],
                            'environment': [
                                {
                                    'name': 'VIDEO_S3_BUCKET',
                                    'value': environ['VIDEO_S3_BUCKET']
                                },
                                {
                                    'name': 'AUDIO_URL',
                                    'value': message["outputUri"]
                                },
                                {
                                    'name': 'IMAGE_URL',
                                    'value': item["imageURL"]
                                },
                                {
                                    'name': 'BOOK_NAME',
                                    'value': item["bookName"]
                                }
                            ],
                            'cpu': 1024,
                            'memory': 5120,
                        },
                    ]
                },
                taskDefinition=environ["TASK_DEFINITION_ARN"]
            )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "OK"
        }),
    }