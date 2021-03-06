import json
import boto3
import botocore
from os import environ
from datetime import datetime
import string
import random
from decimal import Decimal
def convert_text_to_ssml(chunk):
    """Convert text to SSMl for Polly

    Args:
        chunk (str): chunk of text to parse

    Returns:
        str: Input test converted to SSML
    """
    # Escape chars that are forbidden in SSML
    chunk = chunk.replace('"', "&quot;").replace('&', "&amp;").replace("'", "&apos;").replace("<", "&lt;").replace(">", "&gt;")
    # <p></p> makes a longer pause happen between paragraphs
    chunk = chunk.replace("\r\n\r\n", "</p>\n<p>").replace("\n\n", "</p>\n<p>")
    chunk = "<speak><amazon:auto-breaths><p>" + chunk + "</p></amazon:auto-breaths></speak>"
    # Ensure no duplicate tags
    chunk = chunk.replace("</p></p>", "</p>").replace("</p>\n</p>", "</p>").replace("<p><p>", "<p>").replace("<p>\n<p>", "<p>")
    return chunk

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
    print("Function triggered")
    if 'local' == environ.get('APP_STAGE'):
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
        table = dynamodb.Table("audiobooksDB")
    else:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(environ["TABLE_NAME"])
    s3 = boto3.client('s3')
    
    s3FileName = event['Records'][0]['s3']['object']['key'].replace("+", " ")
    bucketName = event['Records'][0]['s3']['bucket']['name']
    # Download file from the S3 bucket
    try:
        book = s3.get_object(Bucket=bucketName, Key=s3FileName)
        print("Loading file from S3 bucket")
        bookContent = book["Body"].read().decode("utf-8", errors="ignore").split("------ END METADATA --------")
        metadata = json.loads(bookContent[0])
        bookContent = bookContent[1]
        # Polly accepts 100,000 chars at a time. We make chunks of 99990 because we put the part 1 maker in
        bookContent = [bookContent[i:i+99990] for i in range(0, len(bookContent), 99990)]
    except Exception as e:
        print("Error while downloading file " + s3FileName + "from the S3 bucket " + bucketName)
        raise
    # Add part marker to book
    if len(bookContent) > 1:
        count = 0
        for chunk in bookContent:
            chunk += "Part " + str(count)
    hasShortPart = False
    audioURLs = []
    pollyClient = boto3.client('polly')
    for chunk in bookContent:
        try:
            chunk = convert_text_to_ssml(chunk)
            print("Asking Polly to record the current chunk")
            response = pollyClient.start_speech_synthesis_task(
                                                        Engine='standard',
                                                        LanguageCode='en-GB',
                                                        OutputFormat='mp3',
                                                        OutputS3BucketName=environ['AUDIO_S3_BUCKET'],
                                                        Text=chunk,
                                                        TextType='ssml',
                                                        VoiceId='Brian',
                                                        SnsTopicArn=environ["SNS_TOPIC"],
                                                    )

            audioURLs.append(response["SynthesisTask"]["OutputUri"].split("amazonaws.com/")[-1])
            if len(chunk) <= 2000:
                hasShortPart = True
            print(response)
            print("Polly was successfully asked to to record the current chunk")
        except Exception as e:
            print("Error parsing chunk or requesting Polly to say it")
            raise
        try:
            randomString = ''.join([random.choice(string.ascii_letters 
            + string.digits) for n in range(32)]) 
            audiobook = {
                       "id": randomString,
                       "bookName": metadata["bookName"],
                       "imageURL":  metadata["imageURL"],
                       "authorName":metadata["authorName"],
                       "genres": metadata["genres"],
                       "audioURLs":  audioURLs,
                       "description": metadata["description"],
                       "hidden": False,
                       "hasShortPart": hasShortPart,
                       "addedAt": Decimal(datetime.now().timestamp())
                   }
            response = table.put_item(
                Item=audiobook
            )
        except Exception as e:
            print("Exception inserting into database")
            print(audiobook)
            print(response)
            raise
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": audioURLs
        }),
    }
