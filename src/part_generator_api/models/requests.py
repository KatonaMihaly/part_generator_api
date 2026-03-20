from pydantic import BaseModel, Field, model_validator


class ScrewRequest(BaseModel):
    diameter: float = Field(gt=0, description="mm")
    length: float = Field(gt=0, description="mm")


class WasherRequest(BaseModel):
    inner_diameter: float = Field(gt=0, description="mm")
    outer_diameter: float = Field(gt=0, description="mm")
    thickness: float = Field(gt=0, description="mm")

    @model_validator(mode="after")
    def check_diameters(self):
        if self.inner_diameter >= self.outer_diameter:
            raise ValueError(
                f"inner_diameter ({self.inner_diameter}) must be less than "
                f"outer_diameter ({self.outer_diameter})"
            )
        return self
