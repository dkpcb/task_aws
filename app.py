from constructs import Construct
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_dynamodb as ddb,
    aws_s3 as s3,
    aws_s3_deployment as s3_deploy,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    aws_apigateway as apigw,
)
import os

class task(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = ddb.Table(
            self, "taskr-Table",
            partition_key=ddb.Attribute(
                name="item_id",
                type=ddb.AttributeType.STRING
            ),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        bucket = s3.Bucket(
            self, "task-Bucket",
            website_index_document="index.html",
            public_read_access=True,
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        common_params = {
            "runtime": _lambda.Runtime.PYTHON_3_8,
            "environment": {
                "TABLE_NAME": table.table_name
            }
        }

        get_task_lambda = _lambda.Function(
            self, "Gettask",
            code=_lambda.Code.from_asset("api"),
            handler="api.get_task",
            memory_size=512,
            timeout=cdk.Duration.seconds(10),
            **common_params,
        )
        post_task_lambda = _lambda.Function(
            self, "Posttask",
            code=_lambda.Code.from_asset("api"),
            handler="api.post_task",
            **common_params,
        )
        patch_task_lambda = _lambda.Function(
            self, "Patchtask",
            code=_lambda.Code.from_asset("api"),
            handler="api.patch_task",
            **common_params,
        )
        delete_task_lambda = _lambda.Function(
            self, "Deletetask",
            code=_lambda.Code.from_asset("api"),
            handler="api.delete_task",
            **common_params,
        )

        table.grant_read_data(get_task_lambda)
        table.grant_read_write_data(post_task_lambda)
        table.grant_read_write_data(patch_task_lambda)
        table.grant_read_write_data(delete_task_lambda)
        
        api = apigw.RestApi(
            self, "taskApi",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            )
        )

        task = api.root.add_resource("task")
        task.add_method(
            "GET",
            apigw.LambdaIntegration(get_task_lambda)
        )
        task.add_method(
            "POST",
            apigw.LambdaIntegration(post_task_lambda)
        )

        task_item_id = task.add_resource("{item_id}")
        task_item_id.add_method(
            "PATCH",
            apigw.LambdaIntegration(patch_task_lambda)
        )
        task_item_id.add_method(
            "DELETE",
            apigw.LambdaIntegration(delete_task_lambda)
        )

        ssm.StringParameter(
            self, "TABLE_NAME",
            parameter_name="TABLE_NAME",
            string_value=table.table_name
        )
        ssm.StringParameter(
            self, "ENDPOINT_URL",
            parameter_name="ENDPOINT_URL",
            string_value=api.url
        )

        # Output parameters
        cdk.CfnOutput(self, 'BucketUrl', value=bucket.bucket_website_domain_name)

app = cdk.App()
task(
    app, "Bashoutter",
    env={
        "region": os.environ["CDK_DEFAULT_REGION"],
        "account": os.environ["CDK_DEFAULT_ACCOUNT"],
    }
)

app.synth()