from pydantic import BaseModel


class ModuleStatusResponse(BaseModel):
    module: str
    status: str = "not_implemented"
