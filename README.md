# Part Generator API

A FastAPI service that generates FEM-simplified STEP files for screws and flat washers. Packaged with UV, containerised with Docker, with an optional Streamlit GUI for manual use.

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
│  models/                 - Pydantic                          │
│  ScrewRequest            - validates data model              │
│  WasherRequest           - validates data model              │
└───────────────────────────────┬──────────────────────────────┘
                                │ validated data object
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  geometry/                - build123d                        │
│  BaseGeometry (ABC)                                          │
│    ├── ScrewGenerator     - generate geomety                 │
│    └── WasherGenerator    - generate geomety                 │
└───────────────────────────────┬──────────────────────────────┘
                                │ STEP bytes (via temp file)
                                ▼
┌──────────────────────────────────────────────────────────────┐
│  routers/                   - FastAPI                        │
│  POST /v1/generate/screw    - StreamingResponse (.step)      │
│  POST /v1/generate/washer   - StreamingResponse (.step)      │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                     downloaded .step file                    │
└──────────────────────────────────────────────────────────────┘
```

### Source layout

```
src/part_generator_api/
├── main.py               FastAPI application entry point
├── models/
│   └── requests.py       Pydantic models
├── geometry/
│   ├── base.py           Abstract base class
│   ├── screw.py          
│   └── washer.py         
├── data/
│   └── iso_4762.json     Nominal dimensions dictionary
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

The `src/` layout keeps the installable package (`part_generator_api`) isolated from project-level files, avoiding accidental imports and ensuring the installed package behaves identically whether installed locally or inside Docker.

The `models/` and the `geometry/` are separate packages because they have different dependency surfaces and different failure modes in two layers. The `models/` depends only on Pydantic and runs at request parse time; `geometry/` depends on build123d (which requires OpenCascade system libraries) and runs during part generation. Keeping them separate makes it possible to test validation without a geometry engine, and geometry without an HTTP stack.

### OOP design: BaseGeometry (Template Method pattern)

`BaseGeometry` is an abstract base class (ABC) with one abstract method `generate()` and one concrete method `to_step_bytes()`. The concrete method contains the OpenCascade temp-file workaround (build123d's `export_step` does not accept a `BytesIO` stream — it requires a file path), so neither `ScrewGenerator` nor `WasherGenerator` need to repeat it. Subclasses only implement `generate()` and return a build123d `Shape`; serialisation to bytes is handled once in the base.

### Optimisation for CAE workflow

The `ISO_4762_HEAD` dictionary in `screw.py` encodes the exact nominal values from ISO 4762:2004 / DIN 912 for all 23 standard sizes (M1.6 through M64). The geometry is deliberately simplified, no thread, no socket recess, no chamfer because those features would produce an impractically fine mesh without contributing to structural accuracy at the assembly level. The simplification is intentional and consistent with standard FEM meshing practice; the critical dimensions (shank diameter, shank length, head diameter, head height) are exact per the standard.

The same principle applies to the anchor point: both generators place the coordinate origin at the bottom-face centre. The part can be inserted at a bolt-hole position without any offset correction in the assembler.

---

## 2. Setup & Deployment

| Goal | Path |
|---|---|
| Run the API (Python already installed) | [Local install](#local-install) |
| Run without installing Python or dependencies | [Docker](#docker) |
| Modify or contribute to the code | [Local development](#local-development) |

### Prequisites (cold start)

Windows:

1) Clone/download the repository.
2) Install Python (3.12<=, <3.14).
3) Create a virtual environment and activate.
4) Install uv: pip install uv
--> local install or local development
5) Install docker: visit https://www.docker.com/products/docker-desktop/
6) 

### Local install

Install the package and start the API from the project directory:

```bash
uv pip install .
uvicorn part_generator_api.main:app
```

The API is available at `http://localhost:8000`.

To uninstall the package:

```bash
uv pip uninstall part-generator-api
```

### Docker

No Python installation required — only Docker.

```bash
docker build -t part-generator-api .
docker run -p 8000:8000 part-generator-api
```

The container runs as a non-root user (`appuser`). The GUI is not included in the
image; see [Streamlit GUI](#streamlit-gui-optional-local-only) below if you want it.

### Local development

An editable install (`-e`) links the package directly to the `src/` directory so
code changes are reflected immediately without reinstalling. `--reload` restarts
the server automatically on file changes.

```bash
uv pip install -e ".[dev]"
uvicorn part_generator_api.main:app --reload
```

The API is available at `http://localhost:8000`.

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

## 3. CLI Usage

No additional packages required — `curl` is pre-installed on Windows and most Linux
distributions.

### Check health

```bash
curl http://localhost:8000/health
```

### Generate a screw

```bash
curl -X POST http://localhost:8000/v1/generate/screw -H "Content-Type: application/json" -d '{"diameter": 12, "length": 80}' -OJ
```

Saves `screw_M12.0x80.0.step` in the current directory.

### Generate a washer

```bash
curl -X POST http://localhost:8000/v1/generate/washer -H "Content-Type: application/json" -d '{"inner_diameter": 13, "outer_diameter": 24, "thickness": 2}' -OJ
```

Saves `washer_13.0x24.0x2.0.step` in the current directory.

### Parameter reference

| Flag | What it does |
|---|---|
| `-X POST` | Use HTTP POST |
| `-H "Content-Type: application/json"` | Tell the server the body is JSON — required, otherwise FastAPI returns 422 |
| `-d '...'` | Request body. Must pass validation (see API docs below) |
| `-OJ` | Save the response to a file using the filename from the `Content-Disposition` header |

---

## 4. API Documentation

### `GET /health`

Liveness check.

**Response — HTTP 200:**
```json
{"status": "ok"}
```

---

### `POST /v1/generate/screw`

Generates a FEM-optimised ISO 4762 screw and returns it as a STEP file to download.

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
Washer dimensions are user-specified; no standard is enforced.

**Request body (JSON):**

| Field            | Type  | Constraints                            | Description             |
|------------------|-------|----------------------------------------|-------------------------|
| `inner_diameter` | float | `> 0` and `<= 100`                     | Inner bore diameter, mm |
| `outer_diameter` | float | `> 0`, `<= 100`, and `> inner_diameter`| Outer ring diameter, mm |
| `thickness`      | float | `> 0` and `<= 50`                     | Washer thickness, mm    |

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

## 5. Testing & Validation Strategy

### Test layers

| File                      | Layer       | Tests | What is covered |
|---------------------------|-------------|-------|-----------------|
| `tests/test_models.py`    | Unit        | 25    | Pydantic validation: all 23 ISO 4762 diameters accepted; non-standard diameter, negative/zero values, inverted diameters, missing fields, and values above upper bounds all raise `ValidationError` with correct messages. |
| `tests/test_geometry.py`  | Unit        | 6     | build123d output: STEP bytes non-empty, `ISO-10303-21` header present in first 100 bytes, bounding-box dimensions match expected ISO 4762 nominal values. |
| `tests/test_endpoints.py` | Integration | 11    | Full HTTP round-trip via FastAPI `TestClient`: HTTP 200 on valid input; `Content-Type: application/STEP`; `ISO-10303-21` in response body; `Content-Disposition` filename correct; HTTP 422 on invalid and missing parameters. |
| `tests/test_health.py`    | Integration | 1     | Health endpoint returns HTTP 200 and `{"status": "ok"}`. |
| **Total**                 |             | **43**|                 |

### How to run

After installing the package in a development environment:

```bash
python -m unittest discover -s tests
```

Without installing the package:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

### Design decisions

**`unittest` not pytest.** The standard library `unittest` module is sufficient for
this scope and introduces no extra dependency. `httpx` (required by FastAPI's
`TestClient`) is the only dev-only addition, declared in `[project.optional-dependencies]` under `dev`.

**`TestClient` not a real server.** Integration tests use FastAPI's `TestClient`
(backed by `httpx`), which runs the app in-process. This avoids port binding,
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

**`def` not `async def` on route handlers.** FastAPI runs on an async event loop:
a single thread that switches between tasks whenever one yields control (at an `await`).
The geometry pipeline calls OpenCascade — CPU-bound blocking work with no `await` points.
Declaring the handlers as plain `def` causes FastAPI to automatically offload them
to a threadpool, keeping the event loop free to serve other requests while geometry
is being computed. Declaring them `async def` would run them directly on the event loop,
blocking it for 1–3 seconds per request and degrading concurrency under load. The threadpool
has a bounded size, so very high concurrency can still queue up but that's a scaling problem.

**`/v1/` prefix on generation endpoints.** If a breaking change is needed later
(different response format, new required fields), a `/v2/generate/screw` endpoint can
coexist with `/v1/` without removing the working original. Clients that depend on `/v1/`
continue to work. Omitting the version now would force a flag day for all consumers
at the first breaking change.

---

## 6. Limitations & Future Work

### Geometric simplifications

The screw geometry consists of two cylinders (shank and head) with no thread helix,
no hex socket recess, and no chamfer. This is deliberate for FEM use: thread detail
produces an impractically fine mesh without improving structural accuracy at the
joint level. Any simulation requiring thread contact or socket loads would need a
more detailed model.

The washer geometry is a Boolean subtraction of two cylinders with no chamfer. It
is geometrically correct for flat washers but does not model spring washers or any other variant.

### Standard coverage

Only ISO 4762 screws are supported, other variants are not implemented.

Washer dimensions are user-specified and not validated against any standard.
The user is responsible for entering consistent dimensions.

### Operational limitations

- No persistent storage. STEP files are generated fresh on every request and not
  cached. High request volumes will produce proportionally high CPU usage from
  the OpenCascade kernel.
- No authentication or rate limiting on any endpoint.
- No batch endpoint. Each request generates one part. Generating an assembly
  (e.g. bolt + washer stack) requires separate requests.
- Only STEP (ISO 10303-21) output. Other exchange formats are not implemented.

### Potential future work

**Geometry and standards**
- Extend screw and washer variations.
- Add more type of parts.

**API and output**
- Batch endpoint returning a ZIP archive of multiple parts in one request.
- Response caching keyed on request parameters. STEP files are currently generated fresh on every request; repeated calls with the same parameters hit the OpenCascade kernel unnecessarily.
- Material metadata embedded in STEP file attributes.
- Authentication and rate limiting for production deployment.

**Infrastructure**
- `uv sync` with a committed `uv.lock` for fully reproducible installs across environments.
- CI/CD pipeline with containerised test execution.
- Cloud deployment: the GUI already reads `API_URL` from an environment variable, so the API and GUI can be deployed to a hosted platform with no code changes.
