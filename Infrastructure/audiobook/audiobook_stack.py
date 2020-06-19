from aws_cdk import core
from aws_cdk import aws_dynamodb, aws_apigateway, aws_lambda, aws_s3, aws_lambda
from aws_cdk.aws_lambda_event_sources import S3EventSource

class AudiobookStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # create audiobooksQueueDB dynamo table
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
        # Make function
        book_upload_lambda_function = aws_lambda.Function(self, "HandleBookUploadLambda",
                                              handler='app.lambda_handler',
                                              runtime=aws_lambda.Runtime.PYTHON_3_8,
                                              code=aws_lambda.Code.from_asset(
                                                  '../Functions/handlers/handle_book_upload'),
                                              timeout=core.Duration.seconds(120))
        book_upload_lambda_function.add_environment("TABLE_NAME", audiobooksDB.table_name)
        audiobooksDB.grant_write_data(book_upload_lambda_function)
        BookUploadBucket = aws_s3.Bucket(self, "BookUploadBucket")
        book_upload_lambda_function.add_event_source(S3EventSource(BookUploadBucket,
                                                      events=[ aws_s3.EventType.OBJECT_CREATED ],
                                                      filters=[ { "suffix": '*txt' } ] 
                                                    ))
        BookUploadBucket.grant_read(book_upload_lambda_function)
