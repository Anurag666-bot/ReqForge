"""
Parameter model for representing a parameter associated with an endpoint.
"""

from typing import Dict, Any, Optional
from .base import BaseModel
from pydantic import Field
from enum import Enum


class ParameterLocation(str, Enum):
    """Locations where a parameter can appear."""
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    PATH = "path"
    BODY_JSON = "body-json"
    BODY_FORM = "body-form"
    BODY_RAW = "body-raw"


class ParameterDataType(str, Enum):
    """Data types for parameters."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class Parameter(BaseModel):
    """Represents a parameter associated with an endpoint."""

    type: str = Field(default="parameter", frozen=True)
    name: str = Field(description="Parameter name")
    location: str = Field(description="Where the parameter appears")
    data_type: str = Field(
        default=ParameterDataType.STRING.value,
        description="Data type of the parameter value"
    )