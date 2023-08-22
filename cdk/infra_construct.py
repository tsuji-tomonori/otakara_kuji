from typing import Any, TypeVar

import aws_cdk as cdk
from aws_cdk import aws_dynamodb as dynamdb
from aws_cdk import aws_sns as sns
from constructs import Construct

Self = TypeVar("Self", bound="InfraConstruct")


class InfraConstruct(Construct):
    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB
        self.table_category = dynamdb.Table(
            scope=self,
            id="category",
            partition_key=dynamdb.Attribute(
                name="category",
                type=dynamdb.AttributeType.STRING,
            ),
            billing_mode=dynamdb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self.table_item = dynamdb.Table(
            scope=self,
            id="item",
            partition_key=dynamdb.Attribute(
                name="category",
                type=dynamdb.AttributeType.STRING,
            ),
            sort_key=dynamdb.Attribute(
                name="item_id",
                type=dynamdb.AttributeType.NUMBER,
            ),
            billing_mode=dynamdb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # AWS SNS
        self.sns_topic = sns.Topic(
            self,
            id="topic",
        )
