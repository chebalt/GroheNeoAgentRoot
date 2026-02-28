# Data Loader

## What it does
Cloud Run Job that downloads product CSV batches from Google Drive, runs ETL into Firestore,
and then syncs changes to the Sitecore Search index queue. Runs per-locale (en_gb, de_de, nl_nl)
with blue-green Firestore database switching for zero-downtime updates.

## Architecture

| Layer | Component | Role |
|---|---|---|
| Cloud Run Job | `grohe-neo-data-loader` | Python 3.13 ETL job, orchestrated by `entrypoint.sh` |
| Firestore | `PLProductContent`, `PLCategory`, `PLVariant`, `CategoryRouting`, `ProductIndexData` | Product data store (5 output collections) |
| Firestore | `products-index-updates` | Change queue consumed by IndexingApi |
| External | Google Drive | Source of product CSV batches (auto-detects latest by folder) |
| External | Firestore config DB | Env-specific config: `grohe-neo-product-{env}-conf` |
| External | `CLEAR_CACHE_URL` | HTTP GET called after ETL completes (cache busting) |

## Data Flow

```
Google Drive (CSV batches, per market/locale)
    ↓  entrypoint.sh reads Firestore config DB
    ↓  resolves blue-green target (opposite of current DB)
    ↓  downloads CSV batch from Drive
    ↓  pre-validation.py (header validation)
    ↓  main.py --to-firestore (extract → transform → load to inactive DB)
    ↓  config DB updated to point to new DB
    ↓  sync_product_index.py (ProductIndexData → products-index-updates)
    ↓  CLEAR_CACHE_URL called
    ↓  summary report uploaded to Drive
```

## Key Business Logic

- **Blue-green switching:** Config DB stores `database_en_gb: "products-en-gb-blue"`. ETL loads
  to the opposite color, then config is atomically updated. Previous DB retained for instant rollback.
- **Locale-scoped runs:** `ENV` var (QA/UAT/PROD) + `LOCALE` var (en_gb/de_de/nl_nl) scope the run.
  `BATCH_FOLDER` optionally overrides the Drive folder to use.
- **Change detection in sync:** SHA256 hash comparison between `ProductIndexData` (main DB) and
  `products-index-updates` (sync DB). Only generates UPDATE/DELETE docs for changed records.
- **5 output models** from `FILE_MODEL_MAP` in `extractor.py`: `PLProductContent`, `PLCategory`,
  `PLVariant`, `ProductIndexData`, `CategoryRouting`.
- **Pre-validation:** Header-only by default — fast. Full row validation optional.
- **Firestore batched writes:** `firestore_loader.py` writes in batches; prints emoji → requires
  `PYTHONUTF8=1` on Windows to avoid `UnicodeEncodeError`.

## Data Models

### Sync doc in `products-index-updates`
```
{
  data: { document: { fields, id, locale } },
  finished: false,                     // set true by Sitecore crawler after processing
  operation: "Update" | "Delete",
  identifier: <string>,
  culture: <string>,
  domain_id: <string>,
  content_hash: <sha256>
}
```

### Config DB doc (`configuration/config`)
```
{
  project_id: "grohe-neo-product-...",
  database_en_gb: "products-en-gb-blue",   // or "-green"
  database_de_de: "products-de-de-blue",
  fallback_locale: "en_gb"
}
```

## Integration Tests

**Phase 1 (44 tests, ~10–11 min):** `tests/pipeline/` — runs full ETL against Firestore emulator,
asserts documents in `PLProductContent`, `PLCategory`, `PLVariant`, `CategoryRouting`.

**Phase 2 (7 tests, ~15s):** `tests/sync/` — seeds controlled `ProductIndexData` docs, runs
`sync_product_index.py --use-emulator`, asserts `products-index-updates` docs.

```bash
# Infra (Firestore emulator + WireMock):
docker compose -f C:/projects/grohe/NEO/integration/docker-compose.yml up -d
cd C:/projects/grohe/NEO/integration

# Phase 1
.venv/Scripts/python.exe -m pytest tests/pipeline/ -v

# Phase 2
.venv/Scripts/python.exe -m pytest tests/sync/ -v
```

**Sync test design notes:**
- Both main and sync use `(default)` Firestore DB — named DBs not supported by gcloud emulator.
- Tests use unrealistic BaseSKUs (10000–40000) to avoid colliding with Phase 1 fixture data.
- Sync tests run alphabetically after pipeline tests, so clearing `ProductIndexData` after Phase 1 is safe.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-data-loader/entrypoint.sh` | Overall orchestration, env vars, blue-green logic |
| `grohe-neo-data-loader/main.py` | CLI entry: extract → transform → load |
| `grohe-neo-data-loader/extractor.py` | `FILE_MODEL_MAP`, CSV reading, Pydantic validation |
| `grohe-neo-data-loader/transformer.py` | Denormalization to 5 output models |
| `grohe-neo-data-loader/firestore_loader.py` | Batch Firestore writes |
| `grohe-neo-data-loader/sync_product_index.py` | Hash-based change detection + queue writing |
| `grohe-neo-data-loader/output_models/` | All 5 Pydantic output model definitions |
| `grohe-neo-data-loader/google_drive_handler.py` | Drive download/upload |

## Known Issues & Gotchas

- **Windows encoding:** `firestore_loader.py` prints emoji. On Windows cp1252 this crashes the
  subprocess. Fix: `PYTHONUTF8=1` env var + `encoding="utf-8"` in `subprocess.run()`.
  Both must be set in `integration/tests/conftest.py` — if either is missing: `UnicodeEncodeError`
  or `stdout=None` in test output.
- **Named Firestore databases not supported by emulator:** sync tests use `(default)` for both DBs.
- **Blue-green target:** always the opposite of the current DB color in config. If config is missing,
  the job fails immediately.

## Common Ticket Patterns

- **Adding a new CSV field:** add to Pydantic model in `extractor.py`, update transformer, update
  the Firestore output model, update integration test assertions.
- **Adding a new output collection:** add to `FILE_MODEL_MAP`, add Firestore model, add
  `firestore_loader.py` batch call, add Phase 1 integration test file.
- **Locale changes:** update `entrypoint.sh` locale list and any locale-specific transformer logic.
- **Sync logic changes:** update `sync_product_index.py`, update Phase 2 test fixtures and assertions.
