from fastapi import FastAPI

from part_generator_api.routers import generate_router

app = FastAPI(title="Part Generator API", version="0.1.0")

app.include_router(generate_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
