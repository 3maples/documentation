# Estimate Documents Dialog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the estimate page's Documents dropdown with a "Documents (N)" dialog. The dialog lists generated Google Doc versions and generates new ones, using an "Additional Information" text (for `{{NOTES}}`) and uploaded images placed after the NOTES section.

**Architecture:** Images are processed with Pillow and stored in Firebase Storage. Each generated version records its text and images, and carries images forward by sharing blobs. During generation, the Google Docs API receives short-lived V4 signed URLs, and the images are inserted at a `{{NOTES_IMAGES}}` marker left by the `{{NOTES}}` text replacement. The doc endpoints move out of the 1,800-line `routers/estimates.py` into `routers/estimate_documents.py`. On the portal, a pure-helper module, a blob-URL hook, and a mount-is-open `DocumentsDialog` sit behind an `EstimateDocuments` button.

**Tech Stack:** FastAPI + Beanie, Pillow, firebase-admin Storage, Google Docs API v1, React 18 + Vitest + Testing Library, Tailwind 4.

**Spec:** [`2026-09-23-estimate-documents-dialog-design.md`](2026-09-23-estimate-documents-dialog-design.md)

## Global Constraints

- Images per document: **at most 10**. Per file: **at most 10MB** before processing.
- Accepted types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`. No PDFs and no HEIC.
- Processing: EXIF-rotate, flatten transparency onto white, scale down so the long edge is at most **2000px**, and output **JPEG quality 85**.
- Storage path: `estimate-doc-images/{company_id}/{estimate_object_id}/{image_id}.jpg`, where `image_id = uuid4().hex`.
- Signed URL: `generate_signed_url(version="v4", expiration=timedelta(minutes=10), method="GET")`.
- `additional_info`: stripped, **at most 5,000 characters** (422 above that). Blank prints **`--`**. `Estimate.notes` is never read by the doc path.
- Width of an image in the doc: `min(468pt, width_px × 0.75)`, with the height scaled to keep the aspect ratio.
- Image failures are fail-closed. The response is **502** with the detail `Couldn't add images to the document. Please try again.`
- A kept image id is resolved only against this estimate's own versions. Any other id → 400.
- Generated versions are read-only in the UI: they can only be opened or deleted (D8).
- Maple never writes `Estimate.notes` and never touches Additional Information. Its estimate notes are `Note` documents with parent type `estimate`, and they ignore the Draft/Review lock (D9).
- US spelling, sentence-case UI copy, and `<type>: <description>` commit messages ending with the `Co-Authored-By` trailer.
- After every `.py` change: `./run_mypy.sh <subtree>` and `./run_ruff.sh <subtree>` must be clean. Run only the related tests, never the full suite.
- **Every `git commit` needs Simon's explicit approval.** Commit steps below stage the files and propose the message; commit only after approval. Never push.
- There are three independent git repos: `platform/`, `portal/` and `documentation/`. Commit in the repo each task names.

## Review Focus

These are the most likely failure modes that the spec implies but doesn't spell out. Each has a pinned test in the task that owns the code.

1. **A transparent PNG** (a logo or screenshot) must come out on white. JPEG has no alpha channel, and a naive `convert("RGB")` paints transparent areas black. Pinned in Task 1.
2. **Whitespace-only Additional Information** (spaces or blank lines) must print `--`, not a blank NOTES section. Pinned in Task 2.
3. **Duplicate `keep_image_ids`** (a double-click, or a stale form) must place the image once, not twice. Pinned in Task 5.
4. **Deleting the latest version while the dialog is open** must not wipe the text being typed. It must also drop kept images that vanished with that version, or the next Generate returns a 400. Pinned in Task 7.
5. **An older portal still posting JSON** during the deploy window must keep generating (printing `--`) rather than failing with a 422. Pinned in Task 5.

---

## Task 1: Doc image model and storage service (platform)

**Files:**
- Modify: `platform/models/estimate.py` (add `DocImage` above `GoogleDocsVersion`, around line 513; add two fields to `GoogleDocsVersion`)
- Create: `platform/services/estimate_doc_images.py`
- Test: `platform/tests/test_estimate_doc_images.py`

**Interfaces:**
- Produces:
  - `models.estimate.DocImage(id: str, storage_path: str, file_name: str, width: int, height: int)`
  - `GoogleDocsVersion.additional_info: Optional[str] = None` and `GoogleDocsVersion.images: List[DocImage] = []`
  - `services.estimate_doc_images`:
    - constants `MAX_DOC_IMAGES = 10`, `MAX_DOC_IMAGE_FILE_SIZE_BYTES`, `MAX_DOC_IMAGE_EDGE_PX`, `MAX_DOC_IMAGE_PIXELS`, `SIGNED_URL_TTL`
    - `@dataclass ProcessedDocImage(content: bytes, width: int, height: int, file_name: str)`
    - `safe_file_name(raw: str | None) -> str`
    - `process_doc_image_upload(file_bytes: bytes, content_type: str, file_name: str | None) -> ProcessedDocImage`, which raises `HTTPException(400)`
    - `doc_image_storage_path(company_id: str, estimate_oid: str, image_id: str) -> str`
    - `store_doc_image(storage_path: str, content: bytes) -> None`
    - `signed_doc_image_url(storage_path: str) -> str`
    - `read_doc_image(storage_path: str) -> bytes`
    - `delete_doc_images(storage_paths: Iterable[str]) -> None`, which never raises
  - **Callers must use module-attribute calls** (`from services import estimate_doc_images as doc_images`, then `doc_images.store_doc_image(...)`). The router tests monkeypatch these functions on the module.

- [ ] **Step 1: Write the failing tests**

`platform/tests/test_estimate_doc_images.py`:

```python
"""Images attached to generated estimate Google Docs: processing + storage."""

import io
from datetime import timedelta

import pytest
from fastapi import HTTPException
from PIL import Image

from services import estimate_doc_images as doc_images


def _image_bytes(fmt="JPEG", size=(800, 600), mode="RGB", color=(120, 160, 90), exif_orientation=None) -> bytes:
    buf = io.BytesIO()
    image = Image.new(mode, size, color)
    kwargs = {}
    if exif_orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = exif_orientation
        kwargs["exif"] = exif
    image.save(buf, format=fmt, **kwargs)
    return buf.getvalue()


@pytest.mark.parametrize(
    "fmt,content_type",
    [("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp"), ("GIF", "image/gif")],
)
def test_accepts_supported_types_and_outputs_jpeg(fmt, content_type):
    out = doc_images.process_doc_image_upload(_image_bytes(fmt), content_type, "site.img")
    assert Image.open(io.BytesIO(out.content)).format == "JPEG"
    assert (out.width, out.height) == (800, 600)
    assert out.file_name == "site.img"


def test_rejects_unsupported_content_type_naming_the_file():
    with pytest.raises(HTTPException) as exc:
        doc_images.process_doc_image_upload(_image_bytes(), "image/heic", "IMG_0001.heic")
    assert exc.value.status_code == 400
    assert "IMG_0001.heic" in exc.value.detail


def test_rejects_bytes_that_are_not_an_image():
    with pytest.raises(HTTPException) as exc:
        doc_images.process_doc_image_upload(b"MZ\x90 not an image", "image/png", "x.png")
    assert exc.value.status_code == 400
    assert "x.png" in exc.value.detail


def test_rejects_empty_files():
    with pytest.raises(HTTPException) as exc:
        doc_images.process_doc_image_upload(b"", "image/jpeg", "empty.jpg")
    assert exc.value.status_code == 400


def test_rejects_files_over_the_size_cap(monkeypatch):
    monkeypatch.setattr(doc_images, "MAX_DOC_IMAGE_FILE_SIZE_BYTES", 10)
    with pytest.raises(HTTPException) as exc:
        doc_images.process_doc_image_upload(_image_bytes(), "image/jpeg", "big.jpg")
    assert exc.value.status_code == 400
    assert "10 MB" in exc.value.detail


def test_rejects_decompression_bombs(monkeypatch):
    monkeypatch.setattr(doc_images, "MAX_DOC_IMAGE_PIXELS", 10)
    with pytest.raises(HTTPException) as exc:
        doc_images.process_doc_image_upload(_image_bytes(size=(100, 100)), "image/jpeg", "bomb.jpg")
    assert exc.value.status_code == 400
    assert "too large" in exc.value.detail


def test_downscales_long_edge_to_2000px():
    out = doc_images.process_doc_image_upload(_image_bytes(size=(4000, 1000)), "image/jpeg", "wide.jpg")
    assert (out.width, out.height) == (2000, 500)


def test_applies_exif_rotation():
    out = doc_images.process_doc_image_upload(
        _image_bytes(size=(800, 600), exif_orientation=6), "image/jpeg", "phone.jpg"
    )
    assert (out.width, out.height) == (600, 800)


def test_flattens_transparency_onto_white():
    """Review Focus #1: a transparent PNG must not come out black."""
    png = _image_bytes("PNG", size=(10, 10), mode="RGBA", color=(0, 0, 0, 0))
    out = doc_images.process_doc_image_upload(png, "image/png", "logo.png")
    r, g, b = Image.open(io.BytesIO(out.content)).convert("RGB").getpixel((5, 5))
    assert min(r, g, b) > 240


def test_file_name_is_reduced_to_its_basename():
    out = doc_images.process_doc_image_upload(_image_bytes(), "image/jpeg", "../../etc\\photos\\gate.jpg")
    assert out.file_name == "gate.jpg"
    assert doc_images.safe_file_name(None) == "image"


def test_storage_path_shape():
    assert doc_images.doc_image_storage_path("c1", "e1", "i1") == "estimate-doc-images/c1/e1/i1.jpg"


class _FakeBlob:
    def __init__(self, bucket, path):
        self.bucket = bucket
        self.path = path
        self.cache_control = None

    def upload_from_string(self, content, content_type):
        self.bucket.uploads[self.path] = (content, content_type)

    def generate_signed_url(self, **kwargs):
        self.bucket.sign_calls.append((self.path, kwargs))
        return f"https://signed/{self.path}"

    def download_as_bytes(self):
        return self.bucket.uploads[self.path][0]

    def delete(self):
        if self.path in self.bucket.fail_deletes:
            raise RuntimeError("storage unavailable")
        self.bucket.deleted.append(self.path)


class _FakeBucket:
    def __init__(self):
        self.name = None
        self.uploads = {}
        self.sign_calls = []
        self.deleted = []
        self.fail_deletes = set()

    def blob(self, path):
        return _FakeBlob(self, path)


@pytest.fixture
def fake_bucket(monkeypatch):
    from config import settings

    bucket = _FakeBucket()

    class _Storage:
        @staticmethod
        def bucket(name):
            bucket.name = name
            return bucket

    monkeypatch.setattr(settings, "firebase_storage_bucket", "gs://unit-test-bucket")
    monkeypatch.setattr(doc_images, "storage", _Storage)
    monkeypatch.setattr(doc_images, "initialize_firebase_admin", lambda: None)
    return bucket


def test_store_read_and_sign(fake_bucket):
    doc_images.store_doc_image("p/a.jpg", b"jpeg-bytes")
    assert fake_bucket.name == "unit-test-bucket"
    assert fake_bucket.uploads["p/a.jpg"] == (b"jpeg-bytes", "image/jpeg")
    assert doc_images.read_doc_image("p/a.jpg") == b"jpeg-bytes"
    assert doc_images.signed_doc_image_url("p/a.jpg") == "https://signed/p/a.jpg"
    assert fake_bucket.sign_calls == [
        ("p/a.jpg", {"version": "v4", "expiration": timedelta(minutes=10), "method": "GET"})
    ]


def test_delete_is_best_effort(fake_bucket):
    fake_bucket.fail_deletes = {"p/bad.jpg"}
    doc_images.delete_doc_images(["p/bad.jpg", "", "p/ok.jpg"])
    assert fake_bucket.deleted == ["p/ok.jpg"]


def test_legacy_version_rows_load_without_new_fields():
    from models.estimate import GoogleDocsVersion

    legacy = GoogleDocsVersion.model_validate({
        "version": 1, "doc_id": "d", "doc_url": "u", "drive_file_id": "f",
        "file_name": "Estimate-E0001-V1", "created_by": "someone",
    })
    assert legacy.additional_info is None
    assert legacy.images == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_estimate_doc_images.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'services.estimate_doc_images'`.

- [ ] **Step 3: Add the model fields**

In `platform/models/estimate.py`, directly above `class GoogleDocsVersion(BaseModel):`:

```python
class DocImage(BaseModel):
    """An image placed after the NOTES section of a generated Google Doc.

    Stored in Firebase Storage (services/estimate_doc_images.py). A version
    that carries an image forward points at the SAME blob as the version it
    came from — deleting a version removes only blobs no other version still
    references (routers/estimate_helpers/doc_versions.py).
    """
    id: str  # uuid4 hex; stable across versions that reuse the image
    storage_path: str
    file_name: str  # original upload name, shown in the Documents dialog
    width: int  # post-processing pixels, used to size the image in the doc
    height: int
```

Append these to `GoogleDocsVersion`, after `estimate_snapshot`:

```python
    # Exactly what went into {{NOTES}}. None on versions generated before the
    # Documents dialog (2026-09-23), which printed Estimate.notes instead.
    additional_info: Optional[str] = None
    images: List[DocImage] = []
```

- [ ] **Step 4: Write the service**

`platform/services/estimate_doc_images.py`:

```python
"""Images attached to a generated estimate Google Doc.

Processed like company logos (services/company_logo.py) but stored WITHOUT a
public download token: Google fetches each one through a short-lived V4
signed URL while the doc is being built and keeps its own copy inside the
Doc, so nothing has to stay publicly readable afterwards.

Callers use module-attribute calls (`doc_images.store_doc_image(...)`) so
tests can swap the storage functions for an in-memory store.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from typing import Any, Iterable

from fastapi import HTTPException, status

try:
    from firebase_admin import storage
except ModuleNotFoundError:  # pragma: no cover - handled by runtime config/tests
    storage = None

from PIL import Image, ImageOps, UnidentifiedImageError
from PIL.Image import DecompressionBombError

from firebase_auth import initialize_firebase_admin
from services.company_logo import _normalized_bucket_name

logger = logging.getLogger(__name__)

MAX_DOC_IMAGES = 10
MAX_DOC_IMAGE_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_DOC_IMAGE_EDGE_PX = 2000
MAX_DOC_IMAGE_PIXELS = 50_000_000
DOC_IMAGE_JPEG_QUALITY = 85
SIGNED_URL_TTL = timedelta(minutes=10)
ALLOWED_DOC_IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp", "image/gif"})


@dataclass
class ProcessedDocImage:
    content: bytes
    width: int
    height: int
    file_name: str


def _bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def safe_file_name(raw: str | None) -> str:
    """The upload's own name without any client-supplied directory parts."""
    name = os.path.basename((raw or "").replace("\\", "/")).strip()
    return name[:200] or "image"


def process_doc_image_upload(file_bytes: bytes, content_type: str, file_name: str | None) -> ProcessedDocImage:
    name = safe_file_name(file_name)
    if not file_bytes:
        raise _bad_request(f'"{name}" is empty.')
    if len(file_bytes) > MAX_DOC_IMAGE_FILE_SIZE_BYTES:
        raise _bad_request(f'"{name}" is larger than 10 MB.')
    if str(content_type or "").strip().lower() not in ALLOWED_DOC_IMAGE_CONTENT_TYPES:
        raise _bad_request(f'"{name}" must be a JPEG, PNG, WebP or GIF image.')

    previous_max_pixels = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = MAX_DOC_IMAGE_PIXELS
    try:
        with Image.open(BytesIO(file_bytes)) as source:
            image = ImageOps.exif_transpose(source)
            image.load()
    except DecompressionBombError:
        raise _bad_request(f'"{name}" has dimensions that are too large.') from None
    except OSError:  # includes UnidentifiedImageError
        raise _bad_request(f'"{name}" could not be read as an image.') from None
    finally:
        Image.MAX_IMAGE_PIXELS = previous_max_pixels

    # JPEG has no alpha: flatten onto white, or transparent areas turn black.
    if image.mode in {"RGBA", "LA", "PA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        flattened = Image.new("RGB", rgba.size, (255, 255, 255))
        flattened.paste(rgba, mask=rgba.getchannel("A"))
        image = flattened
    else:
        image = image.convert("RGB")
    image.thumbnail((MAX_DOC_IMAGE_EDGE_PX, MAX_DOC_IMAGE_EDGE_PX), Image.Resampling.LANCZOS)

    output = BytesIO()
    image.save(output, format="JPEG", quality=DOC_IMAGE_JPEG_QUALITY, optimize=True)
    return ProcessedDocImage(content=output.getvalue(), width=image.width, height=image.height, file_name=name)


def doc_image_storage_path(company_id: str, estimate_oid: str, image_id: str) -> str:
    return f"estimate-doc-images/{company_id}/{estimate_oid}/{image_id}.jpg"


def _bucket() -> Any:
    if storage is None:
        raise RuntimeError("firebase-admin storage support is not installed")
    initialize_firebase_admin()
    return storage.bucket(_normalized_bucket_name())


def store_doc_image(storage_path: str, content: bytes) -> None:
    blob = _bucket().blob(storage_path)
    blob.cache_control = "private, max-age=0"
    blob.upload_from_string(content, content_type="image/jpeg")


def signed_doc_image_url(storage_path: str) -> str:
    """A URL Google can fetch for the next ten minutes, and nobody after."""
    return _bucket().blob(storage_path).generate_signed_url(
        version="v4", expiration=SIGNED_URL_TTL, method="GET"
    )


def read_doc_image(storage_path: str) -> bytes:
    return _bucket().blob(storage_path).download_as_bytes()


def delete_doc_images(storage_paths: Iterable[str]) -> None:
    """Best-effort: a blob that fails to delete is logged and left behind."""
    paths = [path for path in storage_paths if path]
    if not paths:
        return
    if storage is None:
        logger.warning("firebase-admin storage unavailable; skipping delete of %d doc images", len(paths))
        return
    bucket = _bucket()
    for path in paths:
        try:
            bucket.blob(path).delete()
        except Exception:
            logger.warning("Failed to delete estimate doc image blob %s", path, exc_info=True)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_estimate_doc_images.py -q`
Expected: all pass. If the `WEBP` case fails with `KeyError: 'WEBP'`, the local Pillow was built without WebP. Check with `python -c "from PIL import features; print(features.check('webp'))"` and tell Simon before changing the allowlist.

- [ ] **Step 6: Run the gates**

Run: `cd platform && ./run_mypy.sh services/estimate_doc_images.py models/estimate.py && ./run_ruff.sh services/estimate_doc_images.py models/estimate.py tests/test_estimate_doc_images.py`
Expected: `Success: no issues found` and `All checks passed!`

- [ ] **Step 7: Commit (platform repo, after approval)**

```bash
git -C platform add models/estimate.py services/estimate_doc_images.py tests/test_estimate_doc_images.py
git -C platform commit -m "feat: process and store images for generated estimate docs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 2: `{{NOTES}}` from Additional Information; delete the dead DocBuilder path (platform)

**Files:**
- Modify: `platform/services/estimate_doc_generator.py`. Change `prepare_template_data` (around line 185). Delete `class DocBuilder` (around lines 66–168) and `EstimateDocumentGenerator.generate_doc_content` (around lines 285–end).
- Modify: `platform/services/google_drive_service.py`. Delete `create_estimate_document` (starts around line 245). Its only feeder was `generate_doc_content`.
- Modify: `platform/routers/estimate_helpers/doc_versions.py`. `prepare_doc_template` gains `additional_info`.
- Test: `platform/tests/test_estimate_doc_generator.py`, `platform/tests/test_google_drive_service.py`

**Interfaces:**
- Produces:
  - `EstimateDocumentGenerator.prepare_template_data(estimate, company, property_info=None, contacts=None, additional_info: str = "")`
  - `doc_versions.prepare_doc_template(estimate, company, property_info, contacts, additional_info: str = "")`

- [ ] **Step 1: Confirm the dead code really is dead**

Run: `cd platform && grep -rn "generate_doc_content\|DocBuilder\|create_estimate_document\b" --include='*.py' agents routers services scripts main.py`
Expected: matches only inside `services/estimate_doc_generator.py` and `services/google_drive_service.py` (the definitions and `DocBuilder()` inside `generate_doc_content`). If anything else matches, stop and report it.

- [ ] **Step 2: Update and add the failing tests**

In `platform/tests/test_estimate_doc_generator.py`, `test_prepare_template_data`:
- Change `estimate.notes = "Test notes"` to `estimate.notes = "Legacy estimate notes"`.
- Pass `additional_info="Side gate code 4321"` to `prepare_template_data`.
- Change the assertion to `assert replacements["{{NOTES}}"] == "Side gate code 4321"`.

In `test_prepare_template_data_with_empty_fields`, change the NOTES assertion to `assert replacements["{{NOTES}}"] == "--"`.

Delete `test_generate_doc_content_full`, `test_generate_doc_content_not_blank` and `test_generate_doc_content_minimal`. In `tests/test_google_drive_service.py`, delete `test_generate_doc_content_structure` and `test_create_estimate_document`.

Append:

```python
def _minimal_generator_inputs():
    from unittest.mock import MagicMock

    company = MagicMock()
    company.name = "Test Co"
    company.email = None
    company.phone = None
    company.street = company.city = company.prov_state = company.postal_zip = company.country = None
    estimate = MagicMock()
    estimate.estimate_id = "E0001"
    estimate.title = "T"
    estimate.description = None
    estimate.created_at = datetime(2026, 9, 23)
    estimate.job_items = []
    estimate.grand_total = 0.0
    estimate.notes = "Legacy estimate notes"
    return estimate, company


def test_notes_ignores_legacy_estimate_notes():
    estimate, company = _minimal_generator_inputs()
    replacements, _ = EstimateDocumentGenerator().prepare_template_data(estimate, company)
    assert replacements["{{NOTES}}"] == "--"


def test_whitespace_only_additional_info_prints_dashes():
    """Review Focus #2."""
    estimate, company = _minimal_generator_inputs()
    replacements, _ = EstimateDocumentGenerator().prepare_template_data(
        estimate, company, additional_info="  \n\t \n"
    )
    assert replacements["{{NOTES}}"] == "--"


def test_multiline_additional_info_is_kept():
    estimate, company = _minimal_generator_inputs()
    replacements, _ = EstimateDocumentGenerator().prepare_template_data(
        estimate, company, additional_info="Line one\nLine two\n"
    )
    assert replacements["{{NOTES}}"] == "Line one\nLine two"
```

(Check the top of the file imports `datetime` and `EstimateDocumentGenerator`; the existing tests already use both.)

- [ ] **Step 3: Run the tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_estimate_doc_generator.py -q`
Expected: FAIL. `prepare_template_data() got an unexpected keyword argument 'additional_info'`, and `test_notes_ignores_legacy_estimate_notes` asserts `'Legacy estimate notes' == '--'`.

- [ ] **Step 4: Implement**

In `prepare_template_data`, add `additional_info: str = ""` as the last parameter and replace the NOTES line:

```python
            # From the Documents dialog's Additional Information. Estimate.notes
            # is deliberately NOT read (decided 2026-09-23): blank prints "--".
            '{{NOTES}}': additional_info.strip() or "--",
```

Delete `class DocBuilder` in full, `generate_doc_content` in full, and `GoogleDriveService.create_estimate_document` in full. Then remove any imports that ruff reports as unused in those two files.

In `doc_versions.prepare_doc_template`, add `additional_info: str = ""` after `contacts` and pass `additional_info=additional_info` through to `prepare_template_data`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_estimate_doc_generator.py tests/test_google_drive_service.py -q`
Expected: all pass.

- [ ] **Step 6: Run the gates**

Run: `cd platform && ./run_mypy.sh services routers/estimate_helpers && ./run_ruff.sh services routers/estimate_helpers tests/test_estimate_doc_generator.py tests/test_google_drive_service.py`
Expected: clean.

- [ ] **Step 7: Commit (platform, after approval)**

```bash
git -C platform add services/estimate_doc_generator.py services/google_drive_service.py routers/estimate_helpers/doc_versions.py tests/test_estimate_doc_generator.py tests/test_google_drive_service.py
git -C platform commit -m "feat: fill the doc NOTES section from additional info, not Estimate.notes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 3: Insert images after NOTES in the Google Doc (platform)

**Files:**
- Modify: `platform/services/google_drive_service.py` (`create_estimate_from_template` around line 461, plus new module-level helpers and private methods)
- Test: `platform/tests/test_google_drive_service.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `NOTES_IMAGES_MARKER = "{{NOTES_IMAGES}}"`
  - `class DocImageInsertError(Exception)`
  - `GoogleDriveService.create_estimate_from_template(file_name, folder_id, replacements, work_items, logo_url=None, images: Optional[List[Dict[str, Any]]] = None)`. Each image dict is `{"uri": str, "width": int, "height": int}`. When images fail to insert, it trashes the doc and raises `DocImageInsertError`.

- [ ] **Step 1: Write the failing tests**

Append to `platform/tests/test_google_drive_service.py`:

```python
from services.google_drive_service import NOTES_IMAGES_MARKER, DocImageInsertError


def _docs_service_for(doc):
    service = GoogleDriveService()
    service._initialized = True
    service._drive_service = MagicMock()
    docs = MagicMock()
    docs.get.return_value.execute.return_value = doc
    service._docs_service = MagicMock()
    service._docs_service.documents.return_value = docs
    return service, docs


def _paragraph(start, text):
    end = start + len(text.encode("utf-16-le")) // 2
    return {
        "startIndex": start,
        "endIndex": end,
        "paragraph": {"elements": [{"startIndex": start, "endIndex": end, "textRun": {"content": text}}]},
    }


def _sent_requests(docs):
    return docs.batchUpdate.call_args.kwargs["body"]["requests"]


def test_insert_images_replaces_marker_in_display_order():
    doc = {"body": {"content": [
        _paragraph(1, "Gate code 4321\n"),
        _paragraph(16, NOTES_IMAGES_MARKER + "\n"),
        _paragraph(33, "Footer\n"),
    ]}}
    service, docs = _docs_service_for(doc)
    service._insert_images_after_marker("doc1", [
        {"uri": "u1", "width": 800, "height": 600},
        {"uri": "u2", "width": 400, "height": 400},
    ])
    reqs = _sent_requests(docs)
    assert reqs[0] == {"deleteContentRange": {"range": {"startIndex": 16, "endIndex": 32}}}
    assert [next(iter(r)) for r in reqs[1:]] == ["insertInlineImage", "insertText", "insertInlineImage"]
    # Inserted in reverse at one index, so u1 ends up first in the document.
    assert reqs[1]["insertInlineImage"]["uri"] == "u2"
    assert reqs[3]["insertInlineImage"]["uri"] == "u1"
    assert all(next(iter(r.values()))["location"]["index"] == 16 for r in reqs[1:])


def test_image_width_is_clamped_to_text_width_keeping_aspect():
    doc = {"body": {"content": [_paragraph(1, NOTES_IMAGES_MARKER + "\n")]}}
    service, docs = _docs_service_for(doc)
    service._insert_images_after_marker("doc1", [{"uri": "u", "width": 2000, "height": 1000}])
    size = _sent_requests(docs)[1]["insertInlineImage"]["objectSize"]
    assert size == {"width": {"magnitude": 468.0, "unit": "PT"}, "height": {"magnitude": 234.0, "unit": "PT"}}


def test_small_image_keeps_natural_size():
    doc = {"body": {"content": [_paragraph(1, NOTES_IMAGES_MARKER + "\n")]}}
    service, docs = _docs_service_for(doc)
    service._insert_images_after_marker("doc1", [{"uri": "u", "width": 400, "height": 300}])
    size = _sent_requests(docs)[1]["insertInlineImage"]["objectSize"]
    assert size == {"width": {"magnitude": 300.0, "unit": "PT"}, "height": {"magnitude": 225.0, "unit": "PT"}}


def test_marker_is_found_inside_a_table_cell():
    cell_paragraph = _paragraph(40, NOTES_IMAGES_MARKER + "\n")
    doc = {"body": {"content": [
        _paragraph(1, "Intro\n"),
        {"startIndex": 38, "endIndex": 60, "table": {"tableRows": [{"tableCells": [{"content": [cell_paragraph]}]}]}},
    ]}}
    service, docs = _docs_service_for(doc)
    service._insert_images_after_marker("doc1", [{"uri": "u", "width": 100, "height": 100}])
    assert _sent_requests(docs)[0]["deleteContentRange"]["range"]["startIndex"] == 40


def test_marker_index_counts_utf16_code_units():
    # The camera emoji is one Python char but two UTF-16 units; Docs counts units.
    doc = {"body": {"content": [_paragraph(1, "📷 " + NOTES_IMAGES_MARKER + "\n")]}}
    service, docs = _docs_service_for(doc)
    service._insert_images_after_marker("doc1", [{"uri": "u", "width": 100, "height": 100}])
    assert _sent_requests(docs)[0]["deleteContentRange"]["range"]["startIndex"] == 4


def test_missing_marker_appends_images_at_end_of_body():
    doc = {"body": {"content": [_paragraph(1, "Hello\n")]}}  # endIndex 7
    service, docs = _docs_service_for(doc)
    service._insert_images_after_marker("doc1", [{"uri": "u", "width": 100, "height": 100}])
    reqs = _sent_requests(docs)
    assert "deleteContentRange" not in reqs[0]
    assert reqs[0]["insertInlineImage"]["location"]["index"] == 6
    assert reqs[-1] == {"insertText": {"location": {"index": 6}, "text": "\n"}}


def _template_service():
    service = GoogleDriveService()
    service._initialized = True
    service._drive_service = MagicMock()
    service._drive_service.files.return_value.copy.return_value.execute.return_value = {
        "id": "new_doc_123", "webViewLink": "http://example.com/new_doc_123",
    }
    service._docs_service = MagicMock()
    service._find_estimate_template = MagicMock(return_value="template_123")
    service.share_document = MagicMock()
    service._insert_images_after_marker = MagicMock()
    return service


def _replace_text_for(service, placeholder):
    body = service._docs_service.documents.return_value.batchUpdate.call_args_list[0].kwargs["body"]
    for request in body["requests"]:
        if request["replaceAllText"]["containsText"]["text"] == placeholder:
            return request["replaceAllText"]["replaceText"]
    raise AssertionError(f"{placeholder} was not replaced")


def test_template_notes_replacement_carries_marker_when_images_present(mock_settings, mock_google_api):
    service = _template_service()
    images = [{"uri": "u", "width": 10, "height": 10}]
    service.create_estimate_from_template("F", "folder", {"{{NOTES}}": "Gate"}, [], images=images)
    assert _replace_text_for(service, "{{NOTES}}") == f"Gate\n{NOTES_IMAGES_MARKER}"
    service._insert_images_after_marker.assert_called_once_with("new_doc_123", images)


def test_template_without_images_leaves_notes_untouched(mock_settings, mock_google_api):
    service = _template_service()
    service.create_estimate_from_template("F", "folder", {"{{NOTES}}": "Gate"}, [])
    assert _replace_text_for(service, "{{NOTES}}") == "Gate"
    service._insert_images_after_marker.assert_not_called()


def test_image_insert_failure_trashes_doc_and_raises(mock_settings, mock_google_api):
    service = _template_service()
    service._insert_images_after_marker = MagicMock(side_effect=RuntimeError("Google could not fetch the image"))
    service.trash_document = MagicMock(return_value=True)
    with pytest.raises(DocImageInsertError):
        service.create_estimate_from_template(
            "F", "folder", {"{{NOTES}}": "Gate"}, [], images=[{"uri": "u", "width": 10, "height": 10}]
        )
    service.trash_document.assert_called_once_with("new_doc_123")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_google_drive_service.py -q`
Expected: collection error, `ImportError: cannot import name 'NOTES_IMAGES_MARKER'`.

- [ ] **Step 3: Implement**

In `platform/services/google_drive_service.py`, add at module level after `logger`:

```python
# Left by the {{NOTES}} replacement on its own paragraph when a doc has images,
# then swapped for the images themselves. replaceAllText returns no positions,
# so this is how the images find "right after the notes".
NOTES_IMAGES_MARKER = "{{NOTES_IMAGES}}"
DOC_TEXT_WIDTH_PT = 468.0  # 6.5" — a Letter page's text width with 1" margins
PX_TO_PT = 0.75


class DocImageInsertError(Exception):
    """Images could not be placed; the half-built doc has already been trashed."""


def _image_object_size(width_px: int, height_px: int) -> Dict[str, Any]:
    width_pt = min(DOC_TEXT_WIDTH_PT, width_px * PX_TO_PT)
    height_pt = width_pt * height_px / width_px
    return {
        'width': {'magnitude': round(width_pt, 2), 'unit': 'PT'},
        'height': {'magnitude': round(height_pt, 2), 'unit': 'PT'},
    }
```

In `create_estimate_from_template`:
- Add the parameter `images: Optional[List[Dict[str, Any]]] = None` after `logo_url`, and document it in the docstring as `{"uri", "width", "height"}` dicts placed after NOTES, with fail-closed behavior.
- In the text-replacement loop, replace the dict literal so that NOTES carries the marker:

```python
            if placeholder not in ['{{WORK_ITEM_DESCRIPTIONS}}', '{{WORK_ITEM_AMOUNTS}}']:
                replace_text = value
                if placeholder == '{{NOTES}}' and images:
                    replace_text = f"{value}\n{NOTES_IMAGES_MARKER}"
                requests.append({
                    'replaceAllText': {
                        'containsText': {'text': placeholder, 'matchCase': True},
                        'replaceText': replace_text
                    }
                })
```

- After the work-items block and before `# Share document`, add:

```python
        # Images go last so the work-item row inserts above can't shift their
        # indexes. Fail-closed, unlike the logo: the user attached these on
        # purpose, and a doc silently missing them is the worse outcome.
        if images:
            try:
                self._insert_images_after_marker(doc_id, images)
            except Exception as err:
                logger.error(f"Failed to insert {len(images)} images into {doc_id}: {err}")
                try:
                    self.trash_document(doc_id)
                except Exception:
                    logger.warning(f"Failed to trash half-built document {doc_id}", exc_info=True)
                raise DocImageInsertError(str(err)) from err
```

Add the private methods next to `_replace_first_image`:

```python
    def _find_text_start(self, content: List[Dict[str, Any]], text: str) -> Optional[int]:
        """Document index where `text` begins, searching paragraphs and table
        cells. Docs indexes count UTF-16 code units, not Python characters."""
        for element in content:
            paragraph = element.get('paragraph')
            if paragraph:
                for run in paragraph.get('elements', []):
                    run_text = run.get('textRun', {}).get('content', '')
                    offset = run_text.find(text)
                    if offset != -1:
                        return run['startIndex'] + len(run_text[:offset].encode('utf-16-le')) // 2
            table = element.get('table')
            if table:
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        found = self._find_text_start(cell.get('content', []), text)
                        if found is not None:
                            return found
        return None

    def _insert_images_after_marker(self, doc_id: str, images: List[Dict[str, Any]]) -> None:
        """Swap NOTES_IMAGES_MARKER for the images, one per paragraph, in order.

        Every insert lands at the same index, so they are issued in REVERSE —
        each pushes the previous one down. With no marker (a template without
        {{NOTES}}) the images are appended rather than dropped.
        """
        doc = self._docs_service.documents().get(documentId=doc_id).execute()
        content = doc.get('body', {}).get('content', [])
        marker_start = self._find_text_start(content, NOTES_IMAGES_MARKER)

        requests: List[Dict[str, Any]] = []
        if marker_start is not None:
            insert_at = marker_start
            requests.append({'deleteContentRange': {'range': {
                'startIndex': marker_start,
                'endIndex': marker_start + len(NOTES_IMAGES_MARKER),
            }}})
        else:
            logger.warning(f"No {NOTES_IMAGES_MARKER} marker in document {doc_id}; appending images at the end")
            insert_at = content[-1]['endIndex'] - 1

        for position, image in enumerate(reversed(images)):
            if position > 0:
                requests.append({'insertText': {'location': {'index': insert_at}, 'text': '\n'}})
            requests.append({'insertInlineImage': {
                'location': {'index': insert_at},
                'uri': image['uri'],
                'objectSize': _image_object_size(image['width'], image['height']),
            }})
        if marker_start is None:
            requests.append({'insertText': {'location': {'index': insert_at}, 'text': '\n'}})

        self._docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        logger.info(f"Inserted {len(images)} images into document {doc_id}")
```

(Check that `Any` and `Optional` are imported from `typing` at the top of the file. `Dict` and `List` already are.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_google_drive_service.py -q`
Expected: all pass.

- [ ] **Step 5: Run the gates**

Run: `cd platform && ./run_mypy.sh services/google_drive_service.py && ./run_ruff.sh services/google_drive_service.py tests/test_google_drive_service.py && ./run_bandit.sh services/google_drive_service.py`
Expected: mypy and ruff are clean, and bandit adds no new finding (the nested `except Exception` logs, so it isn't a B110).

- [ ] **Step 6: Commit (platform, after approval)**

```bash
git -C platform add services/google_drive_service.py tests/test_google_drive_service.py
git -C platform commit -m "feat: place images after the NOTES section of generated estimate docs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 4: Doc-version image helpers and cleanup (platform)

**Files:**
- Modify: `platform/routers/estimate_helpers/doc_versions.py`
- Test: `platform/tests/test_estimate_doc_version_images.py` (new)

**Interfaces:**
- Consumes: Task 1 (`DocImage`, `doc_images.*`, `ProcessedDocImage`) and Task 3 (`DocImageInsertError`).
- Produces (all in `routers.estimate_helpers.doc_versions`):
  - `DOC_IMAGES_FAILED_DETAIL = "Couldn't add images to the document. Please try again."`
  - `find_doc_image(estimate: Estimate, image_id: str) -> Optional[DocImage]`
  - `resolve_kept_images(estimate: Estimate, image_ids: List[str]) -> List[DocImage]`: 400 on an unknown id; duplicates collapse to the first occurrence.
  - `async read_doc_image_uploads(files: List[UploadFile]) -> List[ProcessedDocImage]`
  - `async stage_doc_images(company_id: str, estimate_oid: str, uploads: List[ProcessedDocImage]) -> List[DocImage]`: on failure, removes what it stored and raises 502.
  - `async build_doc_image_inserts(images: List[DocImage]) -> List[Dict[str, Any]]`: raises 502 on a signing failure.
  - `async discard_doc_image_paths(paths: List[str]) -> None`: never raises.
  - `image_paths_only_in(version: GoogleDocsVersion, remaining: List[GoogleDocsVersion]) -> List[str]`
  - `create_doc_from_template(..., images: Optional[List[Dict[str, Any]]] = None)`: `DocImageInsertError` → 502.
  - `cleanup_estimate_external_resources` also deletes every image blob of every version, even when Drive is disabled.

- [ ] **Step 1: Write the failing tests**

`platform/tests/test_estimate_doc_version_images.py`:

```python
"""Doc-version image helpers: carry-forward resolution, staging, cleanup."""

import asyncio
from unittest.mock import MagicMock

import pytest
from beanie import PydanticObjectId
from fastapi import HTTPException

from models.estimate import DocImage, Estimate, EstimateStatus, GoogleDocsVersion
from routers.estimate_helpers import doc_versions
from services import estimate_doc_images as doc_images
from services.estimate_doc_images import ProcessedDocImage
from services.google_drive_service import DocImageInsertError


def _image(image_id: str) -> DocImage:
    return DocImage(id=image_id, storage_path=f"estimate-doc-images/c/e/{image_id}.jpg",
                    file_name=f"{image_id}.jpg", width=800, height=600)


def _version(number: int, images: list[DocImage]) -> GoogleDocsVersion:
    return GoogleDocsVersion(version=number, doc_id=f"d{number}", doc_url=f"u{number}",
                             drive_file_id=f"f{number}", file_name=f"V{number}", created_by="t", images=images)


def _estimate(versions: list[GoogleDocsVersion]) -> Estimate:
    return Estimate(estimate_id="E0001", company=PydanticObjectId(), title="T", status=EstimateStatus.DRAFT,
                    created_by="t", google_docs_versions=versions)


def test_resolve_kept_images_keeps_order_and_collapses_duplicates():
    a, b = _image("a"), _image("b")
    estimate = _estimate([_version(1, [a]), _version(2, [a, b])])
    kept = doc_versions.resolve_kept_images(estimate, ["b", "a", "b"])
    assert [i.id for i in kept] == ["b", "a"]


def test_resolve_kept_images_rejects_unknown_ids():
    estimate = _estimate([_version(1, [_image("a")])])
    with pytest.raises(HTTPException) as exc:
        doc_versions.resolve_kept_images(estimate, ["not-mine"])
    assert exc.value.status_code == 400


def test_image_paths_only_in_spares_shared_blobs():
    a, b = _image("a"), _image("b")
    deleted = _version(1, [a, b])
    remaining = [_version(2, [a])]
    assert doc_versions.image_paths_only_in(deleted, remaining) == [b.storage_path]


def test_stage_doc_images_removes_partial_uploads_on_failure(monkeypatch):
    stored: list[str] = []
    discarded: list[list[str]] = []

    def _store(path, content):
        if stored:
            raise RuntimeError("storage down")
        stored.append(path)

    monkeypatch.setattr(doc_images, "store_doc_image", _store)
    monkeypatch.setattr(doc_images, "delete_doc_images", lambda paths: discarded.append(list(paths)))
    uploads = [ProcessedDocImage(b"1", 10, 10, "one.jpg"), ProcessedDocImage(b"2", 10, 10, "two.jpg")]

    with pytest.raises(HTTPException) as exc:
        asyncio.run(doc_versions.stage_doc_images("c", "e", uploads))
    assert exc.value.status_code == 502
    assert exc.value.detail == doc_versions.DOC_IMAGES_FAILED_DETAIL
    assert discarded == [stored]


def test_stage_doc_images_returns_doc_images(monkeypatch):
    monkeypatch.setattr(doc_images, "store_doc_image", lambda path, content: None)
    staged = asyncio.run(doc_versions.stage_doc_images("c1", "e1", [ProcessedDocImage(b"1", 30, 20, "g.jpg")]))
    assert len(staged) == 1
    assert staged[0].storage_path == f"estimate-doc-images/c1/e1/{staged[0].id}.jpg"
    assert (staged[0].file_name, staged[0].width, staged[0].height) == ("g.jpg", 30, 20)


def test_build_doc_image_inserts_signs_each_image(monkeypatch):
    monkeypatch.setattr(doc_images, "signed_doc_image_url", lambda path: f"https://signed/{path}")
    inserts = asyncio.run(doc_versions.build_doc_image_inserts([_image("a")]))
    assert inserts == [{"uri": "https://signed/estimate-doc-images/c/e/a.jpg", "width": 800, "height": 600}]


def test_build_doc_image_inserts_maps_signing_failure_to_502(monkeypatch):
    def _boom(path):
        raise RuntimeError("no signing key")

    monkeypatch.setattr(doc_images, "signed_doc_image_url", _boom)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(doc_versions.build_doc_image_inserts([_image("a")]))
    assert exc.value.status_code == 502


def test_create_doc_from_template_maps_image_failure_to_502():
    drive = MagicMock()
    drive.create_estimate_from_template.side_effect = DocImageInsertError("fetch failed")
    estimate, company = MagicMock(estimate_id="E0001"), MagicMock(logo_url=None)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(doc_versions.create_doc_from_template(
            drive, estimate=estimate, company=company, file_name="F", folder_id="f",
            replacements={}, work_items=[], images=[{"uri": "u", "width": 1, "height": 1}],
        ))
    assert exc.value.status_code == 502
    assert exc.value.detail == doc_versions.DOC_IMAGES_FAILED_DETAIL
    assert drive.create_estimate_from_template.call_args.kwargs["images"] == [{"uri": "u", "width": 1, "height": 1}]


def test_estimate_cleanup_deletes_every_image_even_with_drive_disabled(monkeypatch):
    a, b = _image("a"), _image("b")
    deleted: list[list[str]] = []
    drive = MagicMock()
    drive.is_enabled.return_value = False
    monkeypatch.setattr(doc_versions, "get_google_drive_service", lambda: drive)
    monkeypatch.setattr(doc_images, "delete_doc_images", lambda paths: deleted.append(sorted(paths)))
    asyncio.run(doc_versions.cleanup_estimate_external_resources([_version(1, [a]), _version(2, [a, b])], None, "E0001"))
    assert deleted == [sorted([a.storage_path, b.storage_path])]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_estimate_doc_version_images.py -q`
Expected: FAIL with `AttributeError: module 'routers.estimate_helpers.doc_versions' has no attribute 'resolve_kept_images'` (and similar for the other new names).

- [ ] **Step 3: Implement**

In `platform/routers/estimate_helpers/doc_versions.py`, update the imports:

```python
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from models.estimate import DocImage, GoogleDocsVersion
from services import estimate_doc_images as doc_images
from services.estimate_doc_images import ProcessedDocImage
from services.google_drive_service import DocImageInsertError, get_google_drive_service
```

Add below `logger`:

```python
DOC_IMAGES_FAILED_DETAIL = "Couldn't add images to the document. Please try again."
```

At the top of the `try:` in `cleanup_estimate_external_resources`, before the Drive block:

```python
        # Image blobs live in Firebase Storage, not Drive, so they are cleaned
        # up whether or not the Drive integration is enabled.
        image_paths = sorted({image.storage_path for version in versions for image in version.images})
        if image_paths:
            await run_in_threadpool(doc_images.delete_doc_images, image_paths)
```

In `create_doc_from_template`, add the parameter `images: Optional[List[Dict[str, Any]]] = None`, pass `images=images` into the `run_in_threadpool` call, and insert this before the existing `except Exception:`:

```python
    except DocImageInsertError:
        logger.warning("Images could not be placed in the document for estimate %s", estimate.estimate_id)
        raise HTTPException(status_code=502, detail=DOC_IMAGES_FAILED_DETAIL) from None
```

Append the helpers:

```python
def find_doc_image(estimate: Estimate, image_id: str) -> Optional[DocImage]:
    for version in estimate.google_docs_versions:
        for image in version.images:
            if image.id == image_id:
                return image
    return None


def resolve_kept_images(estimate: Estimate, image_ids: List[str]) -> List[DocImage]:
    """Images from earlier versions to carry into the next one.

    Resolved ONLY against this estimate's own versions: the client names an
    id, never a storage path, so it cannot pull in another estimate's blob.
    A repeated id collapses to its first occurrence.
    """
    kept: List[DocImage] = []
    seen: set[str] = set()
    for image_id in image_ids:
        if image_id in seen:
            continue
        seen.add(image_id)
        image = find_doc_image(estimate, image_id)
        if image is None:
            raise HTTPException(
                status_code=400,
                detail="One of the images to keep no longer exists. Reopen Documents and try again.",
            )
        kept.append(image)
    return kept


async def read_doc_image_uploads(files: List[UploadFile]) -> List[ProcessedDocImage]:
    """Validate and process every upload before anything is stored."""
    processed: List[ProcessedDocImage] = []
    for upload in files:
        content = await upload.read()
        processed.append(await run_in_threadpool(
            doc_images.process_doc_image_upload, content, upload.content_type or "", upload.filename,
        ))
    return processed


async def discard_doc_image_paths(paths: List[str]) -> None:
    """Best-effort blob removal; never fails the request it runs in."""
    if not paths:
        return
    try:
        await run_in_threadpool(doc_images.delete_doc_images, paths)
    except Exception:
        logger.warning("Failed to discard %d estimate doc images", len(paths), exc_info=True)


async def stage_doc_images(
    company_id: str,
    estimate_oid: str,
    uploads: List[ProcessedDocImage],
) -> List[DocImage]:
    """Store new uploads. A partial failure removes what it stored, then 502s."""
    staged: List[DocImage] = []
    try:
        for upload in uploads:
            image_id = uuid4().hex
            path = doc_images.doc_image_storage_path(company_id, estimate_oid, image_id)
            await run_in_threadpool(doc_images.store_doc_image, path, upload.content)
            staged.append(DocImage(
                id=image_id, storage_path=path, file_name=upload.file_name,
                width=upload.width, height=upload.height,
            ))
    except Exception:
        logger.warning("Failed to store estimate doc images for estimate %s", estimate_oid, exc_info=True)
        await discard_doc_image_paths([image.storage_path for image in staged])
        raise HTTPException(status_code=502, detail=DOC_IMAGES_FAILED_DETAIL) from None
    return staged


async def build_doc_image_inserts(images: List[DocImage]) -> List[Dict[str, Any]]:
    """Short-lived signed URLs Google fetches while it builds the doc."""
    try:
        return [
            {
                "uri": await run_in_threadpool(doc_images.signed_doc_image_url, image.storage_path),
                "width": image.width,
                "height": image.height,
            }
            for image in images
        ]
    except Exception:
        logger.warning("Failed to sign estimate doc image URLs", exc_info=True)
        raise HTTPException(status_code=502, detail=DOC_IMAGES_FAILED_DETAIL) from None


def image_paths_only_in(version: GoogleDocsVersion, remaining: List[GoogleDocsVersion]) -> List[str]:
    """Blobs the deleted version owned alone — a carried-forward image stays."""
    still_used = {image.storage_path for other in remaining for image in other.images}
    return [image.storage_path for image in version.images if image.storage_path not in still_used]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_estimate_doc_version_images.py tests/test_generate_google_doc_router.py tests/test_estimate_docs_api.py -q`
Expected: the new file passes. The two existing files still pass, because `create_doc_from_template` only gained an optional parameter.

- [ ] **Step 5: Run the gates**

Run: `cd platform && ./run_mypy.sh routers/estimate_helpers && ./run_ruff.sh routers/estimate_helpers tests/test_estimate_doc_version_images.py`
Expected: clean.

- [ ] **Step 6: Commit (platform, after approval)**

```bash
git -C platform add routers/estimate_helpers/doc_versions.py tests/test_estimate_doc_version_images.py
git -C platform commit -m "feat: stage, carry forward, and clean up estimate doc images

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 5: `routers/estimate_documents.py` — multipart generate, image read, reference-checked delete (platform)

**Files:**
- Create: `platform/routers/estimate_documents.py`
- Modify: `platform/routers/estimates.py`. Delete `class GenerateDocRequest`, `generate_google_doc`, `get_docs_versions` and `delete_docs_version` (currently around lines 1693–1801). Trim the `doc_versions` import block (lines ~1431–1444) down to `cleanup_estimate_external_resources`.
- Modify: `platform/routers/__init__.py` and `platform/main.py` (register the router)
- Modify: `platform/tests/test_generate_google_doc_router.py` (retarget the patches)
- Test: `platform/tests/test_estimate_documents_api.py` (new)

**Interfaces:**
- Consumes: Task 2 (`prepare_doc_template(..., additional_info=)`), Task 4 (every helper listed there) and Task 1 (`doc_images.MAX_DOC_IMAGES`, `doc_images.read_doc_image`).
- Produces the HTTP contract the portal (Tasks 6–8) uses:
  - `POST /estimates/{id}/generate-doc`, multipart with the fields `created_by`, `additional_info`, repeated `keep_image_ids` and repeated `files`. Returns the `Estimate`, with `google_docs_versions` sorted newest first and each version carrying `additional_info` and `images[] {id, storage_path, file_name, width, height}`.
  - `GET /estimates/{id}/doc-images/{image_id}` returns `image/jpeg` bytes, or 404.
  - `GET /estimates/{id}/docs-versions` and `DELETE /estimates/{id}/docs-versions/{version}` are unchanged, except that delete now also removes the version's unshared image blobs.

- [ ] **Step 1: Write the failing API tests**

`platform/tests/test_estimate_documents_api.py`:

```python
"""POST generate-doc (multipart), GET doc-images, DELETE docs-versions with images.

Drive and Firebase Storage are faked; the estimate itself is real (local Mongo)
so what the version row persists is what gets asserted.
"""

import io
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

import routers.estimate_documents as docs_router
from services import estimate_doc_images as doc_images
from tests.helpers import onboard_owner, unique_email


def _jpeg(size=(800, 600)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (120, 160, 90)).save(buf, format="JPEG")
    return buf.getvalue()


def _png(size=(400, 400)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (20, 40, 60)).save(buf, format="PNG")
    return buf.getvalue()


class _Store:
    def __init__(self):
        self.blobs: dict[str, bytes] = {}
        self.deleted: list[str] = []


@pytest.fixture
def fake_store(monkeypatch):
    store = _Store()

    def _delete(paths):
        for path in paths:
            store.deleted.append(path)
            store.blobs.pop(path, None)

    def _read(path):
        if path not in store.blobs:
            raise FileNotFoundError(path)
        return store.blobs[path]

    monkeypatch.setattr(doc_images, "store_doc_image", lambda path, content: store.blobs.__setitem__(path, content))
    monkeypatch.setattr(doc_images, "delete_doc_images", _delete)
    monkeypatch.setattr(doc_images, "signed_doc_image_url", lambda path: f"https://signed.example/{path}")
    monkeypatch.setattr(doc_images, "read_doc_image", _read)
    return store


@pytest.fixture
def fake_drive(monkeypatch):
    drive = MagicMock()
    drive.trash_document.return_value = True
    drive.create_calls = []

    async def _folder(drive_service, company):
        return "year-folder"

    async def _create(drive_service, **kwargs):
        drive.create_calls.append(kwargs)
        n = len(drive.create_calls)
        return {"doc_id": f"doc-{n}", "doc_url": f"https://docs.google.com/d/doc-{n}", "drive_file_id": f"drive-{n}"}

    monkeypatch.setattr(docs_router, "require_drive_service", lambda: drive)
    monkeypatch.setattr(docs_router, "get_or_create_doc_folder", _folder)
    monkeypatch.setattr(docs_router, "create_doc_from_template", _create)
    return drive


def _new_estimate(client: TestClient, company_id: str) -> tuple[str, str]:
    prop = client.post("/properties/", json={
        "street": "7 Doc St", "city": "Kelowna", "prov_state": "BC", "country": "Canada",
        "contacts": [], "company": company_id,
    })
    assert prop.status_code == 200, prop.text
    est = client.post("/estimates/", json={
        "company": company_id, "title": "Documents dialog", "property": prop.json()["_id"],
        "created_by": "docs@example.com", "skip_generation": True, "job_items": [],
    })
    assert est.status_code == 200, est.text
    return est.json()["_id"], prop.json()["_id"]


@pytest.fixture
def estimate_id(client: TestClient, test_company_id: str, fake_store, fake_drive):
    # Depends on the fakes so it is torn down FIRST — the estimate-delete
    # cascade must still see the fake store.
    eid, prop = _new_estimate(client, test_company_id)
    yield eid
    client.delete(f"/estimates/{eid}")
    client.delete(f"/properties/{prop}")


def _generate(client: TestClient, eid: str, *, info: str = "", keep=(), files=()):
    data: dict = {"created_by": "Docs Tester", "additional_info": info}
    if keep:
        data["keep_image_ids"] = list(keep)
    multipart = [("files", (name, content, ctype)) for name, content, ctype in files]
    return client.post(f"/estimates/{eid}/generate-doc", data=data, files=multipart or None)


def _latest(response) -> dict:
    return response.json()["google_docs_versions"][0]


def test_generate_records_additional_info_and_images(client, test_company_id, estimate_id, fake_store, fake_drive):
    r = _generate(client, estimate_id, info="  Side gate code 4321\n",
                  files=[("gate.jpg", _jpeg(), "image/jpeg"), ("bed.png", _png(), "image/png")])
    assert r.status_code == 200, r.text
    version = _latest(r)
    assert version["additional_info"] == "Side gate code 4321"
    assert [i["file_name"] for i in version["images"]] == ["gate.jpg", "bed.png"]
    for image in version["images"]:
        assert image["storage_path"].startswith(f"estimate-doc-images/{test_company_id}/{estimate_id}/")
        assert image["storage_path"] in fake_store.blobs

    call = fake_drive.create_calls[0]
    assert call["replacements"]["{{NOTES}}"] == "Side gate code 4321"
    assert call["images"] == [
        {"uri": f"https://signed.example/{i['storage_path']}", "width": i["width"], "height": i["height"]}
        for i in version["images"]
    ]


def test_blank_additional_info_prints_dashes(client, estimate_id, fake_drive):
    r = _generate(client, estimate_id, info="   ")
    assert r.status_code == 200, r.text
    assert fake_drive.create_calls[0]["replacements"]["{{NOTES}}"] == "--"
    assert fake_drive.create_calls[0]["images"] == []
    assert _latest(r)["additional_info"] == ""


def test_legacy_json_body_still_generates(client, estimate_id, fake_drive):
    """Review Focus #5: an old portal tab posting JSON mid-deploy."""
    r = client.post(f"/estimates/{estimate_id}/generate-doc", json={"created_by": "old tab"})
    assert r.status_code == 200, r.text
    assert fake_drive.create_calls[0]["replacements"]["{{NOTES}}"] == "--"


def test_additional_info_over_limit_is_rejected(client, estimate_id, fake_drive):
    r = _generate(client, estimate_id, info="x" * 5001)
    assert r.status_code == 422
    assert fake_drive.create_calls == []


def test_carry_forward_keeps_order_collapses_duplicates_and_shares_blobs(client, estimate_id, fake_store):
    """Review Focus #3: a duplicated keep id places the image once."""
    v1 = _latest(_generate(client, estimate_id, files=[("a.jpg", _jpeg(), "image/jpeg"), ("b.jpg", _jpeg(), "image/jpeg")]))
    a, b = v1["images"]
    r = _generate(client, estimate_id, keep=[b["id"], a["id"], b["id"]], files=[("c.jpg", _jpeg(), "image/jpeg")])
    assert r.status_code == 200, r.text
    v2 = _latest(r)
    assert [i["file_name"] for i in v2["images"]] == ["b.jpg", "a.jpg", "c.jpg"]
    assert v2["images"][0]["storage_path"] == b["storage_path"]
    assert len(fake_store.blobs) == 3


def test_more_than_ten_images_is_rejected_before_anything_is_stored(client, estimate_id, fake_store, fake_drive):
    r = _generate(client, estimate_id, files=[(f"{n}.jpg", _jpeg((20, 20)), "image/jpeg") for n in range(11)])
    assert r.status_code == 400
    assert fake_store.blobs == {}
    assert fake_drive.create_calls == []


def test_bad_file_rejects_the_request_naming_it(client, estimate_id, fake_store, fake_drive):
    r = _generate(client, estimate_id, files=[("ok.jpg", _jpeg(), "image/jpeg"), ("x.png", b"MZ", "image/png")])
    assert r.status_code == 400
    assert "x.png" in r.json()["detail"]
    assert fake_store.blobs == {}


def test_keep_id_from_another_estimate_is_rejected(client, test_company_id, estimate_id, fake_drive):
    image = _latest(_generate(client, estimate_id, files=[("a.jpg", _jpeg(), "image/jpeg")]))["images"][0]
    other_id, other_prop = _new_estimate(client, test_company_id)
    try:
        r = _generate(client, other_id, keep=[image["id"]])
        assert r.status_code == 400
    finally:
        client.delete(f"/estimates/{other_id}")
        client.delete(f"/properties/{other_prop}")


def test_doc_failure_discards_only_new_blobs_and_records_nothing(client, estimate_id, fake_store, monkeypatch):
    kept = _latest(_generate(client, estimate_id, files=[("a.jpg", _jpeg(), "image/jpeg")]))["images"][0]

    async def _fail(drive_service, **kwargs):
        raise HTTPException(status_code=502, detail="Couldn't add images to the document. Please try again.")

    monkeypatch.setattr(docs_router, "create_doc_from_template", _fail)
    r = _generate(client, estimate_id, keep=[kept["id"]], files=[("new.jpg", _jpeg(), "image/jpeg")])
    assert r.status_code == 502
    assert len(fake_store.deleted) == 1 and fake_store.deleted[0] != kept["storage_path"]
    assert kept["storage_path"] in fake_store.blobs
    assert len(client.get(f"/estimates/{estimate_id}").json()["google_docs_versions"]) == 1


def test_delete_version_removes_only_unshared_blobs(client, estimate_id, fake_store):
    a = _latest(_generate(client, estimate_id, files=[("a.jpg", _jpeg(), "image/jpeg")]))["images"][0]
    b = _latest(_generate(client, estimate_id, keep=[a["id"]], files=[("b.jpg", _jpeg(), "image/jpeg")]))["images"][1]

    assert client.delete(f"/estimates/{estimate_id}/docs-versions/1").status_code == 200
    assert a["storage_path"] in fake_store.blobs

    assert client.delete(f"/estimates/{estimate_id}/docs-versions/2").status_code == 200
    assert a["storage_path"] not in fake_store.blobs
    assert b["storage_path"] not in fake_store.blobs


def test_get_doc_image_serves_bytes_and_404s_unknown(client, estimate_id, fake_store):
    image = _latest(_generate(client, estimate_id, files=[("a.jpg", _jpeg(), "image/jpeg")]))["images"][0]
    r = client.get(f"/estimates/{estimate_id}/doc-images/{image['id']}")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content == fake_store.blobs[image["storage_path"]]
    assert client.get(f"/estimates/{estimate_id}/doc-images/nope").status_code == 404


def test_get_doc_image_is_company_scoped(client, estimate_id):
    image = _latest(_generate(client, estimate_id, files=[("a.jpg", _jpeg(), "image/jpeg")]))["images"][0]
    outsider = onboard_owner(client, unique_email("docs.outsider"), company_name="Outsider Co",
                             company_email=unique_email("outsider.co"), phone="+15550100400")
    r = client.get(f"/estimates/{estimate_id}/doc-images/{image['id']}",
                   headers={"X-Test-Email": outsider["email"]})
    assert r.status_code == 403
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd platform && ./scripts/start_test_mongo.sh && ./run_tests.sh tests/test_estimate_documents_api.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'routers.estimate_documents'`.

- [ ] **Step 3: Create the router**

`platform/routers/estimate_documents.py`:

```python
"""Generated Google Docs for an estimate: create, list, delete, and the images
placed after the NOTES section.

Split out of routers/estimates.py (2026-09-23) when generation gained
multipart uploads — that file was already past 1,800 lines.
"""

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from dependencies import assert_company_access
from firebase_auth import verify_verified_firebase_token
from models import AuditAction, Estimate, ResourceType
from models.estimate import GoogleDocsVersion
from routers.estimate_helpers.common import sort_estimate_versions
from routers.estimate_helpers.doc_versions import (
    append_doc_version_to_estimate,
    build_doc_image_inserts,
    build_estimate_snapshot,
    calculate_next_doc_version,
    create_doc_from_template,
    discard_doc_image_paths,
    fetch_estimate_doc_context,
    find_doc_image,
    find_doc_version,
    get_or_create_doc_folder,
    image_paths_only_in,
    prepare_doc_template,
    read_doc_image_uploads,
    remove_doc_version_from_estimate,
    require_drive_service,
    resolve_kept_images,
    stage_doc_images,
    trash_doc_version,
)
from services import estimate_doc_images as doc_images
from services.audit_decorator import audit_log

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/estimates", tags=["estimates"])

MAX_ADDITIONAL_INFO_CHARS = 5000


@router.post("/{estimate_id}/generate-doc", response_model=Estimate)
@audit_log(
    action=AuditAction.ESTIMATE_DOC_GENERATE,
    resource_type=ResourceType.ESTIMATE,
    extract_resource_id=lambda result: str(result.id),
    extract_company_id=lambda result: result.company,
    capture_after=True
)
async def generate_google_doc(
    estimate_id: str,
    request: Request,
    created_by: str = Form("portal-user"),
    additional_info: str = Form("", max_length=MAX_ADDITIONAL_INFO_CHARS),
    keep_image_ids: List[str] = Form([]),
    files: List[UploadFile] = File([]),
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
    """Generate a new Google Docs version of the estimate.

    `additional_info` fills {{NOTES}} ("--" when blank). Images — carried
    forward by id from earlier versions, then new uploads — go after NOTES.
    Image handling is fail-closed: on any failure the new blobs are removed,
    the half-built doc is trashed, and no version is recorded.
    """
    drive_service = require_drive_service()

    estimate = await Estimate.get(estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    await assert_company_access(decoded_token, estimate.company)

    kept_images = resolve_kept_images(estimate, keep_image_ids)
    if len(kept_images) + len(files) > doc_images.MAX_DOC_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"A document can include at most {doc_images.MAX_DOC_IMAGES} images.",
        )
    uploads = await read_doc_image_uploads(files)
    notes_text = additional_info.strip()

    company, property_info, contacts = await fetch_estimate_doc_context(estimate)
    next_version = calculate_next_doc_version(estimate)
    year_folder_id = await get_or_create_doc_folder(drive_service, company)
    replacements, work_items = prepare_doc_template(
        estimate, company, property_info, contacts, additional_info=notes_text,
    )

    new_images = await stage_doc_images(str(estimate.company), str(estimate.id), uploads)
    images = kept_images + new_images
    file_name = f"Estimate-{estimate.estimate_id}-V{next_version}"
    try:
        doc_result = await create_doc_from_template(
            drive_service,
            estimate=estimate,
            company=company,
            file_name=file_name,
            folder_id=year_folder_id,
            replacements=replacements,
            work_items=work_items,
            images=await build_doc_image_inserts(images),
        )
    except Exception:
        await discard_doc_image_paths([image.storage_path for image in new_images])
        raise

    new_version = GoogleDocsVersion(
        version=next_version,
        doc_id=doc_result['doc_id'],
        doc_url=doc_result['doc_url'],
        drive_file_id=doc_result['drive_file_id'],
        file_name=file_name,
        created_at=datetime.now(timezone.utc),
        created_by=created_by,
        estimate_snapshot=build_estimate_snapshot(estimate),
        additional_info=notes_text,
        images=images,
    )
    await append_doc_version_to_estimate(estimate, new_version, year_folder_id)

    estimate = await Estimate.get(estimate_id)
    assert estimate is not None  # Just appended a doc version on this estimate_id; reload must succeed.
    return sort_estimate_versions(estimate)


@router.get("/{estimate_id}/doc-images/{image_id}")
async def get_doc_image(
    estimate_id: str,
    image_id: str,
    decoded_token: dict = Depends(verify_verified_firebase_token),
):
    """Stream one of the estimate's doc images, for the Documents dialog."""
    estimate = await Estimate.get(estimate_id)
    if not estimate:
        raise HTTPException(status_code=404, detail="Estimate not found")
    await assert_company_access(decoded_token, estimate.company)

    image = find_doc_image(estimate, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    try:
        content = await run_in_threadpool(doc_images.read_doc_image, image.storage_path)
    except Exception:
        logger.warning("Estimate doc image %s is missing from storage", image.storage_path, exc_info=True)
        raise HTTPException(status_code=404, detail="Image not found") from None
    return Response(content=content, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})
```

Then **move** `get_docs_versions` and `delete_docs_version` from `routers/estimates.py` into this file unchanged, except for the end of `delete_docs_version`, which becomes:

```python
    version_to_delete = find_doc_version(estimate, version)
    remaining = [v for v in estimate.google_docs_versions if v.version != version]
    await trash_doc_version(drive_service, estimate, version_to_delete)
    await remove_doc_version_from_estimate(estimate, version)
    # A carried-forward image is shared with later versions; only blobs this
    # version owned alone go.
    await discard_doc_image_paths(image_paths_only_in(version_to_delete, remaining))
```

- [ ] **Step 4: Remove the old endpoints from `routers/estimates.py`**

Delete `class GenerateDocRequest`, `generate_google_doc`, `get_docs_versions` and `delete_docs_version`. Reduce the `doc_versions` import block to:

```python
from routers.estimate_helpers.doc_versions import (  # noqa: E402
    cleanup_estimate_external_resources,
)
```

Then run `cd platform && ./run_ruff.sh routers/estimates.py`. For each name it reports as unused (F401), check whether it's a re-export before deleting it:

```bash
grep -rn "estimates_module\.<Name>\|from routers.estimates import.*<Name>\|estimates_router\.<Name>" platform/tests platform/routers platform/agents
```

Delete only the names nothing imports through `routers.estimates`. (Do not run `--fix`: CLAUDE.md warns about F401 on re-export hubs.)

- [ ] **Step 5: Register the router**

In `platform/routers/__init__.py`, after the `estimates` line:

```python
from .estimate_documents import router as estimate_documents_router
```

In `platform/main.py`, add `estimate_documents_router,` to the `from routers import (...)` list, and after `app.include_router(estimates_router, ...)`:

```python
app.include_router(estimate_documents_router, dependencies=protected_route_dependencies)
```

- [ ] **Step 6: Retarget the existing router tests**

In `platform/tests/test_generate_google_doc_router.py`:
- Add `import routers.estimate_documents as docs_router_module` wherever `import routers.estimates as estimates_module` appears in a test that hits `/generate-doc`.
- In those tests, change every `monkeypatch.setattr(estimates_module, "<name>", ...)` for `fetch_estimate_doc_context`, `get_or_create_doc_folder`, `create_doc_from_template`, `append_doc_version_to_estimate`, `require_drive_service` and `sort_estimate_versions` to target `docs_router_module`. Keep `estimates_module.Estimate.get`: it patches the shared class, so it works from either module.
- Give each `_fake_create_doc` the signature `(drive_service, estimate, company, file_name, folder_id, replacements, work_items, images=None)`.
- Change each `client.post(..., json={"created_by": "tester@example.com"}, ...)` to `data={"created_by": "tester@example.com"}`.
- Leave the `stub_doc_generator` fixture alone. It patches `routers.estimate_helpers.doc_versions.EstimateDocumentGenerator`, which is still where `prepare_doc_template` looks it up.
- `test_generate_google_doc_estimate_not_found` and `test_generate_google_doc_drive_disabled_returns_503` must patch `require_drive_service` on `docs_router_module` too. The 503 check still runs before the 404 lookup.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_estimate_documents_api.py tests/test_generate_google_doc_router.py tests/test_estimate_docs_api.py tests/test_estimate_doc_version_images.py -q`
Expected: all pass.

- [ ] **Step 8: Run the gates**

Run: `cd platform && ./run_mypy.sh routers && ./run_ruff.sh routers main.py tests/test_estimate_documents_api.py tests/test_generate_google_doc_router.py && ./run_bandit.sh routers/estimate_documents.py`
Expected: mypy and ruff are clean, and bandit adds no finding.

- [ ] **Step 9: Commit (platform, after approval)**

```bash
git -C platform add routers/estimate_documents.py routers/estimates.py routers/__init__.py main.py tests/test_estimate_documents_api.py tests/test_generate_google_doc_router.py
git -C platform commit -m "feat: generate estimate docs with additional info and images

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 6: Portal API, doc-version helpers, blob-URL hook (portal)

**Files:**
- Modify: `portal/src/api/estimates.ts` (remove `GenerateDocPayload`, replace `generateGoogleDoc`, add `docImageBlob`)
- Create: `portal/src/components/estimates/docVersions.ts`
- Create: `portal/src/lib/useBlobObjectUrl.ts`
- Modify: `portal/src/components/notes/NoteAttachmentStrip.tsx` (`useAttachmentObjectUrl` delegates to the new hook)
- Test: `portal/tests/docVersions.test.ts`, `portal/tests/estimatesApiGenerateDoc.test.ts`, `portal/tests/useBlobObjectUrl.test.tsx`

**Interfaces:**
- Produces:
  - `export interface GenerateDocInput { createdBy: string; additionalInfo: string; keepImageIds: string[]; files: File[] }` (in `api/estimates.ts`)
  - `estimatesApi.generateGoogleDoc(id: string, input: GenerateDocInput)` and `estimatesApi.docImageBlob(id: string, imageId: string): Promise<Blob>`
  - `docVersions.ts` exports:
    - `DocImage { id; file_name; width; height }`
    - `DocVersion { version; doc_url?; file_name?; created_at?; created_by?; additional_info?: string | null; images?: DocImage[] }`
    - `MAX_DOC_IMAGES = 10`, `MAX_ADDITIONAL_INFO_CHARS = 5000`, `MAX_DOC_IMAGE_BYTES`, `DOC_IMAGE_ACCEPT`
    - `latestDocVersion(versions): DocVersion | undefined`
    - `docImagePickError(file): string | null`
  - `useBlobObjectUrl(key: string | null, load: () => Promise<Blob>): string`

- [ ] **Step 1: Write the failing tests**

`portal/tests/docVersions.test.ts`:

```ts
import { describe, test, expect } from "vitest";
import { docImagePickError, latestDocVersion, MAX_DOC_IMAGE_BYTES } from "../src/components/estimates/docVersions";

describe("latestDocVersion", () => {
  test("returns the highest version regardless of order", () => {
    expect(latestDocVersion([{ version: 2 }, { version: 5 }, { version: 3 }])?.version).toBe(5);
  });
  test("returns undefined for no versions", () => {
    expect(latestDocVersion([])).toBeUndefined();
  });
});

describe("docImagePickError", () => {
  test("accepts JPEG, PNG, WebP and GIF within the size cap", () => {
    for (const type of ["image/jpeg", "image/png", "image/webp", "image/gif"]) {
      expect(docImagePickError({ name: "a", type, size: 1000 })).toBeNull();
    }
  });
  test("rejects PDFs and HEIC by name", () => {
    expect(docImagePickError({ name: "plan.pdf", type: "application/pdf", size: 1 })).toMatch(/plan\.pdf/);
    expect(docImagePickError({ name: "IMG.heic", type: "image/heic", size: 1 })).toMatch(/IMG\.heic/);
  });
  test("rejects files over 10MB", () => {
    expect(docImagePickError({ name: "big.jpg", type: "image/jpeg", size: MAX_DOC_IMAGE_BYTES + 1 })).toMatch(/10MB/);
  });
});
```

`portal/tests/estimatesApiGenerateDoc.test.ts`:

```ts
import { describe, test, expect, vi } from "vitest";

const apiRequest = vi.fn((..._args: unknown[]) => Promise.resolve({}));
const apiRequestBlob = vi.fn((..._args: unknown[]) => Promise.resolve(new Blob()));
vi.mock("../src/api/client", () => ({
  apiRequest: (...args: unknown[]) => apiRequest(...args),
  apiRequestBlob: (...args: unknown[]) => apiRequestBlob(...args),
  apiRequestWithTotal: vi.fn(),
}));

import { estimatesApi } from "../src/api/estimates";

describe("estimatesApi.generateGoogleDoc", () => {
  test("posts multipart with repeated keep ids and files", async () => {
    const file = new File(["x"], "gate.jpg", { type: "image/jpeg" });
    await estimatesApi.generateGoogleDoc("est-1", {
      createdBy: "Sam", additionalInfo: "Side gate", keepImageIds: ["a", "b"], files: [file],
    });
    const [path, options] = apiRequest.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/estimates/est-1/generate-doc");
    expect(options.method).toBe("POST");
    const form = options.body as FormData;
    expect(form.get("created_by")).toBe("Sam");
    expect(form.get("additional_info")).toBe("Side gate");
    expect(form.getAll("keep_image_ids")).toEqual(["a", "b"]);
    expect((form.getAll("files")[0] as File).name).toBe("gate.jpg");
  });

  test("docImageBlob fetches the authed image path", async () => {
    await estimatesApi.docImageBlob("est-1", "img 1");
    expect(apiRequestBlob).toHaveBeenCalledWith("/estimates/est-1/doc-images/img%201");
  });
});
```

(If `src/api/estimates.ts` imports anything else from `./client`, add it to the mock factory with `vi.fn()`.)

`portal/tests/useBlobObjectUrl.test.tsx`:

```tsx
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, cleanup } from "@testing-library/react";
import { useBlobObjectUrl } from "../src/lib/useBlobObjectUrl";

afterEach(cleanup);

beforeEach(() => {
  URL.createObjectURL = vi.fn(() => "blob:mock");
  URL.revokeObjectURL = vi.fn();
});

describe("useBlobObjectUrl", () => {
  test("loads once per key and exposes the object URL", async () => {
    const load = vi.fn(() => Promise.resolve(new Blob(["x"])));
    const { result, rerender } = renderHook(({ k }) => useBlobObjectUrl(k, load), { initialProps: { k: "a" } });
    await waitFor(() => expect(result.current).toBe("blob:mock"));
    rerender({ k: "a" });
    expect(load).toHaveBeenCalledTimes(1);
  });

  test("a null key loads nothing", () => {
    const load = vi.fn(() => Promise.resolve(new Blob()));
    renderHook(() => useBlobObjectUrl(null, load));
    expect(load).not.toHaveBeenCalled();
  });

  test("revokes on unmount", async () => {
    const { result, unmount } = renderHook(() => useBlobObjectUrl("a", () => Promise.resolve(new Blob())));
    await waitFor(() => expect(result.current).toBe("blob:mock"));
    unmount();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:mock");
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd portal && npm test -- docVersions estimatesApiGenerateDoc useBlobObjectUrl`
Expected: FAIL with `Failed to resolve import "../src/components/estimates/docVersions"` and `"../src/lib/useBlobObjectUrl"`, and the API test fails on `form.get` of a JSON string body.

- [ ] **Step 3: Implement**

`portal/src/components/estimates/docVersions.ts`:

```ts
/** A generated Google Doc version and the inputs it was built from. */
export interface DocImage {
  id: string;
  file_name: string;
  width: number;
  height: number;
}

export interface DocVersion {
  version: number;
  doc_url?: string;
  file_name?: string;
  created_at?: string;
  created_by?: string;
  /** What printed in NOTES. Null/absent on versions from before 2026-09-23. */
  additional_info?: string | null;
  images?: DocImage[];
}

/** Client-side mirrors of services/estimate_doc_images.py and the router's limit. */
export const MAX_DOC_IMAGES = 10;
export const MAX_ADDITIONAL_INFO_CHARS = 5000;
export const MAX_DOC_IMAGE_BYTES = 10 * 1024 * 1024;
export const DOC_IMAGE_ACCEPT = "image/jpeg,image/png,image/webp,image/gif";
const ACCEPTED_TYPES = new Set(DOC_IMAGE_ACCEPT.split(","));

/** The newest version by number — the one the dialog's form prefills from. */
export function latestDocVersion(versions: DocVersion[]): DocVersion | undefined {
  return versions.reduce<DocVersion | undefined>(
    (latest, v) => (!latest || v.version > latest.version ? v : latest),
    undefined,
  );
}

/** Fast local rejection before a doomed upload. Null means the file is fine. */
export function docImagePickError(file: Pick<File, "name" | "type" | "size">): string | null {
  if (!ACCEPTED_TYPES.has(file.type)) return `"${file.name}" isn't a JPEG, PNG, WebP or GIF image.`;
  if (file.size > MAX_DOC_IMAGE_BYTES) return `"${file.name}" is larger than 10MB.`;
  return null;
}
```

`portal/src/lib/useBlobObjectUrl.ts`:

```ts
import { useEffect, useRef, useState } from "react";

/**
 * Fetch a blob through an authed loader and expose it as an object URL,
 * revoked when `key` changes or the host unmounts. A null key loads nothing.
 *
 * `load` is read through a ref, so an inline arrow does not refetch on every
 * render — only a new `key` does.
 */
export function useBlobObjectUrl(key: string | null, load: () => Promise<Blob>): string {
  const loadRef = useRef(load);
  useEffect(() => {
    loadRef.current = load;
  });
  const [objectUrl, setObjectUrl] = useState("");
  useEffect(() => {
    if (!key) return;
    let alive = true;
    let url = "";
    loadRef.current()
      .then((blob) => {
        url = URL.createObjectURL(blob);
        if (alive) setObjectUrl(url);
        else URL.revokeObjectURL(url);
      })
      .catch(() => {
        // Leave the placeholder; the tile is still listed and removable.
      });
    return () => {
      alive = false;
      if (url) URL.revokeObjectURL(url);
      setObjectUrl("");
    };
  }, [key]);
  return objectUrl;
}
```

In `portal/src/components/notes/NoteAttachmentStrip.tsx`, replace the body of `useAttachmentObjectUrl` (keep its signature and doc comment):

```ts
function useAttachmentObjectUrl(noteId: string, attachmentId: string | undefined, size: "thumb" | "full") {
  return useBlobObjectUrl(
    attachmentId ? `${noteId}/${attachmentId}/${size}` : null,
    () => notesApi.attachmentBlob(noteId, attachmentId ?? "", size),
  );
}
```

Add `import { useBlobObjectUrl } from "../../lib/useBlobObjectUrl";` and drop `useEffect`/`useState` from the React import only if nothing else in the file uses them.

In `portal/src/api/estimates.ts`, import `apiRequestBlob` from `./client`, delete `interface GenerateDocPayload`, and add:

```ts
export interface GenerateDocInput {
  createdBy: string;
  additionalInfo: string;
  keepImageIds: string[];
  files: File[];
}
```

Replace `generateGoogleDoc` and add `docImageBlob`:

```ts
  generateGoogleDoc: (id: string, input: GenerateDocInput) => {
    const form = new FormData();
    form.append("created_by", input.createdBy);
    form.append("additional_info", input.additionalInfo);
    input.keepImageIds.forEach((imageId) => form.append("keep_image_ids", imageId));
    input.files.forEach((file) => form.append("files", file, file.name));
    return apiRequest<unknown>(`/estimates/${id}/generate-doc`, { method: "POST", body: form });
  },
  docImageBlob: (id: string, imageId: string) =>
    apiRequestBlob(`/estimates/${encodeURIComponent(id)}/doc-images/${encodeURIComponent(imageId)}`),
```

- [ ] **Step 4: Run the tests to verify they pass, including the notes regression**

Run: `cd portal && npm test -- docVersions estimatesApiGenerateDoc useBlobObjectUrl NoteAttachment NoteCard NotesPanel`
Expected: all pass. `NewEstimateWithActivityPage` won't typecheck yet, because it still calls the old payload shape; Task 8 fixes that.

- [ ] **Step 5: Lint**

Run: `cd portal && npx eslint src/api/estimates.ts src/components/estimates/docVersions.ts src/lib/useBlobObjectUrl.ts src/components/notes/NoteAttachmentStrip.tsx`
Expected: clean.

- [ ] **Step 6: Commit (portal, after approval)**

```bash
git -C portal add src/api/estimates.ts src/components/estimates/docVersions.ts src/lib/useBlobObjectUrl.ts src/components/notes/NoteAttachmentStrip.tsx tests/docVersions.test.ts tests/estimatesApiGenerateDoc.test.ts tests/useBlobObjectUrl.test.tsx
git -C portal commit -m "feat: add multipart doc generation client and doc-version helpers

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 7: `DocumentsDialog` (portal)

**Files:**
- Create: `portal/src/components/estimates/DocumentsDialog.tsx`
- Test: `portal/tests/DocumentsDialog.test.tsx`

**Interfaces:**
- Consumes: Task 6 (`docVersions.ts`, `estimatesApi.docImageBlob`, `useBlobObjectUrl`), `Modal` (`src/components/common/Modal`) and `AttachmentRemoveBadge`.
- Produces:

```ts
export interface DocGenerateRequest { additionalInfo: string; keepImageIds: string[]; files: File[] }
export interface DocumentsDialogProps {
  estimateId: string;
  versions: DocVersion[];
  isGenerating: boolean;
  isSaving: boolean;
  isDeleting: boolean;
  /** Resolves with the estimate's versions after success; rejects with an Error whose message is shown. */
  onGenerate: (request: DocGenerateRequest) => Promise<DocVersion[]>;
  onDelete: (version: DocVersion) => void;
  onClose: () => void;
}
export function DocumentsDialog(props: DocumentsDialogProps): JSX.Element
```

Mounting the dialog is opening it: there is no `open` prop (the `NoteComposer` pattern).

- [ ] **Step 1: Write the failing tests**

`portal/tests/DocumentsDialog.test.tsx`:

```tsx
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { DocVersion } from "../src/components/estimates/docVersions";

vi.mock("../src/api/estimates", () => ({
  estimatesApi: { docImageBlob: vi.fn(() => Promise.resolve(new Blob(["x"]))) },
}));

import { DocumentsDialog, type DocumentsDialogProps } from "../src/components/estimates/DocumentsDialog";

afterEach(cleanup);
beforeEach(() => {
  URL.createObjectURL = vi.fn(() => `blob:${Math.random()}`);
  URL.revokeObjectURL = vi.fn();
});

const v1: DocVersion = { version: 1, doc_url: "https://docs/1", created_by: "Ana", created_at: "2026-09-12T10:00:00Z" };
const v2: DocVersion = {
  version: 2, doc_url: "https://docs/2", created_by: "Sam", created_at: "2026-09-20T10:00:00Z",
  additional_info: "Side gate code 4321",
  images: [
    { id: "img-a", file_name: "north-bed.jpg", width: 800, height: 600 },
    { id: "img-b", file_name: "side-gate.jpg", width: 800, height: 600 },
  ],
};

function renderDialog(overrides: Partial<DocumentsDialogProps> = {}) {
  const props: DocumentsDialogProps = {
    estimateId: "est-1", versions: [v2, v1], isGenerating: false, isSaving: false, isDeleting: false,
    onGenerate: vi.fn(() => Promise.resolve([v2, v1])), onDelete: vi.fn(), onClose: vi.fn(),
    ...overrides,
  };
  const utils = render(<DocumentsDialog {...props} />);
  return { ...utils, props };
}

const jpeg = (name: string, size = 1000) => new File(["x".repeat(size)], name, { type: "image/jpeg" });

describe("DocumentsDialog", () => {
  test("lists versions newest first as new-tab links with image counts", () => {
    renderDialog();
    const links = screen.getAllByRole("link");
    expect(links.map((l) => l.textContent)).toEqual([expect.stringContaining("Estimate v2"), expect.stringContaining("Estimate v1")]);
    expect(links[0].getAttribute("href")).toBe("https://docs/2");
    expect(links[0].getAttribute("target")).toBe("_blank");
    expect(links[0].getAttribute("rel")).toContain("noopener");
    expect(screen.getByText(/2 images/)).toBeTruthy();
  });

  test("shows an empty state with no versions", () => {
    renderDialog({ versions: [] });
    expect(screen.getByText("No documents yet.")).toBeTruthy();
  });

  test("the trash icon asks the page to delete that version", async () => {
    const { props } = renderDialog();
    await userEvent.click(screen.getByRole("button", { name: "Delete Estimate v1" }));
    expect(props.onDelete).toHaveBeenCalledWith(v1);
  });

  test("prefills from the latest version", () => {
    renderDialog();
    expect((screen.getByLabelText("Additional information") as HTMLTextAreaElement).value).toBe("Side gate code 4321");
    expect(screen.getByRole("button", { name: "Remove north-bed.jpg" })).toBeTruthy();
    expect(screen.getByText("2 / 10")).toBeTruthy();
  });

  test("a legacy latest version prefills nothing", () => {
    renderDialog({ versions: [v1] });
    expect((screen.getByLabelText("Additional information") as HTMLTextAreaElement).value).toBe("");
    expect(screen.getByText("0 / 10")).toBeTruthy();
  });

  test("generate sends the text, the kept images and the new files", async () => {
    const { props } = renderDialog();
    await userEvent.click(screen.getByRole("button", { name: "Remove north-bed.jpg" }));
    const file = jpeg("new.jpg");
    await userEvent.upload(screen.getByLabelText("Add images"), file);
    await userEvent.click(screen.getByRole("button", { name: "Generate document" }));
    expect(props.onGenerate).toHaveBeenCalledWith({
      additionalInfo: "Side gate code 4321", keepImageIds: ["img-b"], files: [file],
    });
  });

  test("rejects non-images and oversize files, and stops at 10 images", async () => {
    renderDialog({ versions: [v1] });
    const input = screen.getByLabelText("Add images");
    // v14 filters by `accept` unless told not to; the point here is the dialog's own check.
    await userEvent.setup({ applyAccept: false }).upload(input, new File(["x"], "plan.pdf", { type: "application/pdf" }));
    expect(screen.getByRole("alert").textContent).toMatch(/plan\.pdf/);
    await userEvent.upload(input, Array.from({ length: 11 }, (_, n) => jpeg(`${n}.jpg`)));
    expect(screen.getByText("10 / 10")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toMatch(/at most 10 images/);
  });

  test("after success the form re-prefills from the new latest version", async () => {
    const v3: DocVersion = { version: 3, additional_info: "Fresh text", images: [{ id: "img-c", file_name: "c.jpg", width: 1, height: 1 }] };
    renderDialog({ onGenerate: vi.fn(() => Promise.resolve([v3, v2, v1])) });
    await userEvent.upload(screen.getByLabelText("Add images"), jpeg("staged.jpg"));
    await userEvent.click(screen.getByRole("button", { name: "Generate document" }));
    await waitFor(() =>
      expect((screen.getByLabelText("Additional information") as HTMLTextAreaElement).value).toBe("Fresh text"),
    );
    expect(screen.queryByRole("button", { name: "Remove staged.jpg" })).toBeNull();
    expect(screen.getByRole("button", { name: "Remove c.jpg" })).toBeTruthy();
  });

  test("a failed generation shows the error and keeps the form", async () => {
    renderDialog({ onGenerate: vi.fn(() => Promise.reject(new Error("Couldn't add images to the document. Please try again."))) });
    await userEvent.click(screen.getByRole("button", { name: "Generate document" }));
    expect((await screen.findByRole("alert")).textContent).toMatch(/Couldn't add images/);
    expect((screen.getByLabelText("Additional information") as HTMLTextAreaElement).value).toBe("Side gate code 4321");
  });

  test("deleting the latest version keeps typed text but drops vanished images", async () => {
    // Review Focus #4
    const { rerender, props } = renderDialog();
    const box = screen.getByLabelText("Additional information");
    await userEvent.clear(box);
    await userEvent.type(box, "Still typing");
    rerender(<DocumentsDialog {...props} versions={[v1]} />);
    expect((screen.getByLabelText("Additional information") as HTMLTextAreaElement).value).toBe("Still typing");
    expect(screen.queryByRole("button", { name: "Remove north-bed.jpg" })).toBeNull();
    expect(screen.getByText("0 / 10")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd portal && npm test -- DocumentsDialog`
Expected: FAIL with `Failed to resolve import "../src/components/estimates/DocumentsDialog"`.

- [ ] **Step 3: Implement**

`portal/src/components/estimates/DocumentsDialog.tsx`:

```tsx
import { useEffect, useMemo, useRef, useState } from "react";
import { ExternalLink, FileText, ImagePlus, Loader2, Trash2 } from "lucide-react";
import { Modal } from "../common/Modal";
import { AttachmentRemoveBadge } from "../common/AttachmentRemoveBadge";
import { estimatesApi } from "../../api/estimates";
import { useBlobObjectUrl } from "../../lib/useBlobObjectUrl";
import {
  DOC_IMAGE_ACCEPT, MAX_ADDITIONAL_INFO_CHARS, MAX_DOC_IMAGES,
  docImagePickError, latestDocVersion, type DocImage, type DocVersion,
} from "./docVersions";

export interface DocGenerateRequest {
  additionalInfo: string;
  keepImageIds: string[];
  files: File[];
}

export interface DocumentsDialogProps {
  estimateId: string;
  versions: DocVersion[];
  isGenerating: boolean;
  isSaving: boolean;
  isDeleting: boolean;
  /** Resolves with the estimate's versions after success; rejects with an Error whose message is shown. */
  onGenerate: (request: DocGenerateRequest) => Promise<DocVersion[]>;
  onDelete: (version: DocVersion) => void;
  onClose: () => void;
}

interface StagedImage {
  file: File;
  previewUrl: string;
}

const TILE = "relative w-20 shrink-0";
const THUMB = "w-full aspect-square rounded-lg object-cover border border-gray-200 bg-gray-100";

function KeptImageTile({ estimateId, image, disabled, onRemove }: {
  estimateId: string; image: DocImage; disabled: boolean; onRemove: () => void;
}) {
  const url = useBlobObjectUrl(`${estimateId}/${image.id}`, () => estimatesApi.docImageBlob(estimateId, image.id));
  return (
    <div className={TILE} title={image.file_name}>
      {url ? <img src={url} alt={image.file_name} className={THUMB} /> : <div className={THUMB} aria-label={image.file_name} />}
      <AttachmentRemoveBadge filename={image.file_name} onClick={onRemove} disabled={disabled} />
    </div>
  );
}

function formatCreated(v: DocVersion): string {
  const date = v.created_at
    ? new Date(v.created_at).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" })
    : "";
  const count = v.images?.length ?? 0;
  return [date, v.created_by, count ? `${count} ${count === 1 ? "image" : "images"}` : ""].filter(Boolean).join(" · ");
}

/**
 * Generated versions (read-only: open or delete) above the form for the next
 * one. Mounting is opening — the page renders this only while it is open.
 *
 * The form prefills from the LATEST version when it mounts and again after a
 * successful generation, never on other changes to `versions`: a delete
 * mid-edit must not wipe what the user is typing. Kept images whose version
 * vanished are filtered out at render instead, so they neither show nor get
 * sent (the server would 400 on them).
 */
export function DocumentsDialog({
  estimateId, versions, isGenerating, isSaving, isDeleting, onGenerate, onDelete, onClose,
}: DocumentsDialogProps) {
  const [info, setInfo] = useState(() => latestDocVersion(versions)?.additional_info ?? "");
  const [kept, setKept] = useState<DocImage[]>(() => latestDocVersion(versions)?.images ?? []);
  const [staged, setStaged] = useState<StagedImage[]>([]);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const busy = isGenerating || isSaving;

  const stagedRef = useRef<StagedImage[]>([]);
  useEffect(() => {
    stagedRef.current = staged;
  }, [staged]);
  useEffect(() => () => stagedRef.current.forEach((s) => URL.revokeObjectURL(s.previewUrl)), []);

  const sorted = useMemo(() => [...versions].sort((a, b) => b.version - a.version), [versions]);
  const liveImageIds = useMemo(
    () => new Set(versions.flatMap((v) => (v.images ?? []).map((i) => i.id))),
    [versions],
  );
  const visibleKept = kept.filter((image) => liveImageIds.has(image.id));
  const imageCount = visibleKept.length + staged.length;

  const addFiles = (files: FileList | File[] | null) => {
    if (!files) return;
    const rejected: string[] = [];
    const additions: StagedImage[] = [];
    let room = MAX_DOC_IMAGES - imageCount;
    for (const file of Array.from(files)) {
      const pickError = docImagePickError(file);
      if (pickError) {
        rejected.push(pickError);
        continue;
      }
      if (room <= 0) {
        rejected.push(`A document can include at most ${MAX_DOC_IMAGES} images.`);
        break;
      }
      additions.push({ file, previewUrl: URL.createObjectURL(file) });
      room -= 1;
    }
    setError(rejected.join(" "));
    setStaged((previous) => [...previous, ...additions]);
    if (inputRef.current) inputRef.current.value = "";
  };

  const unstage = (target: StagedImage) => {
    URL.revokeObjectURL(target.previewUrl);
    setStaged((previous) => previous.filter((s) => s.previewUrl !== target.previewUrl));
  };

  const submit = async () => {
    if (busy) return;
    setError("");
    try {
      const updated = await onGenerate({
        additionalInfo: info,
        keepImageIds: visibleKept.map((image) => image.id),
        files: staged.map((s) => s.file),
      });
      const next = latestDocVersion(updated);
      staged.forEach((s) => URL.revokeObjectURL(s.previewUrl));
      setStaged([]);
      setInfo(next?.additional_info ?? "");
      setKept(next?.images ?? []);
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : "Couldn't generate the document. Try again.");
    }
  };

  return (
    <Modal
      open
      title="Documents"
      onClose={() => { if (!busy) onClose(); }}
      maxWidth="max-w-2xl"
      bottomSheetOnMobile
      footer={
        <div className="space-y-2">
          <p role="alert" className="text-xs text-red-600 min-h-4">{error}</p>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} disabled={busy}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-60">
              Close
            </button>
            <button type="button" onClick={() => void submit()} disabled={busy}
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-brand text-white rounded-lg hover:bg-brand-dark disabled:opacity-50">
              {isGenerating && <Loader2 className="w-4 h-4 animate-spin" />}
              Generate document
            </button>
          </div>
        </div>
      }
    >
      <div className="space-y-5">
        <section aria-labelledby="documents-versions-heading">
          <h4 id="documents-versions-heading" className="text-sm font-medium text-gray-900 mb-2">Generated versions</h4>
          {sorted.length === 0 ? (
            <p className="text-sm text-gray-500">No documents yet.</p>
          ) : (
            <ul className="divide-y divide-gray-200 border border-gray-200 rounded-lg max-h-56 overflow-y-auto">
              {sorted.map((v) => (
                <li key={v.version} className="flex items-center gap-3 px-3 py-2">
                  <FileText className="w-4 h-4 text-blue-600 shrink-0" aria-hidden="true" />
                  <div className="flex-1 min-w-0">
                    {v.doc_url ? (
                      <a href={v.doc_url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline">
                        Estimate v{v.version}
                        <ExternalLink className="w-3 h-3" aria-hidden="true" />
                      </a>
                    ) : (
                      <span className="text-sm text-gray-700">Estimate v{v.version}</span>
                    )}
                    <p className="text-xs text-gray-500 truncate">{formatCreated(v)}</p>
                  </div>
                  <button type="button" aria-label={`Delete Estimate v${v.version}`} title="Delete this version"
                    disabled={isDeleting || busy} onClick={() => onDelete(v)}
                    className="inline-flex items-center justify-center w-8 h-8 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full disabled:opacity-60">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="documents-new-heading" className="border-t border-gray-200 pt-4 space-y-3">
          <h4 id="documents-new-heading" className="text-sm font-medium text-gray-900">New document</h4>
          <div>
            <label htmlFor="documents-additional-info" className="block text-sm font-medium text-gray-700 mb-1">
              Additional information
            </label>
            <textarea id="documents-additional-info" rows={4} value={info} maxLength={MAX_ADDITIONAL_INFO_CHARS}
              onChange={(e) => setInfo(e.target.value)} disabled={busy}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Printed in the Notes section. Left blank, it shows "--".</span>
              <span>{info.length.toLocaleString()} / {MAX_ADDITIONAL_INFO_CHARS.toLocaleString()}</span>
            </div>
          </div>

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); if (!busy) addFiles(e.dataTransfer.files); }}
          >
            <div className="flex items-baseline justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Images</span>
              <span className="text-xs text-gray-500">{imageCount} / {MAX_DOC_IMAGES}</span>
            </div>
            <div className="flex flex-wrap gap-3 pt-1.5">
              {visibleKept.map((image) => (
                <KeptImageTile key={image.id} estimateId={estimateId} image={image} disabled={busy}
                  onRemove={() => setKept((previous) => previous.filter((i) => i.id !== image.id))} />
              ))}
              {staged.map((item) => (
                <div key={item.previewUrl} className={TILE} title={item.file.name}>
                  <img src={item.previewUrl} alt={item.file.name} className={THUMB} />
                  <AttachmentRemoveBadge filename={item.file.name} onClick={() => unstage(item)} disabled={busy} />
                </div>
              ))}
              {imageCount < MAX_DOC_IMAGES && (
                <label className="flex flex-col items-center justify-center gap-1 w-20 aspect-square rounded-lg border border-dashed border-gray-400 text-gray-500 text-xs cursor-pointer hover:bg-gray-50">
                  <ImagePlus className="w-5 h-5" aria-hidden="true" />
                  Add images
                  <input ref={inputRef} type="file" multiple accept={DOC_IMAGE_ACCEPT} className="sr-only"
                    aria-label="Add images" disabled={busy} onChange={(e) => addFiles(e.target.files)} />
                </label>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Added after the Notes section. JPEG, PNG, WebP or GIF, up to 10MB each.
            </p>
          </div>
        </section>
      </div>
    </Modal>
  );
}
```

Two notes:
- The "rejects … stops at 10" test uploads 11 files while the "Add images" tile disappears at 10. That's fine, because `addFiles` handles the whole `FileList` in one call.
- If `Modal`'s prop set differs from what `NoteComposer` uses (`bottomSheetOnMobile`), mirror `NoteComposer.tsx` exactly.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd portal && npm test -- DocumentsDialog`
Expected: all pass.

- [ ] **Step 5: Lint**

Run: `cd portal && npx eslint src/components/estimates/DocumentsDialog.tsx tests/DocumentsDialog.test.tsx`
Expected: clean.

- [ ] **Step 6: Commit (portal, after approval)**

```bash
git -C portal add src/components/estimates/DocumentsDialog.tsx tests/DocumentsDialog.test.tsx
git -C portal commit -m "feat: add the estimate Documents dialog

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 8: "Documents (N)" button and page integration; remove `DocumentsBar` (portal)

**Files:**
- Create: `portal/src/components/estimates/EstimateDocuments.tsx`
- Modify: `portal/src/pages/NewEstimateWithActivityPage.tsx`:
  - the import around line 87
  - remove the `selectedDocVersion` state (line ~245)
  - `handleGenerateGoogleDoc` (lines ~553–579)
  - the `DocumentsBar` JSX (lines ~1031–1046)
  - the Delete Doc Version `Modal` (line ~1531) gains `zIndexClassName="z-[60]"`
- Delete: `portal/src/components/estimates/DocumentsBar.tsx` and `portal/tests/DocumentsBar.test.tsx`
- Modify: the `vi.mock("../src/components/estimates/DocumentsBar", ...)` line in each of `tests/EstimateChecklistDialogLayout.test.tsx`, `tests/NewEstimateWithActivityPage.autosave.test.tsx`, `tests/NewEstimateWithActivityPage.notes.test.tsx`, `tests/NewEstimateWithActivityPage.sendGate.test.tsx`, `tests/NewEstimateWithActivityPropertyLabel.test.tsx`, `tests/NewEstimateWithActivityRetry.test.tsx` and `tests/WorkItemsMobileColumns.test.tsx`
- Modify: `portal/tests/EstimateEditorTour.test.tsx` (header comment), `portal/src/tours/registry.ts` (`estimate-documents` step text)
- Test: `portal/tests/EstimateDocuments.test.tsx` (new), `portal/tests/NewEstimateWithActivityPage.documents.test.tsx` (new)

**Interfaces:**
- Consumes: Task 7 (`DocumentsDialog`, `DocumentsDialogProps`, `DocGenerateRequest`), Task 6 (`estimatesApi.generateGoogleDoc(id, GenerateDocInput)`, `latestDocVersion`, `DocVersion`).
- Produces: `export default function EstimateDocuments(props: Omit<DocumentsDialogProps, "onClose">)`, which renders a `data-tour="estimate-documents"` wrapper holding the "Documents (N)" button.

- [ ] **Step 1: Write the failing tests**

`portal/tests/EstimateDocuments.test.tsx`:

```tsx
import { describe, test, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../src/components/estimates/DocumentsDialog", () => ({
  DocumentsDialog: ({ onClose }: { onClose: () => void }) => (
    <div role="dialog" aria-label="Documents">
      <button type="button" onClick={onClose}>close-stub</button>
    </div>
  ),
}));

import EstimateDocuments from "../src/components/estimates/EstimateDocuments";

afterEach(cleanup);

const props = {
  estimateId: "est-1", isGenerating: false, isSaving: false, isDeleting: false,
  onGenerate: vi.fn(), onDelete: vi.fn(),
};

describe("EstimateDocuments", () => {
  test("labels the button with the version count, zero included", () => {
    const { rerender } = render(<EstimateDocuments {...props} versions={[]} />);
    expect(screen.getByRole("button", { name: /Documents \(0\)/ })).toBeTruthy();
    rerender(<EstimateDocuments {...props} versions={[{ version: 2 }, { version: 1 }]} />);
    expect(screen.getByRole("button", { name: /Documents \(2\)/ })).toBeTruthy();
  });

  test("keeps the tour anchor", () => {
    const { container } = render(<EstimateDocuments {...props} versions={[]} />);
    expect(container.querySelector('[data-tour="estimate-documents"]')).toBeTruthy();
  });

  test("opens and closes the dialog", async () => {
    render(<EstimateDocuments {...props} versions={[]} />);
    expect(screen.queryByRole("dialog")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /Documents/ }));
    expect(screen.getByRole("dialog", { name: "Documents" })).toBeTruthy();
    await userEvent.click(screen.getByText("close-stub"));
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
```

`portal/tests/NewEstimateWithActivityPage.documents.test.tsx`: copy the whole harness from `tests/NewEstimateWithActivityPage.autosave.test.tsx`, which is everything above its first `describe(`: the `vi.mock` calls, `makeEstimate`, `renderEditMode` and `beforeEach`. Then make these changes:
- In the `../src/api/estimates` mock factory, add `generateGoogleDoc: (id: string, input: unknown) => generateMock(id, input),` and declare `const generateMock = vi.fn();` next to `getMock`.
- Replace its `DocumentsBar` mock with this stub:

```tsx
const generateResults: Promise<unknown>[] = [];
vi.mock("../src/components/estimates/EstimateDocuments", () => ({
  default: (p: { onGenerate: (r: unknown) => Promise<unknown> }) => (
    <button type="button" onClick={() => {
      generateResults.push(p.onGenerate({ additionalInfo: "Gate", keepImageIds: ["img-1"], files: [] }));
    }}>
      stub-generate
    </button>
  ),
}));
```

Then the test:

```tsx
describe("NewEstimateWithActivityPage — documents", () => {
  test("generating passes the dialog's inputs, opens the new doc, and resolves the versions", async () => {
    const versions = [{ version: 1, doc_url: "https://docs/1" }];
    getMock.mockResolvedValue(makeEstimate());
    generateMock.mockResolvedValue(makeEstimate({ google_docs_versions: versions }));
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);

    renderEditMode();
    fireEvent.click(await screen.findByText("stub-generate"));

    await expect(generateResults[0]).resolves.toEqual(versions);
    expect(generateMock).toHaveBeenCalledWith("est-1", expect.objectContaining({
      additionalInfo: "Gate", keepImageIds: ["img-1"], files: [],
    }));
    expect(openSpy).toHaveBeenCalledWith("https://docs/1", "_blank");
    openSpy.mockRestore();
  });

  test("a failed generation rejects so the dialog can show it", async () => {
    getMock.mockResolvedValue(makeEstimate());
    generateMock.mockRejectedValue(new Error("Couldn't add images to the document. Please try again."));
    renderEditMode();
    fireEvent.click(await screen.findByText("stub-generate"));
    await expect(generateResults.at(-1)).rejects.toThrow(/Couldn't add images/);
  });
});
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd portal && npm test -- EstimateDocuments NewEstimateWithActivityPage.documents`
Expected: FAIL with `Failed to resolve import "../src/components/estimates/EstimateDocuments"`, and "stub-generate" is not found, because the page still renders `DocumentsBar`.

- [ ] **Step 3: Implement `EstimateDocuments`**

`portal/src/components/estimates/EstimateDocuments.tsx`:

```tsx
import { useState } from "react";
import { FileText } from "lucide-react";
import { DocumentsDialog, type DocumentsDialogProps } from "./DocumentsDialog";

/**
 * The estimate page's entry to its generated Google Docs: a count on a button,
 * with the list and the generate form behind it in DocumentsDialog. Replaced
 * the inline DocumentsBar dropdown 2026-09-23.
 */
export default function EstimateDocuments(props: Omit<DocumentsDialogProps, "onClose">) {
  const [isOpen, setIsOpen] = useState(false);
  return (
    // data-tour: anchor for the estimate editor tour's documents step
    <div data-tour="estimate-documents" className="flex items-center">
      <button type="button" onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white text-gray-700 hover:bg-gray-50">
        <FileText className="w-4 h-4" aria-hidden="true" />
        Documents ({props.versions.length})
      </button>
      {isOpen && <DocumentsDialog {...props} onClose={() => setIsOpen(false)} />}
    </div>
  );
}
```

- [ ] **Step 4: Wire the page**

In `NewEstimateWithActivityPage.tsx`:
- Replace `import DocumentsBar, { type DocVersion } from "../components/estimates/DocumentsBar";` with:

```ts
import EstimateDocuments from "../components/estimates/EstimateDocuments";
import type { DocGenerateRequest } from "../components/estimates/DocumentsDialog";
import { latestDocVersion, type DocVersion } from "../components/estimates/docVersions";
```

- Delete `const [selectedDocVersion, setSelectedDocVersion] = useState<number | null>(null);`.
- Replace `handleGenerateGoogleDoc` with:

```ts
  // Resolves with the new versions for the Documents dialog to re-prefill
  // from; rejects with a user-facing message the dialog shows (the page's own
  // error banner sits behind the modal).
  const handleGenerateGoogleDoc = async (request: DocGenerateRequest): Promise<DocVersion[]> => {
    if (!estimate) throw new Error("The estimate is still loading. Try again in a moment.");
    setIsGeneratingDoc(true);
    try {
      if (isDirty) {
        const saved = await handleSaveEstimate();
        if (!saved) throw new Error("Your changes couldn't be saved, so no document was generated.");
      }
      const updated = await estimatesApi.generateGoogleDoc(getEntityId(estimate), {
        ...request,
        createdBy: currentUserDisplayName || "portal-user",
      }) as EstimateWithExtras;
      setEstimate(updated);
      const versions = updated.google_docs_versions || [];
      setDocVersions(versions);
      const latest = latestDocVersion(versions);
      if (latest?.doc_url) window.open(latest.doc_url, "_blank");
      return versions;
    } finally {
      setIsGeneratingDoc(false);
    }
  };
```

(If `getEntityId(estimate)` is typed `string | null` here, keep whatever narrowing the old handler used.)

- Replace the `{/* Documents row ... */}` block with:

```tsx
        {/* Documents — generated versions + the form for the next, in a dialog */}
        {isEditMode && estimate && (
          <EstimateDocuments
            estimateId={getEntityId(estimate) ?? ""}
            versions={docVersions}
            isGenerating={isGeneratingDoc}
            isSaving={isSaving}
            isDeleting={isSubmitting}
            onGenerate={handleGenerateGoogleDoc}
            onDelete={(v) => {
              setDocVersionToDelete(v);
              setIsDeleteDocOpen(true);
              setFormError("");
            }}
          />
        )}
```

- On the Delete Document Version `<Modal`, add `zIndexClassName="z-[60]"`. It now opens on top of the Documents dialog (`z-50`).

- [ ] **Step 5: Remove `DocumentsBar` and retarget the mocks**

```bash
git -C portal rm src/components/estimates/DocumentsBar.tsx tests/DocumentsBar.test.tsx
```

In each of the seven test files listed under **Files**, change
`vi.mock("../src/components/estimates/DocumentsBar", () => ({ default: () => null }));` to
`vi.mock("../src/components/estimates/EstimateDocuments", () => ({ default: () => null }));`.

In `tests/EstimateEditorTour.test.tsx`, change the header comment's "REAL EstimateTitleBar and DocumentsBar" to "REAL EstimateTitleBar and EstimateDocuments".

In `src/tours/registry.ts`, set the `estimate-documents` step text to:

```ts
        text: "Open Documents to generate printable Google Docs versions of an Estimate for your Customer — add extra information and photos — and reopen earlier versions.",
```

(`tests/tourRegistry.test.ts` expects `/Google Docs/`, which this still matches.)

- [ ] **Step 6: Run the tests and the typecheck**

Run: `cd portal && npm test -- EstimateDocuments NewEstimateWithActivityPage EstimateChecklistDialogLayout NewEstimateWithActivityPropertyLabel NewEstimateWithActivityRetry WorkItemsMobileColumns EstimateEditorTour tourRegistry DocumentsDialog && npm run typecheck && npm run lint`
Expected: all pass, and the typecheck and lint are clean. No references to `DocumentsBar` or `selectedDocVersion` should remain: `grep -rn "DocumentsBar\|selectedDocVersion" src tests` prints nothing.

- [ ] **Step 7: Verify in the browser**

Start the portal dev server with `preview_start` (add a `portal` entry to `.claude/launch.json` if one is missing: `npm run dev` in `portal/`), with the platform running locally against Dev. Open an estimate and check:
- "Documents (N)" shows the right count.
- The dialog lists the versions, and each link opens in a new tab.
- Delete confirmation stacks on top of the dialog.
- At phone width (`resize_window` preset `mobile`), the dialog becomes a bottom sheet.

Take a screenshot as proof. Generating a doc here exercises the live Drive; do it once, and delete the test version afterward.

- [ ] **Step 8: Commit (portal, after approval)**

```bash
git -C portal add -A src/components/estimates src/pages/NewEstimateWithActivityPage.tsx src/tours/registry.ts tests
git -C portal commit -m "feat: replace the Documents dropdown with a Documents dialog

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 9: Maple files estimate notes in the Notes feed (platform)

The spec calls this D9 / Section 4 (Option C). "Add a note to the estimate" must create an estimate-level `Note` and never write `Estimate.notes`. A "set/replace the notes" phrasing adds a note too. Notes skip the Draft/Review edit lock, per the Notes system rule that an estimate's status never gates notes.

**Files:**
- Modify: `platform/agents/estimate/crud_handlers.py`:
  - module docstring (line ~14)
  - `_load_estimate_for_update` (line ~869) gains `enforce_edit_lock: bool = True`
  - the notes branch of `_handle_update_estimate` (line ~2521)
  - replace `_handle_update_estimate_notes` (line ~2871) with `_handle_add_estimate_note`
  - imports
- Test: `platform/tests/test_maple_estimate_field_edits.py` (`TestNotesByTitle`, plus a new `TestEstimateNotesGoToFeed`) and `platform/tests/test_estimate_agent.py` (the locked-status tests)

**Interfaces:**
- Consumes: `services.notes.create_note_as(*, company, parent_type, parent_id, body, author_email, author_name) -> Note`, `models.note.NoteParentType.ESTIMATE`, and `agents.text_utils.NOTE_SAVE_NO_AUTHOR_REASON` / `NOTE_SAVE_FAILED_REASON`.
- Produces: the result dict `{"operation": "add_estimate_note", "estimate_id": code, "note_id": str | None, "saved": bool}`. `finalize_result` still anchors `active_estimate_code` from the flat `estimate_id`, because only delete ops are skipped there.

- [ ] **Step 1: Write the failing tests**

In `platform/tests/test_maple_estimate_field_edits.py`, replace the whole `TestNotesByTitle` class with:

```python
class _NoteTarget:
    """An estimate the notes path must never write to."""
    id = "665f1f77bcf86cd799439075"
    estimate_id = "E0075"
    notes = "legacy memo"
    company = None

    async def set(self, update=None, **_kwargs):
        raise AssertionError("Maple must not write Estimate.notes")

    async def save(self):
        raise AssertionError("Maple must not write Estimate.notes")


def _capture_notes(monkeypatch, *, fail=False):
    from agents.estimate import crud_handlers

    created: list[dict] = []

    async def _create_note_as(**kwargs):
        if fail:
            raise RuntimeError("mongo down")
        created.append(kwargs)
        return type("N", (), {"id": "665f1f77bcf86cd7994390ee"})()

    monkeypatch.setattr(crud_handlers, "create_note_as", _create_note_as)
    return created


def _load_note_target(monkeypatch, agent, seen_kwargs=None):
    async def _load(query, company_id, code, context, **kwargs):
        if seen_kwargs is not None:
            seen_kwargs.update(kwargs)
        return _NoteTarget(), None

    monkeypatch.setattr(agent, "_load_estimate_for_update", _load)


_SIGNED_IN = {"current_user_email": "Sam@Example.com", "current_user_name": "Sam Lee"}


class TestNotesByTitle:
    def test_adds_note_resolving_estimate_by_title(self, monkeypatch):
        agent = _agent(monkeypatch)
        created = _capture_notes(monkeypatch)

        async def _by_title(query, company_id, context, probability):
            return type("E", (), {"estimate_id": "E0075"})()

        monkeypatch.setattr(agent, "_resolve_estimate_by_title", _by_title)
        _load_note_target(monkeypatch, agent)

        result = asyncio.run(agent._handle_update_estimate(
            'for estimate Spring Cleaning, add to the notes the following: "call before 9am"',
            "507f1f77bcf86cd799439011", dict(_SIGNED_IN),
        ))
        assert created[0]["body"] == "call before 9am"
        assert "E0075" in result["response"]


class TestEstimateNotesGoToFeed:
    def test_note_is_filed_on_the_estimate_feed(self, monkeypatch):
        from beanie import PydanticObjectId

        from models.note import NoteParentType

        agent = _agent(monkeypatch)
        created = _capture_notes(monkeypatch)
        seen: dict = {}
        _load_note_target(monkeypatch, agent, seen)

        result = asyncio.run(agent._handle_update_estimate(
            'add a note to E0075: "call before 9am"', "507f1f77bcf86cd799439011", dict(_SIGNED_IN),
        ))

        assert len(created) == 1
        note = created[0]
        assert note["parent_type"] == NoteParentType.ESTIMATE
        assert note["parent_id"] == PydanticObjectId(_NoteTarget.id)
        assert note["company"] == PydanticObjectId("507f1f77bcf86cd799439011")
        assert note["body"] == "call before 9am"
        assert note["author_email"] == "sam@example.com"
        assert note["author_name"] == "Sam Lee"
        assert seen == {"enforce_edit_lock": False}
        assert "I've added a note to estimate E0075" in result["response"]
        assert "call before 9am" in result["response"]
        assert result["result"]["operation"] == "add_estimate_note"
        assert result["result"]["saved"] is True

    def test_replace_phrasing_adds_a_note_instead(self, monkeypatch):
        agent = _agent(monkeypatch)
        created = _capture_notes(monkeypatch)
        _load_note_target(monkeypatch, agent)
        asyncio.run(agent._handle_update_estimate(
            'replace the notes on E0075 with "gate code 4321"', "507f1f77bcf86cd799439011", dict(_SIGNED_IN),
        ))
        assert [n["body"] for n in created] == ["gate code 4321"]

    def test_no_signed_in_user_skips_the_note_and_says_why(self, monkeypatch):
        from agents.text_utils import NOTE_SAVE_NO_AUTHOR_REASON

        agent = _agent(monkeypatch)
        created = _capture_notes(monkeypatch)
        _load_note_target(monkeypatch, agent)
        result = asyncio.run(agent._handle_update_estimate(
            'add a note to E0075: "call before 9am"', "507f1f77bcf86cd799439011", {},
        ))
        assert created == []
        assert NOTE_SAVE_NO_AUTHOR_REASON in result["response"]
        assert result["success"] is False
        assert result["result"]["saved"] is False

    def test_save_failure_is_reported_not_raised(self, monkeypatch):
        from agents.text_utils import NOTE_SAVE_FAILED_REASON

        agent = _agent(monkeypatch)
        _capture_notes(monkeypatch, fail=True)
        _load_note_target(monkeypatch, agent)
        result = asyncio.run(agent._handle_update_estimate(
            'add a note to E0075: "call before 9am"', "507f1f77bcf86cd799439011", dict(_SIGNED_IN),
        ))
        assert NOTE_SAVE_FAILED_REASON in result["response"]
        assert "mongo down" not in result["response"]
        assert result["success"] is False
```

(If `_handle_update_estimate` needs more context keys to reach the notes branch, copy them from the old `TestNotesByTitle`, which passed `{}`. Its signature is `(query, company_id, context)`.)

In `platform/tests/test_estimate_agent.py`:
- The lock tests currently use a note as their edit probe: `test_locked_estimate_archived_refuses_notes_edit`, `test_locked_estimate_sent_refuses_notes_edit`, `test_locked_estimate_other_statuses_refuse_notes_edit` and `test_locked_estimate_review_reachable_statuses_suggest_review`. In each, replace the query `'add a note to E0039: "call customer before Monday"'` with `'set the description of E0039 to "Full backyard rebuild"'`. Rename `_notes_edit` to `_description_edit` in the first three names. Keep every assertion; the lock must still hold for description edits. If the description detector doesn't claim that phrasing, use the quoted form the existing `update_estimate_description` tests use.
- Replace `test_editable_estimate_notes_edit_still_works` with:

```python
@pytest.mark.parametrize("status", ["Draft", "Review", "Sent", "Won", "Archived"])
def test_estimate_notes_ignore_the_edit_lock(monkeypatch, status):
    """Notes are commentary, not estimate content: any status takes one, and
    Estimate.notes itself is never written (2026-09-23, Option C)."""
    from agents.estimate import crud_handlers

    target, save_calls = _patch_estimate_for_locked_edit(monkeypatch, status=status)
    created = []

    async def _create_note_as(**kwargs):
        created.append(kwargs)
        return type("N", (), {"id": "665f1f77bcf86cd7994390ef"})()

    monkeypatch.setattr(crud_handlers, "create_note_as", _create_note_as)

    agent = _build_agent(monkeypatch)
    result = asyncio.run(
        agent.process(
            'add a note to E0039: "call customer before Monday"',
            context={
                "company_id": "507f1f77bcf86cd799439011",
                "orchestrator_intent": "update_estimate",
                "orchestrator_confidence": 0.9,
                "current_user_email": "sam@example.com",
                "current_user_name": "Sam Lee",
            },
        )
    )

    assert result["success"] is True
    assert [n["body"] for n in created] == ["call customer before Monday"]
    assert save_calls["count"] == 0
    assert target.notes == "existing memo"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py tests/test_estimate_agent.py -q -k "Notes or notes or locked"`
Expected: FAIL. The note tests fail with `AttributeError: ... has no attribute 'create_note_as'` or `AssertionError: Maple must not write Estimate.notes`, and `test_estimate_notes_ignore_the_edit_lock[Sent]` and friends get the lock refusal. The renamed description-lock tests should already pass.

- [ ] **Step 3: Implement**

In `crud_handlers.py`:

Imports: add `from models.note import NoteParentType` and `from services.notes import create_note_as`. Also import `NOTE_SAVE_FAILED_REASON` and `NOTE_SAVE_NO_AUTHOR_REASON` in the existing `from agents.text_utils import (...)` block. If `services.notes` turns out to import from `agents.estimate` (a circular import), move the `create_note_as` import to module level with `# noqa: E402` and a one-line reason, or do it inside the handler. The monkeypatch target must stay the module attribute `crud_handlers.create_note_as` either way.

`_load_estimate_for_update`: add the keyword parameter `enforce_edit_lock: bool = True`, and gate the lock:

```python
        if enforce_edit_lock:
            locked = self._locked_status_edit_refusal(query, context, code, target)
            if locked is not None:
                return None, locked
```

Add one docstring line: `enforce_edit_lock=False is for notes only — the Notes system never lets an estimate's status gate a note.`

In `_handle_update_estimate`'s notes branch:

```python
        note_op = self._detect_note_update(query)
        if note_op is not None:
            note_value, _mode = note_op  # a feed has nothing to overwrite; "set" adds too
            return await self._handle_add_estimate_note(query, company_id, context, note_value)
```

Replace `_handle_update_estimate_notes` in full with:

```python
    async def _handle_add_estimate_note(
        self,
        query: str,
        company_id: str,
        context: Dict[str, Any],
        note_value: str,
    ) -> Dict[str, Any]:
        """File *note_value* as a Note on the estimate's Notes feed.

        Since 2026-09-23 Maple never writes ``Estimate.notes``: that field no
        longer prints, and what prints on the customer's document is the
        Documents dialog's Additional Information, which Maple does not touch.
        Like every note, this ignores the Draft/Review edit lock.
        """
        probability = float(context.get("orchestrator_confidence") or 0.9)
        code, envelope = await self._resolve_update_estimate_code(
            query, company_id, context,
            response=(
                "Which estimate should I add the note to? Please share the "
                "estimate code (e.g. E0042) or its title."
            ),
        )
        if envelope is not None:
            return envelope

        target, err = await self._load_estimate_for_update(
            query, company_id, code, context, enforce_edit_lock=False,
        )
        if err is not None:
            return err

        body = note_value.strip()
        author_email = _safe_str(context.get("current_user_email")).strip().lower()
        failure_reason: Optional[str] = None
        note_id: Optional[str] = None
        if not author_email:
            # author_email is the note's edit-authorization key: without a
            # signed-in user there is nobody honest to attribute it to.
            failure_reason = NOTE_SAVE_NO_AUTHOR_REASON
        else:
            try:
                note = await create_note_as(
                    company=self._coerce_company_oid(company_id) or target.company,
                    parent_type=NoteParentType.ESTIMATE,
                    parent_id=PydanticObjectId(_safe_str(target.id)),
                    body=body,
                    author_email=author_email,
                    author_name=_safe_str(context.get("current_user_name")),
                )
                note_id = _safe_str(note.id)
            except Exception:
                # `.warning` without exc_info: Sentry attaches frame locals,
                # and this frame holds the note body and the author's email.
                logger.warning("Estimate agent could not save a note on estimate %s", code)
                failure_reason = NOTE_SAVE_FAILED_REASON

        if failure_reason is not None:
            envelope = self._crud_envelope(
                query=query,
                intent="update_estimate",
                probability=probability,
                response=f"I wasn't able to add that note to estimate {code} — {failure_reason}.",
                result={"operation": "add_estimate_note", "estimate_id": code, "note_id": None, "saved": False},
                context=context,
            )
            envelope["success"] = False
            return envelope

        return self._crud_envelope(
            query=query,
            intent="update_estimate",
            probability=probability,
            response=f"I've added a note to estimate {code} for you:\n{body}",
            result={"operation": "add_estimate_note", "estimate_id": code, "note_id": note_id, "saved": True},
            context=context,
        )
```

(Import `PydanticObjectId` from `beanie` if the module doesn't already have it. `_coerce_company_oid` returns `Optional[PydanticObjectId]`. If mypy objects to the `or target.company` fallback's type, annotate `target` as `Any`, which is what `_load_estimate_for_update` already returns.)

Update the module docstring bullet at line ~14 from `_handle_update_estimate_notes — set / append on the notes …` to `_handle_add_estimate_note — files a Note on the estimate's Notes feed (never Estimate.notes)`.

Then find anything else that dispatches on the old name or operation:

```bash
grep -rn "_handle_update_estimate_notes\|update_estimate_notes" agents routers services
```

Update every hit to the new name and operation, except for literal test fixtures in `tests/test_agent_helpers_finalize_result.py`. Those only exercise the flat-`estimate_id` anchor and stay valid.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd platform && ./run_tests.sh tests/test_maple_estimate_field_edits.py tests/test_estimate_agent.py tests/test_agent_helpers_finalize_result.py tests/test_maple_crud_coverage.py -q`
Expected: all pass. If a `test_maple_crud_coverage.py` row expected the old "updated the notes" copy, update that expectation to the new response and note the row for the phrasing-reference update in Task 10.

- [ ] **Step 5: Run the gates**

Run: `cd platform && ./run_mypy.sh agents/estimate && ./run_ruff.sh agents/estimate tests/test_maple_estimate_field_edits.py tests/test_estimate_agent.py && ./run_bandit.sh agents/estimate`
Expected: clean. The B110 count stays at 11, because the new `except` logs.

- [ ] **Step 6: Commit (platform, after approval)**

```bash
git -C platform add agents/estimate/crud_handlers.py tests/test_maple_estimate_field_edits.py tests/test_estimate_agent.py
git -C platform commit -m "feat: file Maple's estimate notes in the Notes feed

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 10: Documentation (platform, root, documentation)

**Files:**
- Modify: `CLAUDE.md` (root repo), Notes system item 6
- Modify: `platform/user_guides/users_guide.md` (lines ~339, ~655–658, ~884–885). This file is also what Maple answers help questions from, so its wording is user-facing twice.
- Modify: `documentation/development/plans/2026-09-17-notes-design.md` (D1 cross-reference)
- Modify: `documentation/development/maple-phrasing-reference.md`
- Modify: `documentation/development/plans/2026-09-23-estimate-documents-dialog-design.md` (Status line)

- [ ] **Step 1: CLAUDE.md**

In "Notes system", item 6, replace the sentence starting "It still prints on the customer's Google Doc as the `NOTES` section" through "so it is a live field, not a leftover." with the block below. In item 4, add "Maple's estimate agent" to the list of `create_note_as` callers.

```markdown
   **As of 2026-09-23 it has no writer and no printed reader** — legacy
   data only. `{{NOTES}}` is filled from the **Additional Information** box in
   the estimate page's Documents dialog (stored per version as
   `GoogleDocsVersion.additional_info`, `--` when blank), and Maple's "add a
   note to the estimate" files a real estimate-level `Note` via
   `_handle_add_estimate_note` in `agents/estimate/crud_handlers.py` — which,
   like every note, ignores the Draft/Review edit lock. Maple cannot touch
   Additional Information. Estimate details still render a non-empty legacy
   value. See [`2026-09-23-estimate-documents-dialog-design.md`](documentation/development/plans/2026-09-23-estimate-documents-dialog-design.md).
```

- [ ] **Step 2: User guide**

In `platform/user_guides/users_guide.md`:
- Replace the **Documents** bullet (~655–658) with:

```markdown
- **Documents** — a **Documents (N)** button that opens the Documents
  dialog. It lists every generated version (click one to open that Google
  Doc in a new tab, or delete it), and below the list, generates a new one:
  type **Additional information** for the Notes section (left blank, it
  prints "--") and add up to 10 photos (JPEG, PNG, WebP or GIF, up to 10 MB
  each), which are placed right after the Notes section. The next time you
  open it, the text and photos from your latest version are already filled
  in. Any unsaved edits are auto-saved before a new version is generated.
```

- Replace step 8 (~884–885) with:

```markdown
8. **Generate a Document** — Click **Documents** and use the dialog: add any
   **Additional information** and photos for your customer, then click
   **Generate document** to create a Google Doc in your company's Drive
   folder. Each generation creates a new version (v1, v2, v3, …); earlier
   versions are listed in the same dialog to open or delete. Any unsaved
   edits are auto-saved first. Open the Doc or download it as a PDF to send
   to your customer. If you want to directly edit the Google Doc, we
   recommend that you save it to your own non-3Maples Google Drive and edit
   it there.
```

- Replace the Maple **Notes** bullet (~339) with:

```markdown
  - **Notes** — "add a note to the Henderson estimate: gate code is 4321". Casual phrasings work too — "jot this down…", "FYI…", or "remember that…". These go into the estimate's **Notes** feed (section 9.6), attributed to you, alongside the notes your team adds on the estimate page. They do **not** print on the customer document — what prints in its Notes section is the **Additional information** you type in the Documents dialog, which Maple doesn't change.
```

- [ ] **Step 3: Maple phrasing reference**

`CLAUDE.md` requires this in the same change. In `documentation/development/maple-phrasing-reference.md`:
- Bump "Last updated" to the implementation date.
- Add a dated wave entry at the top of the change log: *"Estimate notes → Notes feed (Option C): every estimate note phrasing (add / append / jot / FYI / remember / set / replace) now files an estimate-level Note via `_handle_add_estimate_note`; nothing writes `Estimate.notes`. Set/replace phrasings add rather than overwrite. Notes ignore the Draft/Review lock; the lock tests now probe with a description edit. Tests: `TestEstimateNotesGoToFeed`, `test_estimate_notes_ignore_the_edit_lock`."*
- In the estimate notes rows, update the described behavior. Every tag stays ✅, because these phrasings still work.
- If Task 9, Step 4 changed any `test_maple_crud_coverage.py` expectation, refresh the §12.3 counts from `tests/reports/maple_crud_gap_report.md`.

- [ ] **Step 4: Notes design and spec status**

In `2026-09-17-notes-design.md`, under decision D1, append: `Superseded for printing on 2026-09-23: {{NOTES}} now comes from the Documents dialog's Additional Information — see 2026-09-23-estimate-documents-dialog-design.md.`

In the dialog spec, change the Status line to `**Status:** Implemented 2026-09-XX (plan: 2026-09-23-estimate-documents-dialog-plan.md)`, using the actual date.

- [ ] **Step 5: Commit each repo (after approval)**

```bash
git add CLAUDE.md && git commit -m "docs: record that Estimate.notes no longer prints on the doc

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git -C platform add user_guides/users_guide.md && git -C platform commit -m "docs: describe the Documents dialog in the user guide

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git -C documentation add development/plans development/maple-phrasing-reference.md && git -C documentation commit -m "docs: cross-reference the Documents dialog; Maple estimate notes go to the feed

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Task 11: End-to-end check against the real Google Docs API on Dev

Unit tests fake Google and Firebase Storage. Three behaviors can only be proven against the real services, and the spec's Risks section depends on them.

- [ ] **Step 1:** With the platform running locally against Dev (`uvicorn main:app --reload`) and the portal dev server up, open a Dev estimate. Generate a version with two lines of Additional Information and three photos (one landscape, one portrait phone photo, one tall portrait image such as a phone screenshot).
- [ ] **Step 2:** Open the generated Doc and confirm:
  - (a) The NOTES text is present, and each image sits on its own line directly **below** the notes text, in the order picked. This proves that `replaceAllText` turns `\n` into a new paragraph. If the images sit inline on the notes line instead, report it: the fix is to find the `{{NOTES}}` paragraph's end index instead of using the marker's own paragraph.
  - (b) No `{{NOTES_IMAGES}}` text is left anywhere.
  - (c) The portrait photo is upright and at most page width.
  - (d) The tall portrait image (the phone screenshot) fits on one page and is not clipped.
  - (e) The multi-line Additional Information prints as separate lines with no extra blank lines between them.
- [ ] **Step 3:** Confirm signing worked. `platform` logs show no `Failed to sign estimate doc image URLs`. If it failed with a missing-private-key error, the credentials in that environment can't sign V4 URLs. Report it; do not work around it silently.
- [ ] **Step 4:** Reopen Documents. The text and both photos are prefilled. Remove one photo, add another, and generate v2. Then delete v1, and in the Firebase console confirm that the blob shared with v2 still exists. Delete v2 and confirm both of its blobs are gone.
- [ ] **Step 5:** Record the outcome of Steps 2–4 in `documentation/development/notes.md` (date, estimate id, pass/fail per check).

---

## Decision log

- **2026-09-23: Option C for Maple estimate notes.** Maple files estimate notes in the Notes feed and never touches what prints (Task 9). Rejected: A, where Maple's notes would be silently unprinted and invisible, and B, which would prefill Additional Information from `Estimate.notes` and let Maple keep a back door into the document.
