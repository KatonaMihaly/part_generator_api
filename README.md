# Part Generator API

A FastAPI service that generates FEM-simplyfied STEP files for crews and flat washers.
Packaged with UV, containerised with Docker, with an optional Streamlit GUI for manual use.

---

## 1. Architecture

### Layer diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        HTTP Client                           │
│               (curl / Streamlit GUI / CAE tool)              │
└───────────────────────────────┬──────────────────────────────┘
                                │ JSON request body
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  models/   (Pydantic)                                        │
│  ScrewRequest   — validates ISO 4762 diameter, length > 0    │
│  WasherRequest  — validates inner < outer, all fields > 0    │
└───────────────────────────────┬──────────────────────────────┘
                                │ validated parameter objects
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  geometry/   (build123d)                                     │
│  BaseGeometry (ABC)                                          │
│    ├── ScrewGenerator   — ISO 4762 head + shank cylinders    │
│    └── WasherGenerator  — outer cylinder minus inner bore    │
└───────────────────────────────┬──────────────────────────────┘
                                │ STEP bytes (via temp file)
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  routers/   (FastAPI)                                        │
│  POST /v1/generate/screw    → StreamingResponse (.step)      │
│  POST /v1/generate/washer   → StreamingResponse (.step)      │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  main.py                                                     │
│  FastAPI app — mounts routers, exposes GET /health           │
└──────────────────────────────────────────────────────────────┘
```

### Source layout

```
src/part_generator_api/
├── main.py               FastAPI application entry point
├── models/
│   └── requests.py       ScrewRequest and WasherRequest Pydantic models
├── geometry/
│   ├── base.py           BaseGeometry ABC: generate() + to_step_bytes()
│   ├── screw.py          ScrewGenerator + ISO_4762_HEAD lookup table
│   └── washer.py         WasherGenerator
└── routers/
    └── generate.py       /v1/generate/* endpoints
gui/
└── app.py                Streamlit GUI (runs separately; not in Docker)
tests/
├── test_models.py        Unit — Pydantic validation
├── test_geometry.py      Unit — build123d output
├── test_endpoints.py     Integration — HTTP contract
└── test_health.py        Integration — health endpoint
Dockerfile
pyproject.toml
requirements.txt          GUI + dev dependencies (not used by Docker)
```

The `src/` layout keeps the installable package (`part_generator_api`) isolated from
project-level files, avoiding accidental imports and ensuring the installed package
behaves identically whether installed locally or inside Docker.

`models/` and `geometry/` are separate packages because they have different
dependency surfaces and different failure modes. `models/` depends only on Pydantic
and runs at request parse time; `geometry/` depends on build123d (which requires
OpenCascade system libraries) and runs during part generation. Keeping them separate
makes it possible to test validation without a geometry engine, and geometry without
an HTTP stack.

### OOP design: BaseGeometry

`BaseGeometry` is an abstract base class (ABC) with one abstract method `generate()`
and one concrete method `to_step_bytes()`. The concrete method contains the
OpenCascade temp-file workaround (build123d's `export_step` does not accept a
`BytesIO` stream — it requires a file path), so neither `ScrewGenerator` nor
`WasherGenerator` need to repeat it. Subclasses only implement `generate()` and
return a build123d `Shape`; serialisation to bytes is handled once in the base.

### ISO 4762 lookup table: the CAE workflow rationale

Head dimensions for socket-head cap screws are **not proportional** to nominal
diameter. A proportional approximation (e.g. `dk ≈ 1.5 * d`) can be off by several
millimetres for the sizes most commonly used in structural FEM models (M8–M24).
Errors of that magnitude affect contact area, pretension cross-section, and
ultimately the stress distribution in the joint.

The `ISO_4762_HEAD` dictionary in `screw.py` encodes the exact nominal values from
ISO 4762:2004 / DIN 912 for all 23 standard sizes (M1.6 through M64). The geometry
is deliberately simplified — no thread helix, no socket recess, no chamfer — because
those features would produce an impractically fine mesh without contributing to
structural accuracy at the assembly level. The simplification is intentional and
consistent with standard FEM meshing practice; the critical dimensions (shank
diameter, shank length, head diameter, head height) are exact per the standard.

The same principle applies to the anchor point: both generators place the coordinate
origin at the bottom-face centre of the shank so the part can be inserted at a
bolt-hole position without any offset correction in the assembler.

---

## 2. Setup & Deployment

### Prerequisites

- Python 3.12+
- [UV](https://github.com/astral-sh/uv) — `pip install uv`
- Docker (for containerised deployment only)

### Local development

Install the package with dev dependencies (adds `httpx` for `TestClient`):

```bash
uv pip install -e ".[dev]"
```

Start the API:

```bash
PYTHONPATH=src uvicorn part_generator_api.main:app --reload
```

The API is available at `http://localhost:8000`.

### Docker

```bash
docker build -t part-generator-api .
docker run -p 8000:8000 part-generator-api
```

The Docker image installs only the core API package (`pyproject.toml` dependencies).
The GUI is intentionally excluded — it is a local development tool that connects to
a separately running API instance. The container runs as a non-root user (`appuser`)
created at build time.

### Streamlit GUI (optional, local only)

Install GUI dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file at the project root:

```
API_URL=http://localhost:8000
```

Start the GUI:

```bash
streamlit run gui/app.py
```

The GUI provides a **Screw** tab (diameter selector populated from the same
`ISO_4762_DIAMETERS` list used by the API, plus a length input) and a **Washer**
tab (inner diameter, outer diameter, thickness). Each tab generates and downloads
the STEP file directly from the running API.

---

## 3. API Documentation

### `GET /health`

Liveness check.

**Response — HTTP 200:**
```json
{"status": "ok"}
```

---

### `POST /v1/generate/screw`

Generates a FEM-optimised ISO 4762 socket-head cap screw and returns it as a STEP
file download.

**Request body (JSON):**

| Field      | Type  | Constraints                           | Description              |
|------------|-------|---------------------------------------|--------------------------|
| `diameter` | float | Must be a standard ISO 4762 size (mm) | Nominal screw diameter   |
| `length`   | float | `> 0` and `<= 200`                    | Shank length in mm       |

Valid ISO 4762 diameters (mm):
`1.6, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 36, 42, 48, 56, 64`

**Example request:**
```json
{"diameter": 12, "length": 80}
```

**Success — HTTP 200:**
```
Content-Type: application/STEP
Content-Disposition: attachment; filename=screw_M12.0x80.0.step
Body: binary STEP file (ISO-10303-21)
```

**Validation error — HTTP 422:**

Returned when the diameter is not a standard ISO 4762 size, the length is outside
the valid range, or a required field is missing. The response body is a Pydantic
validation error with a human-readable message, for example:

```json
{
  "detail": [
    {
      "msg": "Value error, Diameter 13 mm is not a standard ISO 4762 size. Valid sizes: M1.6, M2, ..."
    }
  ]
}
```

---

### `POST /v1/generate/washer`

Generates a FEM-optimised flat washer and returns it as a STEP file download.
Washer dimensions are user-specified; no standard (e.g. ISO 7089) is enforced.

**Request body (JSON):**

| Field            | Type  | Constraints                            | Description             |
|------------------|-------|----------------------------------------|-------------------------|
| `inner_diameter` | float | `> 0` and `<= 100`                     | Inner bore diameter, mm |
| `outer_diameter` | float | `> 0`, `<= 100`, and `> inner_diameter`| Outer ring diameter, mm |
| `thickness`      | float | `> 0` and `<= 100`                     | Washer thickness, mm    |

**Example request:**
```json
{"inner_diameter": 13, "outer_diameter": 24, "thickness": 2}
```

**Success — HTTP 200:**
```
Content-Type: application/STEP
Content-Disposition: attachment; filename=washer_13.0x24.0x2.0.step
Body: binary STEP file (ISO-10303-21)
```

**Validation error — HTTP 422:**

Returned when `inner_diameter >= outer_diameter`, any value is zero or negative,
any value exceeds its upper bound, or a required field is missing.

---

### Interactive documentation

With the server running, FastAPI's auto-generated docs are available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 4. Testing & Validation Strategy

### Test layers

| File                      | Layer       | Tests | What is covered |
|---------------------------|-------------|-------|-----------------|
| `tests/test_models.py`    | Unit        | 19    | Pydantic validation: all 23 ISO 4762 diameters accepted; non-standard diameter, negative/zero values, inverted diameters, and missing fields all raise `ValidationError` with correct messages. |
| `tests/test_geometry.py`  | Unit        | 6     | build123d output: STEP bytes non-empty, `ISO-10303-21` header present in first 100 bytes, bounding-box dimensions match expected ISO 4762 nominal values. |
| `tests/test_endpoints.py` | Integration | 11    | Full HTTP round-trip via FastAPI `TestClient`: HTTP 200 on valid input; `Content-Type: application/STEP`; `ISO-10303-21` in response body; `Content-Disposition` filename correct; HTTP 422 on invalid and missing parameters. |
| `tests/test_health.py`    | Integration | 1     | Health endpoint returns HTTP 200 and `{"status": "ok"}`. |
| **Total**                 |             | **37**|                 |

### How to run

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

### Design decisions

**`unittest` not pytest.** The standard library `unittest` module is sufficient for
this scope and introduces no extra dependency. `httpx` (required by FastAPI's
`TestClient`) is the only dev-only addition, declared in `[project.optional-dependencies]`
under `dev`.

**`TestClient` not a real server.** Integration tests use FastAPI's `TestClient`
(backed by `httpx`), which runs the ASGI app in-process. This avoids port binding,
startup/teardown complexity, and network variance while still exercising the full
request-response cycle including middleware, routing, and Pydantic parsing.

**STEP format checked at two layers.** Geometry unit tests verify that `to_step_bytes()`
produces a valid ISO-10303-21 file directly from the generator. Endpoint integration
tests verify the same property in the HTTP response body. These are different failure
modes: a geometry failure would show up at the unit level; a serialisation or
streaming error (e.g. a broken `StreamingResponse` wrapper) would only show up at
the endpoint level. Checking both layers means failures are localised immediately.

**GUI has no automated tests.** `gui/app.py` contains no business logic — it
delegates all validation and generation to the API. The Streamlit UI populates the
diameter dropdown from the same `ISO_4762_DIAMETERS` list used by the models layer,
so it cannot present an invalid diameter. Manual verification is sufficient.

---

## 5. Limitations & Future Work

### Geometric simplifications

The screw geometry consists of two cylinders (shank and head) with no thread helix,
no hex socket recess, and no chamfer. This is deliberate for FEM use: thread detail
produces an impractically fine mesh without improving structural accuracy at the
joint level. Any simulation requiring thread contact or socket loads would need a
more detailed model.

The washer geometry is a Boolean subtraction of two cylinders with no chamfer. It
is geometrically correct for flat washers but does not model spring washers, tab
washers, or any other variant.

### Standard coverage

Only ISO 4762 socket-head cap screws are supported. Hex bolts (ISO 4014), hex
socket set screws, and countersunk variants are not implemented.

Washer dimensions are user-specified and not validated against any standard (e.g.
ISO 7089). The user is responsible for entering consistent dimensions.

### Operational limitations

- No persistent storage. STEP files are generated fresh on every request and not
  cached. High request volumes will produce proportionally high CPU usage from
  the OpenCascade kernel.
- No authentication or rate limiting on any endpoint.
- No batch endpoint. Each request generates one part. Generating an assembly
  (e.g. bolt + washer stack) requires separate requests.
- Only STEP (ISO 10303-21) output. Other exchange formats (IGES, STL, Parasolid)
  are not implemented.

### Potential future work

- Nut generator (ISO 4032 hex nuts) to complete the fastener set
- Hex bolt generator (ISO 4014)
- ISO 7089 / ISO 7090 standardised washer sizes
- Batch endpoint returning a ZIP archive of multiple parts
- Material metadata embedded in STEP file attributes
- CI/CD pipeline with containerised test execution
- Authentication and rate limiting for production deployment
