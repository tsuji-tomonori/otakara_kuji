import aws_cdk as cdk
from aws_cdk import Tags

from cdk.root_stack import OtakaraKujiStack


def add_name_tag(scope):  # noqa: ANN001, ANN201
    for child in scope.node.children:
        if cdk.Resource.is_resource(child):
            Tags.of(child).add("Name", child.node.path.replace("/", "-"))
        add_name_tag(child)


app = cdk.App()
stack = OtakaraKujiStack(app, "OtakaraKuji")
Tags.of(app).add("Project", "OtakaraKuji")
add_name_tag(app)
app.synth()
