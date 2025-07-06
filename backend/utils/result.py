from typing import Generic, TypeVar, Literal, Union, Annotated
from pydantic import BaseModel, Field, TypeAdapter
from requests import Response

ModelT = TypeVar("ModelT", bound=BaseModel)


class SuccessResponse(BaseModel, Generic[ModelT]):
    """成功时的响应模型 (success=True)"""

    success: Literal[True]
    msg: None = None
    data: ModelT


class ErrorResponse(BaseModel):
    """失败时的响应模型 (success=False)"""

    success: Literal[False]
    msg: str
    data: None = None


DiscriminatedApiResponse = Annotated[
    Union[SuccessResponse[ModelT], ErrorResponse],
    Field(discriminator="success"),
]


def safe_json_response(response: Response, data_model: type[ModelT]):
    api_response_adapter = TypeAdapter(DiscriminatedApiResponse[data_model])
    parsed_response = api_response_adapter.validate_python(response.json())
    return parsed_response
