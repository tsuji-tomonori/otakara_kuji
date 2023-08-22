import json
import os
import traceback
from typing import Any, NamedTuple, TypeVar

import boto3
import botocore
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBClient, DynamoDBServiceResource

logger = Logger()
dynamodb_client = boto3.client("dynamodb")
dynamodb_resource = boto3.resource("dynamodb")
ClientErrorSelf = TypeVar("ClientErrorSelf", bound="ClientError")
ServerErrorSelf = TypeVar("ServerErrorSelf", bound="ServerError")
ResponseSelf = TypeVar("ResponseSelf", bound="Response")


class ClientError(Exception):
    def __init__(self: ClientErrorSelf, input_param: str, message: str) -> None:
        self.message = message
        super().__init__(f"{message}: {input_param}")


class ServerError(Exception):
    def __init__(self: ServerErrorSelf, input_param: str, message: str) -> None:
        super().__init__(f"{message}: {input_param}")


class EnvParam(NamedTuple):
    CATEGORY_TABLE_NAME: str
    ITEM_TABLE_NAME: str

    @classmethod
    def from_env(cls: type["EnvParam"]) -> "EnvParam":
        try:
            return EnvParam(**{k: os.environ[k] for k in EnvParam._fields})
        except Exception as e:
            raise ServerError(
                json.dumps(os.environ),
                "Required environment variables are not set.",
            ) from e


class ApiBody(NamedTuple):
    category: str
    items: list[dict]

    @classmethod
    def from_event(cls: type["ApiBody"], event: dict[str, Any]) -> "ApiBody":
        try:
            body = json.loads(event["body"])
            return ApiBody(**{k: body[k] for k in ApiBody._fields})
        except Exception as e:
            raise ClientError(event["body"], "Invalid parameter.") from e


def delete_items(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    keys: list[dict],
) -> None:
    if len(keys) == 0:
        return
    table = db_resource.Table(table_name)
    try:
        with table.batch_writer() as batch:
            for key in keys:
                batch.delete_item(Key=key)
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error
        else:
            raise ClientError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error


def query_items(
    client: DynamoDBClient,
    db_name: str,
    key: str,
    value: str,
    query: str,
) -> list[str]:
    paginator = client.get_paginator("query")
    response_iterator = paginator.paginate(
        TableName=db_name,
        KeyConditions={
            key: {"ComparisonOperator": "EQ", "AttributeValueList": [{"S": value}]},
        },
    )
    try:
        return list(response_iterator.search(query))
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                query,
                error.response["Error"]["Message"],
            ) from error
        elif error.response["Error"]["Code"] == "ResourceNotFoundException":
            return []
        else:
            raise ClientError(
                query,
                error.response["Error"]["Message"],
            ) from error


def get_item(
    db_resource: DynamoDBServiceResource,
    table_name: str,
    key: dict,
) -> dict[str, Any] | None:
    table = db_resource.Table(table_name)
    try:
        return table.get_item(Key=key).get("Item")
    except botocore.exceptions.ClientError as error:
        if error.response["Error"]["Code"] == "InternalServerError":
            raise ServerError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error
        elif error.response["Error"]["Code"] == "ResourceNotFoundException":
            return None
        else:
            raise ClientError(
                json.dumps(key),
                error.response["Error"]["Message"],
            ) from error


class Response(NamedTuple):
    status_code: int
    message: str

    def data(self: ResponseSelf) -> dict[str, Any]:
        return {
            "statusCode": self.status_code,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, DELETE",
                "Access-Control-Allow-Credentials": True,
                "Access-Control-Allow-Headers": "origin, x-requested-with",
            },
            "body": json.dumps(
                {
                    "message": self.message,
                },
            ),
            "isBase64Encoded": False,
        }


def service(
    body: ApiBody,
    db_client: DynamoDBClient,
    db_resource: DynamoDBServiceResource,
    env: EnvParam,
) -> Response:
    response_category = get_item(
        db_resource=db_resource,
        table_name=env.CATEGORY_TABLE_NAME,
        key={"category": body.category},
    )
    if response_category is None:
        raise ClientError(
            input_param=body.category,
            message=f"category is empty: {body.category}",
        )
    response_items = query_items(
        client=db_client,
        db_name=env.ITEM_TABLE_NAME,
        key="category",
        value=body.category,
        query="Items[].item_id.S",
    )
    delete_items(
        db_resource=db_resource,
        table_name=env.ITEM_TABLE_NAME,
        keys=[{"category": body.category, "item_id": x} for x in response_items],
    )
    delete_items(
        db_resource=db_resource,
        table_name=env.CATEGORY_TABLE_NAME,
        keys=[{"category": body.category}],
    )
    return Response(
        status_code=200,
        message="success",
    )


@logger.inject_lambda_context(
    correlation_id_path="requestContext.requestId",
)
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    try:
        return service(
            body=ApiBody.from_event(event),
            db_client=dynamodb_client,
            db_resource=dynamodb_resource,
            env=EnvParam.from_env(),
        ).data()
    except ServerError:
        logger.error(traceback.format_exc())
        return Response(
            status_code=500,
            message="internal server error. Please access again after some time.",
        ).data()
    except ClientError as ce:
        logger.warning(traceback.format_exc())
        return Response(
            status_code=400,
            message=f"client error. {ce.message}",
        ).data()
    except Exception:
        logger.error(traceback.format_exc())
        return Response(
            status_code=500,
            message="internal server error. Please contact the operator.",
        ).data()
