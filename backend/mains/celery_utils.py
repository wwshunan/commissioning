def init_celery(celery, app):
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                import inspect
                call_res = TaskBase.__call__(self, *args, **kwargs)
                return call_res
                #return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask