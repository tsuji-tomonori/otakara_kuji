from typing import Any, TypeVar

from aws_cdk import aws_apigateway as apigw
from constructs import Construct

from cdk.infra_construct import InfraConstruct
from cdk.lmd_construct import LambdaConstruct

Self = TypeVar("Self", bound="AppConstruct")


class AppConstruct(Construct):
    def __init__(
        self: Self,
        scope: Construct,
        construct_id: str,
        infra: InfraConstruct,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api = apigw.RestApi(
            scope=self,
            id="api",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
            ),
        )
        category = self.api.root.add_resource("category")
        omikuji = self.api.root.add_resource("omikuji")
        omikuji_category = omikuji.add_resource("{category}")

        self.create_category = LambdaConstruct(self, "create_category", infra)
        category.add_method(
            http_method="POST",
            integration=apigw.LambdaIntegration(
                handler=self.create_category.function,
            ),
        )
        assert self.create_category.function.role is not None
        infra.table_category.grant_read_write_data(self.create_category.function.role)
        self.create_category.function.add_environment(
            key="CATEGORY_TABLE_NAME",
            value=infra.table_category.table_name,
        )
        infra.table_item.grant_read_write_data(self.create_category.function.role)
        self.create_category.function.add_environment(
            key="ITEM_TABLE_NAME",
            value=infra.table_item.table_name,
        )

        self.list_category = LambdaConstruct(self, "list_category", infra)
        category.add_method(
            http_method="GET",
            integration=apigw.LambdaIntegration(
                handler=self.list_category.function,
            ),
        )
        assert self.list_category.function.role is not None
        infra.table_category.grant_read_data(self.list_category.function.role)
        self.list_category.function.add_environment(
            key="CATEGORY_TABLE_NAME",
            value=infra.table_category.table_name,
        )

        self.delete_category = LambdaConstruct(self, "delete_category", infra)
        category.add_method(
            http_method="DELETE",
            integration=apigw.LambdaIntegration(
                handler=self.delete_category.function,
            ),
        )
        assert self.delete_category.function.role is not None
        infra.table_category.grant_read_write_data(self.delete_category.function.role)
        self.delete_category.function.add_environment(
            key="CATEGORY_TABLE_NAME",
            value=infra.table_category.table_name,
        )
        infra.table_item.grant_read_write_data(self.delete_category.function.role)
        self.delete_category.function.add_environment(
            key="ITEM_TABLE_NAME",
            value=infra.table_item.table_name,
        )

        self.omikuji = LambdaConstruct(self, "omikuji", infra)
        omikuji_category.add_method(
            http_method="GET",
            integration=apigw.LambdaIntegration(
                handler=self.omikuji.function,
            ),
        )
        assert self.omikuji.function.role is not None
        infra.table_category.grant_read_data(self.omikuji.function.role)
        self.omikuji.function.add_environment(
            key="CATEGORY_TABLE_NAME",
            value=infra.table_category.table_name,
        )
        infra.table_item.grant_read_data(self.omikuji.function.role)
        self.omikuji.function.add_environment(
            key="ITEM_TABLE_NAME",
            value=infra.table_item.table_name,
        )
