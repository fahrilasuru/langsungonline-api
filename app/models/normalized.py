from enum import Enum
from pydantic import BaseModel, Field

class TemplateType(str, Enum):
    LANDING_PAGE = "landing_page"
    COMPANY_PROFILE = "company_profile"
    PRODUCT_PAGE = "product_page"
    EVENT_PAGE = "event_page"

class ColorInfo(BaseModel):
    name: str | None = None
    value: str | None = None
    role: str | None = None
    source: str | None = None

class DesignInfo(BaseModel):
    style: list[str] = Field(default_factory=list)
    colors: list[ColorInfo] = Field(default_factory=list)
    typography: list[str] = Field(default_factory=list)
    layout: str | None = None

class NormalizedInput(BaseModel):
    template: TemplateType

    title: str | None = None
    description: str | None = None

    requirements: list[str] = Field(default_factory=list)

    design: DesignInfo | None = None

    missing_information: list[str] = Field(
        default_factory=list
    )

    follow_up_questions: list[str] = Field(
        default_factory=list
    )