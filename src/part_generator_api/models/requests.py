from pydantic import BaseModel, Field, field_validator, model_validator
import json
from importlib.resources import files

_raw = json.loads(files("part_generator_api.data").joinpath("iso_4762.json").read_text())
ISO_4762_DIAMETERS = {float(k) for k in _raw}


class ScrewRequest(BaseModel):
    """
    Data model for screw input. Also validates ISO 4762 diameters.
    """
    diameter: float = Field(description="mm")
    length: float = Field(gt=0, le=200, description="mm")

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
    """
    Data model for washer input. Also validates inner diameter < outer diameter.
    """
    inner_diameter: float = Field(gt=0, le=100, description="mm")
    outer_diameter: float = Field(gt=0, le=100, description="mm")
    thickness: float = Field(gt=0, le=50, description="mm")

    @model_validator(mode="after")
    def check_diameters(self):
        if self.inner_diameter >= self.outer_diameter:
            raise ValueError(
                f"inner_diameter ({self.inner_diameter}) must be less than "
                f"outer_diameter ({self.outer_diameter})"
            )
        return self
