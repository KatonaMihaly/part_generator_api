from io import BytesIO

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from part_generator_api.geometry import ScrewGenerator, WasherGenerator
from part_generator_api.models import ScrewRequest, WasherRequest

router = APIRouter(prefix="/v1/generate", tags=["Generation"])

@router.post("/screw")
def generate_screw(params: ScrewRequest):
    generator = ScrewGenerator(diameter=params.diameter, length=params.length)
    step_bytes = generator.to_step_bytes()
    filename = f"screw_M{params.diameter:g}x{params.length:g}.step"
    return StreamingResponse(
        BytesIO(step_bytes),
        media_type="application/STEP",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/washer")
def generate_washer(params: WasherRequest):
    generator = WasherGenerator(
        inner_diameter=params.inner_diameter,
        outer_diameter=params.outer_diameter,
        thickness=params.thickness,
    )
    step_bytes = generator.to_step_bytes()
    filename = f"washer_{params.inner_diameter:g}x{params.outer_diameter:g}x{params.thickness:g}.step"
    return StreamingResponse(
        BytesIO(step_bytes),
        media_type="application/STEP",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
