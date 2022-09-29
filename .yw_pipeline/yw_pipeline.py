from typing import List

from youwol.environment.forward_declaration import YouwolEnvironment
from youwol.environment.models import IPipelineFactory
from youwol.environment.models_project import Artifact, Flow, Pipeline, PipelineStep, FileListing, BrowserApp, \
    Execution, BrowserAppGraphics
from youwol.pipelines.pipeline_typescript_weback_npm import PublishCdnLocalStep, \
    create_sub_pipelines_publish
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


class PipelineFactory(IPipelineFactory):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def get(self, _env: YouwolEnvironment, ctx: Context):

        publish_remote_steps, dags = await create_sub_pipelines_publish(start_step="publish-local", context=ctx)

        return Pipeline(
            target=BrowserApp(
                displayName="Todos",
                execution=Execution(
                    standalone=True
                ),
                graphics=BrowserAppGraphics(
                    appIcon={'class': 'fas fa-check-circle fa-2x'},
                    fileIcon={}
                ),
            ),
            tags=["javascript", "library", "npm"],
            projectName=lambda path: parse_json(path / "package.json")["name"],
            projectVersion=lambda path: parse_json(path / "package.json")["version"],
            steps=[
                InitStep(),
                BuildStep(),
                PublishCdnLocalStep(packagedArtifacts=['dist']),
                *publish_remote_steps
            ],
            flows=[
                Flow(
                    name="prod",
                    dag=[
                        "init > build > publish-local",
                        *dags
                    ]
                )
            ]
        )
