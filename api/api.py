import json, os, uuid, decimal
from datetime import datetime, timezone
import boto3

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["TABLE_NAME"])

HEADERS = {
    "Access-Control-Allow-Origin": "*",
}

# this custom class is to handle decimal.Decimal objects in json.dumps()
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def get_task(event, context):
    
    try:
        response = table.scan()

        status_code = 200
        resp = response.get("Items")
    except Exception as e:
        status_code = 500
        resp = {"description": f"Internal server error. {str(e)}"}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp, cls=DecimalEncoder)
    }

def post_task(event, context):
    
    try:
        body = event.get("body")
        if not body:
            raise ValueError("Invalid request. The request body is missing!")
        body = json.loads(body)

        for key in ["username", "task"]:
            if not body.get(key):
                raise ValueError(f"{key} is empty")

        task = {
            "task_id": uuid.uuid4().hex,
            "username": body["username"],
            "task": body["task"],
            "Finished": bool(body.get("Finished", False)),
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")
        }
        response = table.put_item(Item=task)

        status_code = 201
        resp = {"description": "Successfully added a new task."}
    except ValueError as e:
        status_code = 400
        resp = {"description": f"Bad request. {str(e)}"}
    except Exception as e:
        status_code = 500
        resp = {"description": str(e)}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp)
    }

def change_finished_task(event, context):
    
    try:
        path_params = event.get("pathParameters", {})
        task_id = path_params.get("task_id", "")
        if not task_id:
            raise ValueError("Invalid request. The path parameter 'task_id' is missing")
        
        body = json.loads(event.get("body", "{}"))
        finished_status = bool(body.get("Finished", False))
        
        response = table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET Finished = :fin",
            ExpressionAttributeValues={
                ':fin': finished_status
            },
            ReturnValues="UPDATED_NEW"
        )
        
        status_code = 200
        resp = {"description": "Update successful", "updatedAttributes": response.get('Attributes')}
    
    except ValueError as e:
        status_code = 400
        resp = {"description": f"Bad request. {str(e)}"}
    except Exception as e:
        status_code = 500
        resp = {"description": f"Internal server error: {str(e)}"}
    
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp)
    }

def delete_task(event, context):

    try:
        path_params = event.get("pathParameters", {})
        task_id = path_params.get("task_id", "")
        if not task_id:
            raise ValueError("Invalid request. The path parameter 'task_id' is missing")
        
        response = table.delete_item(
            Key={"task_id": task_id}
        )

        status_code = 204
        resp = {"description": "Successfully deleted."}
    except ValueError as e:
        status_code = 400
        resp = {"description": f"Bad request. {str(e)}"}
    except Exception as e:
        status_code = 500
        resp = {"description": str(e)}
    return {
        "statusCode": status_code,
        "headers": HEADERS,
        "body": json.dumps(resp)
    }
