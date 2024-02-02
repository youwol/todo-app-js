from youwol.app.environment import YouwolEnvironment
from youwol.app.routers.projects import (BrowserApp, BrowserAppGraphics,
                                         Execution, IPipelineFactory)
from youwol.pipelines.pipeline_raw_app import PipelineConfig, pipeline
from youwol.utils import Context


class PipelineFactory(IPipelineFactory):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def get(self, _env: YouwolEnvironment, ctx: Context):
        config = PipelineConfig(
            target=BrowserApp(
                displayName="Todos",
                execution=Execution(standalone=True),
                graphics=BrowserAppGraphics(
                    appIcon={"class": "fas fa-check-circle fa-2x"}, fileIcon={}
                ),
            ),
            with_tags=["javascript", "library", "npm"],
        )
        return await pipeline(config=config, context=ctx)
