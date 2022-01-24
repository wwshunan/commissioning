from fastapi import FastAPI
import fastapi_plugins

@fastapi_plugins.registered_configuration
class AppSettings(
    fastapi_plugins.ControlSettings,
    fastapi_plugins.RedisSettings,
    fastapi_plugins.SchedulerSettings,
):
    api_name: str = str(__name__)

@fastapi_plugins.registered_configuration(name='sentinel')
class AppSettingsSentinel(AppSettings):
    redis_type = fastapi_plugins.RedisType.sentinel
    redis_sentinels = 'localhost:26379'


def register_redis(app: FastAPI, config) -> None:
    @app.on_event('startup')
    async def on_startup() -> None:
        await fastapi_plugins.config_plugin.init_app(app, config)
        await fastapi_plugins.config_plugin.init()
        await fastapi_plugins.redis_plugin.init_app(app, config=config)
        await fastapi_plugins.redis_plugin.init()
        await fastapi_plugins.control_plugin.init_app(
            app,
            config=config,
            version='0.1',
            environ=config.dict()
        )
        await fastapi_plugins.control_plugin.init()


    @app.on_event('shutdown')
    async def on_shutdown() -> None:
        await fastapi_plugins.control_plugin.terminate()
        await fastapi_plugins.redis_plugin.terminate()
        await fastapi_plugins.config_plugin.terminate()