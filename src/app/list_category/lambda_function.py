import json
import os
import traceback
from typing import Any, NamedTuple, TypeVar

import boto3
import botocore
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_dynamodb import DynamoDBClient

logger = Logger()
dynamodb_client = boto3.client("dynamodb")
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

    @classmethod
    def from_env(cls: type["EnvParam"]) -> "EnvParam":
        try:
            return EnvParam(**{k: os.environ[k] for k in EnvParam._fields})
        except Exception as e:
            raise ServerError(
                json.dumps(os.environ),
                "Required environment variables are not set.",
            ) from e


def scan_items(client: DynamoDBClient, db_name: str, query: str) -> list[str]:
    paginator = client.get_paginator("scan")
    response_iterator = paginator.paginate(
        TableName=db_name,
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


class Response(NamedTuple):
    status_code: int
    message: str | list[str]

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
    db_client: DynamoDBClient,
    env: EnvParam,
) -> Response:
    response_items = scan_items(
        client=db_client,
        db_name=env.CATEGORY_TABLE_NAME,
        query="Items[].category.S",
    )
    return Response(
        status_code=200,
        message=response_items,
    )


@logger.inject_lambda_context(
    correlation_id_path="requestContext.requestId",
)
def lambda_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    try:
        return service(
            db_client=dynamodb_client,
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
