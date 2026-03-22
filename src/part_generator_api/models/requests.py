from pydantic import BaseModel, Field, field_validator, model_validator

ISO_4762_DIAMETERS = [
    1.6, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 36, 42, 48, 56, 64
]


class ScrewRequest(BaseModel):
    diameter: float
    length: float = Field(gt=0, description="mm")

    @field_validator("diameter")
    @classmethod
    def validate_diameter(cls, v):
        if v not in ISO_4762_DIAMETERS:
            valid = ", ".join(f"M{d:g}" for d in ISO_4762_DIAMETERS)
            raise ValueError(
                f"Diameter {v:g} mm is not a standard ISO 4762 size. Valid sizes: {valid}"
            )
        return v


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
