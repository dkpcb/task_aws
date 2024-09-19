from constructs import Construct
from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_ssm as ssm,
    aws_apigateway as apigateway,
    RemovalPolicy,
    Duration
)
import os

class TaskStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Table
        table = dynamodb.Table(
            self, "taskr-Table",
            partition_key=dynamodb.Attribute(
                name="item_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda Environment Parameters
        common_params = {
            "runtime": lambda_.Runtime.PYTHON_3_8,
            "environment": {
                "TABLE_NAME": table.table_name
            }
        }

        # Lambda Functions for Task Operations
        get_task_lambda = lambda_.Function(
            self, "Gettask",
            code=lambda_.Code.from_asset("api"),
            handler="api.get_task",
            memory_size=512,
            timeout=Duration.seconds(10),
            **common_params,
        )
        post_task_lambda = lambda_.Function(
            self, "Posttask",
            code=lambda_.Code.from_asset("api"),
            handler="api.post_task",
            **common_params,
        )
        put_task_lambda = lambda_.Function(
            self, "Puttask",
            code=lambda_.Code.from_asset("api"),
            handler="api.change_finished_task",
            **common_params,
        )
        delete_task_lambda = lambda_.Function(
            self, "Deletetask",
            code=lambda_.Code.from_asset("api"),
            handler="api.delete_task",
            **common_params,
        )

        # Grant Table Permissions to Lambda Functions
        table.grant_read_data(get_task_lambda)
        table.grant_read_write_data(post_task_lambda)
        table.grant_read_write_data(put_task_lambda)
        table.grant_read_write_data(delete_task_lambda)
        
        # API Gateway Setup
        api = apigateway.RestApi(
            self, "taskApi",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            )
        )

        # Define API Resources and Methods
        task = api.root.add_resource("task")
        task.add_method(
            "GET",
            apigateway.LambdaIntegration(get_task_lambda)
        )
        task.add_method(
            "POST",
            apigateway.LambdaIntegration(post_task_lambda)
        )

        task_item_id = task.add_resource("{item_id}")
        task_item_id.add_method(
            "PUT",
            apigateway.LambdaIntegration(put_task_lambda)
        )
        task_item_id.add_method(
            "DELETE",
            apigateway.LambdaIntegration(delete_task_lambda)
        )

        # Store Parameters in SSM Parameter Store
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

from aws_cdk import App

app = App()
TaskStack(
    app, "TaskStack",
    env={
        "region": os.environ["CDK_DEFAULT_REGION"],
        "account": os.environ["CDK_DEFAULT_ACCOUNT"],
    }
)

app.synth()