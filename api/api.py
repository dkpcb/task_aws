import json, os, uuid, decimal
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["TABLE_NAME"])

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
}

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def create_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def get_task(event, context):
    try:
        response = table.scan()
        return create_response(200, response.get("Items", []))
    except ClientError as e:
        return create_response(500, {"description": f"Internal server error: {str(e)}"})

def post_task(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        for key in ["username", "task"]:
            if not body.get(key):
                return create_response(400, {"description": f"Bad request. {key} is empty"})

        task = {
            "task_id": uuid.uuid4().hex,
            "username": body["username"],
            "task": body["task"],
            "Finished": bool(body.get("Finished", False)),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")
        }
        table.put_item(Item=task)
        return create_response(201, {"description": "Successfully added a new task."})
    except ClientError as e:
        return create_response(500, {"description": f"Internal server error: {str(e)}"})

def change_finished_task(event, context):
    try:
        task_id = event.get("pathParameters", {}).get("task_id")
        if not task_id:
            return create_response(400, {"description": "Invalid request. The path parameter 'task_id' is missing"})
        
        body = json.loads(event.get("body", "{}"))
        finished_status = bool(body.get("Finished", False))
        
        response = table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET Finished = :fin",
            ExpressionAttributeValues={':fin': finished_status},
            ReturnValues="UPDATED_NEW"
        )
        
        return create_response(200, {"description": "Update successful", "updatedAttributes": response.get('Attributes')})
    except ClientError as e:
        return create_response(500, {"description": f"Internal server error: {str(e)}"})

def delete_task(event, context):
    try:
        task_id = event.get("pathParameters", {}).get("task_id")
        if not task_id:
            return create_response(400, {"description": "Invalid request. The path parameter 'task_id' is missing"})
        
        table.delete_item(Key={"task_id": task_id})
        return create_response(204, {"description": "Successfully deleted."})
    except ClientError as e:
        return create_response(500, {"description": f"Internal server error: {str(e)}"})