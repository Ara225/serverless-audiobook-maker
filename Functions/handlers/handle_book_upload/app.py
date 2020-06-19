import json
import boto3
import botocore
from os import environ

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
    s3 = boto3.resource('s3')
    localFileName = event['Records'][0]['s3']['object']['key'].split("/")[-1]
    s3FileName = event['Records'][0]['s3']['object']['key']
    bucketName = event['Records'][0]['s3']['bucket']['name']
    try:
        s3.Bucket(bucketName).download_file(s3FileName, localFileName)
    except Exception as e:
        print(e)
        print("Error while downloading file " + s3FileName + "from the S3 bucket " + bucketName)
        raise
        return {
               "statusCode": 500,
               "body": json.dumps({
                   "message": "Error while downloading file " + s3FileName + "from the S3 bucket " + bucketName,
               }),
           }
    try:
        metadata = ""
        with open(localFileName, "r",encoding="utf-8") as book:
            for line in book:
                if "------ END METADATA --------" not in line:
                    metadata += line.replace("\r\n", "").replace("\n", "")
                else:
                    break
            #TODO Insert into DB
            print(json.loads(metadata))
            bookContent = book.read()
        bookContent = [bookContent[i:i+99990] for i in range(0, len(bookContent), 99990)]
        print(bookContent)
    except Exception as e:
        print("Error while reading downloaded file " + str(localFileName))
        print(e)
        raise
        return {
               "statusCode": 500,
               "body": json.dumps({
                   "message": "Error while reading downloaded file " + str(localFileName),
               }),
        }
    if len(bookContent) > 1:
        count = 0
        for chunk in bookContent:
            chunk += "Part " + str(count)
    for chunk in bookContent:
        try:
            print("here")
            chunk = chunk.replace('"', "&quot;").replace('&', "&amp;").replace("'", "&apos;").replace("<", "&lt;").replace(">", "&gt;")
            chunk = chunk.replace("\n\n", "</p>\n<p>")
            chunk = "<speak><amazon:auto-breaths><p>" + chunk + "</p></amazon:auto-breaths></speak>"
            chunk = chunk.replace("</p></p>", "</p>").replace("</p>\n</p>", "</p>").replace("<p><p>", "<p>").replace("<p>\n<p>", "<p>")
            pollyClient = boto3.client('polly')
            response = pollyClient.start_speech_synthesis_task(
                                                        Engine='standard',
                                                        LanguageCode='en-GB',
                                                        OutputFormat='mp3',
                                                        OutputS3BucketName=environ['AUDIO_S3_BUCKET'],
                                                        Text=chunk,
                                                        TextType='ssml',
                                                        VoiceId='Brian'
                                                    )
            print(response)
        except Exception as e:
            print("Error parsing chunk or requesting Polly to say it")
            print(e)
            raise
    response["CreationTime"] = response["CreationTime"].timestamp()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": response,
        }),
    }