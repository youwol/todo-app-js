"""
This pipeline serves as example of a custom (simple) pipeline created from scratch.

More elaborated pipelines are provided as python modules, usually published in PyPi.
See the py-youwol documentation https://l.youwol.com/doc/py-youwol
"""

from typing import List
from youwol.environment import YouwolEnvironment
from youwol.environment.models_project import Artifact, Flow, Pipeline, PipelineStep, FileListing, BrowserApp, \
    Execution, BrowserAppGraphics, IPipelineFactory
from youwol.pipelines.pipeline_typescript_weback_npm import PublishCdnLocalStep, \
    create_sub_pipelines_publish
from youwol_utils.context import Context
from youwol_utils.utils_paths import parse_json

index_html = "index.html"
package_json = "package.json"
style_css = "style.css"

all_files = [index_html, package_json, style_css]


class InitStep(PipelineStep):
    """
    This defines a step called 'init', when executed it triggers the shell command 'yarn' from the project folder.
    """
    id: str = "init"
    run: str = "yarn"

    """
    Providing the 'sources' attribute allows to automatically check the status of this step:
    *  if no run has already been executed => none
    *  if the fingerprint of the files have changed => out-of-date 
    *  if the fingerprint of the files did not changed => sync
    """
    sources: FileListing = FileListing(
        include=[package_json]
    )


class BuildStep(PipelineStep):
    """
    This step does not trigger any action (beside the 'echo').
    Its purpose is to define an artifact 'dist' that includes the project's files.
    Later in this file it is referenced as unique contribution to the published bundle.
    """
    id: str = "build"
    run: str = "echo 'Nothing to do'"
    sources: FileListing = FileListing(
        include=all_files
    )

    """
    One artifact is defined, it is called 'dist' and contains the files 'all_files'.
    """
    artifacts: List[Artifact] = [
        Artifact(
            id='dist',
            files=FileListing(
                include=all_files
            )
        )
    ]


class PipelineFactory(IPipelineFactory):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def get(self, _env: YouwolEnvironment, ctx: Context):

        # The function 'create_sub_pipelines_publish' create children pipelines dedicated to publications.
        # It uses one or more CdnTarget & NpmTarget, defined in the Py-YouWol global configuration file.
        # See dedicated documentation here: https://l.youwol.com/doc/py-youwol
        publish_remote_steps, dags = await create_sub_pipelines_publish(start_step="cdn-local", context=ctx)

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
            projectName=lambda path: parse_json(path / package_json)["name"],
            projectVersion=lambda path: parse_json(path / package_json)["version"],
            # Below are defined the steps of the pipeline
            steps=[
                InitStep(),
                BuildStep(),
                # The attribute 'packagedArtifacts' defines which artifacts to include in the bundle published
                # in the ecosystem. Here, only the dist artifact (defined in the BuildStep class).
                PublishCdnLocalStep(packagedArtifacts=['dist']),
            ] + publish_remote_steps,
            # Below are defined the connections between the steps.
            flows=[
                Flow(
                    name="prod",
                    dag=[
                        "init > build > cdn-local",
                    ] + dags
                )
            ]
        )
