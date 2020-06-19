import json
import boto3
import botocore
from os import environ

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

def readFile(localFileName):
    """Read from the file, input metadata to database, return file contents

    Args:
        localFileName (str): Name of the file to read from

    Returns:
        list: Content of the book in 99990 char chunks
    """
    try:
        metadata = ""
        with open(localFileName, "r", encoding="utf-8") as book:
            # Metadata is a object in JSON style 
            for line in book:
                if "------ END METADATA --------" not in line:
                    metadata += line.replace("\r\n", "").replace("\n", "")
                else:
                    break
            #TODO Insert into DB
            print(json.loads(metadata))
            # Starts reading from where we left off
            bookContent = book.read()
        # Polly accepts 100,000 chars at a time. We make chunks of 99990 because we put the part 1 maker in
        bookContent = [bookContent[i:i+99990] for i in range(0, len(bookContent), 99990)]
    except Exception as e:
        print("Error while reading downloaded file " + str(localFileName))
        raise
    return bookContent

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
    # Download file from the S3 bucket
    try:
        s3.Bucket(bucketName).download_file(s3FileName, localFileName)
    except Exception as e:
        print("Error while downloading file " + s3FileName + "from the S3 bucket " + bucketName)
        raise

    bookContent = readFile(localFileName)
    # Add part marker to book
    if len(bookContent) > 1:
        count = 0
        for chunk in bookContent:
            chunk += "Part " + str(count)
    for chunk in bookContent:
        try:
            chunk = convert_text_to_ssml(chunk)
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
        except Exception as e:
            print("Error parsing chunk or requesting Polly to say it")
            raise
    if response.get("CreationTime"):
        # CreationTime is a datetime, need to convert to string or will cause JSON parse error
        response["CreationTime"] = response["CreationTime"].timestamp()
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": response,
        }),
    }