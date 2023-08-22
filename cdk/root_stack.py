from typing import Any, TypeVar

from aws_cdk import Stack
from constructs import Construct

from cdk.app_construct import AppConstruct
from cdk.infra_construct import InfraConstruct
from cdk.static_construct import StaticConstruct

Self = TypeVar("Self", bound="OtakaraKujiStack")


class OtakaraKujiStack(Stack):
    def __init__(
        self: Self,
        scope: Construct | None = None,
        construct_id: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.infra = InfraConstruct(self, "infra")
        self.static = StaticConstruct(self, "static")
        self.app = AppConstruct(self, "app", self.infra)
