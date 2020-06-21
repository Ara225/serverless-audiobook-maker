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
                     aws_iam,
                     aws_ec2
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

        # ******* Lambda functions
        book_upload_lambda_function = aws_lambda.Function(self, "HandleBookUploadLambda",
                                                          handler='app.lambda_handler',
                                                          runtime=aws_lambda.Runtime.PYTHON_3_8,
                                                          code=aws_lambda.Code.from_asset(
                                                              '../Functions/handlers/handle_book_upload'))
        polly_audio_lambda_function = aws_lambda.Function(self, "HandlePollyAudioLambda",
                                                          handler='app.lambda_handler',
                                                          runtime=aws_lambda.Runtime.PYTHON_3_8,
                                                          code=aws_lambda.Code.from_asset(
                                                              '../Functions/handlers/handle_polly_audio'), 
                                                          timeout=core.Duration.seconds(120))

        # ******* S3 upload buckets
        BookUploadBucket = aws_s3.Bucket(self, "BookUploadBucket")
        AudioUploadBucket = aws_s3.Bucket(self, "AudioUploadBucket")
        VideoUploadBucket = aws_s3.Bucket(self, "VideoUploadBucket")
        ImageUploadBucket = aws_s3.Bucket(self, "ImageUploadBucket")

        # ******* Create S3 event source
        book_upload_lambda_function.add_event_source(S3EventSource(BookUploadBucket,
                                                                   events=[
                                                                       aws_s3.EventType.OBJECT_CREATED],
                                                                   filters=[
                                                                       {"suffix": '.txt'}]
                                                                   ))
        # ******* Create SNS topic
        PollySNSTopic = aws_sns.Topic(self, "PollySNSTopic")
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
        
        # ******* Fargate container permissions
        role = aws_iam.Role(self, "FargateContainerRole", assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        role.add_to_policy(aws_iam.PolicyStatement(actions=["s3:PutObject"], resources=[VideoUploadBucket.bucket_arn+"/*"]))
        role.add_to_policy(aws_iam.PolicyStatement(actions=["s3:GetObject"], resources=[AudioUploadBucket.bucket_arn+"/*"]))
        role.add_to_policy(aws_iam.PolicyStatement(actions=["s3:GetObject"], resources=[ImageUploadBucket.bucket_arn+"/*"]))
        
        # ******* Fargate container
        vpc = aws_ec2.Vpc(self, "CdkFargateVpc", max_azs=2)
        cluster = aws_ecs.Cluster(self, 'FargateCluster', vpc=vpc)
        image = aws_ecs.ContainerImage.from_asset("../Functions/ECSContainerFiles")
        task_definition = aws_ecs.FargateTaskDefinition(
            self, "FargateContainerTaskDefinition", execution_role=role, task_role=role, cpu=1024, memory_limit_mib=3072
        )
        
        port_mapping = aws_ecs.PortMapping(container_port=80, host_port=80)
        container = task_definition.add_container(
            "Container", image=image,
            logging=aws_ecs.AwsLogDriver(stream_prefix="videoProcessingContainer")
        )
        container.add_port_mappings(port_mapping)
        
        # ******* Audio function environment variables
        polly_audio_lambda_function.add_environment("VIDEO_S3_BUCKET", VideoUploadBucket.bucket_name)
        polly_audio_lambda_function.add_environment("TASK_DEFINITION_ARN", task_definition.task_definition_arn)
        polly_audio_lambda_function.add_environment("CLUSTER_ARN", cluster.cluster_arn)
        polly_audio_lambda_function.add_environment("TABLE_NAME", audiobooksDB.table_name)
        polly_audio_lambda_function.add_environment("CONTAINER_NAME", container.container_name)
        polly_audio_lambda_function.add_environment("VPC_ID", str(vpc.vpc_id))

        # ******* Audio function permissions
        audiobooksDB.grant_read_write_data(polly_audio_lambda_function)
        polly_audio_lambda_function.add_to_role_policy(aws_iam.PolicyStatement(actions=["ecs:RunTask"], resources=["*"]))
        polly_audio_lambda_function.add_to_role_policy(aws_iam.PolicyStatement(actions=["iam:PassRole"], resources=["*"]))
        polly_audio_lambda_function.add_to_role_policy(aws_iam.PolicyStatement(actions=["ec2:DescribeSubnets"], resources=["*"]))