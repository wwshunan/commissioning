class TaskException(Exception):
    def __init__(self, *args: object, detail) -> None:
        super().__init__(*args)
        self.detail = detail

    def __str__(self) -> str:
        return self.detail

def raise_exception(detail):
    exception = TaskException(detail=detail)
    raise exception