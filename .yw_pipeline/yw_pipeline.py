from typing import List

from pydantic import BaseModel
from youwol.environment.forward_declaration import YouwolEnvironment
from youwol.environment.models import IPipelineFactory
from youwol.environment.models_project import Artifact, Flow, Pipeline, PipelineStep, FileListing, BrowserApp, \
    Execution, FromAsset, BrowserAppGraphics
from youwol.pipelines.pipeline_typescript_weback_npm import PublishCdnRemoteStep, PublishCdnLocalStep
from youwol_utils.context import Context
from youwol_utils.utils_paths import parse_json


class InitStep(PipelineStep):
    id: str = "init"
    run: str = "yarn"
    

class BuildStep(PipelineStep):
    id: str = "build"
    run: str = "echo 'Nothing to do'"
    sources: FileListing = FileListing(
        include=["index.html", "package.json", "style.css"]
    )

    artifacts: List[Artifact] = [
        Artifact(
            id='dist',
            files=FileListing(
                include=["index.html", "package.json", "style.css"]
            )
        )
    ]


class PipelineConfig(BaseModel):
    target: BrowserApp


def pipeline(config: PipelineConfig) -> Pipeline:

    return Pipeline(
        target=config.target,
        tags=["javascript", "library", "npm"],
        projectName=lambda path: parse_json(path / "package.json")["name"],
        projectVersion=lambda path: parse_json(path / "package.json")["version"],
        steps=[
            InitStep(),
            BuildStep(),
            PublishCdnLocalStep(packagedArtifacts=['dist']),
            PublishCdnRemoteStep()
        ],
        flows=[
            Flow(
                name="prod",
                dag=[
                    "init > build > publish-local > publish-remote "
                ]
            )
        ]
    )


class PipelineFactory(IPipelineFactory):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def get(self, _env: YouwolEnvironment, _ctx: Context):

        config = PipelineConfig(
            target=BrowserApp(
                displayName="Todos",
                execution=Execution(
                    standalone=True,
                    parametrized=[
                        FromAsset(
                            match={"kind": "data", "mimeType": 'vdr/todos'},
                            parameters={"id": 'rawId'}
                        )
                    ]
                ),
                graphics=BrowserAppGraphics(
                    appIcon={'class': 'fas fa-check-circle fa-2x'},
                    fileIcon={}
                ),
            )
        )
        return pipeline(config)
