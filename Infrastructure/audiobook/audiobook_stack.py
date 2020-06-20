from aws_cdk import core
from aws_cdk import (aws_dynamodb, 
                     aws_apigateway, 
                     aws_lambda, 
                     aws_s3, 
                     aws_lambda, 
                     aws_sns, 
                     aws_sns_subscriptions, 
                     aws_ecs, 
                     aws_ecs_patterns,
                     aws_iam
                    )
from aws_cdk.aws_lambda_event_sources import S3EventSource


class AudiobookStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # ******* Database table
        audiobooksDB = aws_dynamodb.Table(
            self, "audiobooksDB",
            partition_key=aws_dynamodb.Attribute(
                name="id",
                type=aws_dynamodb.AttributeType.STRING
            ),
            read_capacity=2,
            write_capacity=2,
            billing_mode=aws_dynamodb.BillingMode.PROVISIONED
        )

        # ******* Lambda function
        book_upload_lambda_function = aws_lambda.Function(self, "HandleBookUploadLambda",
                                                          handler='app.lambda_handler',
                                                          runtime=aws_lambda.Runtime.PYTHON_3_8,
                                                          code=aws_lambda.Code.from_asset(
                                                              '../Functions/handlers/handle_book_upload'))
        polly_audio_lambda_function = aws_lambda.Function(self, "HandlePollyAudioLambda",
                                                          handler='app.lambda_handler',
                                                          runtime=aws_lambda.Runtime.PYTHON_3_8,
                                                          code=aws_lambda.Code.from_asset(
                                                              '../Functions/handlers/handle_polly_audio'))

        # ******* S3 upload buckets
        BookUploadBucket = aws_s3.Bucket(self, "BookUploadBucket")
        AudioUploadBucket = aws_s3.Bucket(self, "AudioUploadBucket")
        VideoUploadBucket = aws_s3.Bucket(self, "VideoUploadBucket")

        # ******* Create S3 event source
        book_upload_lambda_function.add_event_source(S3EventSource(BookUploadBucket,
                                                                   events=[
                                                                       aws_s3.EventType.OBJECT_CREATED],
                                                                   filters=[
                                                                       {"suffix": '*txt'}]
                                                                   ))

        # ******* Create SNS topic
        PollySNSTopic = aws_sns.Topic(
            self, "PollySNSTopic", display_name="Topic that AWS Polly posts SNS notifications in when it's finished making audio")
        PollySNSTopic.add_subscription(
            aws_sns_subscriptions.LambdaSubscription(polly_audio_lambda_function))

        # ******* Book function environment variables
        book_upload_lambda_function.add_environment(
            "TABLE_NAME", audiobooksDB.table_name)
        book_upload_lambda_function.add_environment(
            "AUDIO_S3_BUCKET", AudioUploadBucket.bucket_name)
        book_upload_lambda_function.add_environment(
            "SNS_TOPIC", PollySNSTopic.topic_arn)

        # ******* Book function permissions
        audiobooksDB.grant_write_data(book_upload_lambda_function)
        BookUploadBucket.grant_read(book_upload_lambda_function)
        AudioUploadBucket.grant_write(book_upload_lambda_function)
        PollySNSTopic.grant_publish(book_upload_lambda_function)
        book_upload_lambda_function.add_to_role_policy(aws_iam.PolicyStatement(actions=["polly:*"], resources=["*"]))
