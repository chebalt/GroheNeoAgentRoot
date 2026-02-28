# Product Indexing

## What it does
Keeps the Sitecore Search index in sync with Firestore product data. The IndexingApi (triggered by
Workato on a schedule) reads a Firestore change queue, maps records to Sitecore Search document format,
POSTs to the Sitecore Search Ingestion API, then triggers Vercel cache revalidation. A SynchronizationJob
separately copies product change records to an XM Cloud-specific queue.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.IndexingApi` | Reads `products-index-updates`, posts to Sitecore Search, revalidates Vercel |
| .NET job | `GroheNeo.SynchronizationJob` | Copies `products-index-updates` → `xmcloud-index-updates` |
| .NET job | `GroheNeo.StoreLocatorJob` | Syncs store locations → `stores-index-updates` (same pattern) |
| Firestore | `products-index-updates` | Change queue: `{operation: UPDATE/DELETE, finished: false}` |
| Firestore | `xmcloud-index-updates` | XM Cloud mirror of the same queue |
| External | Sitecore Search Ingestion API | `https://discover-euc1.sitecorecloud.io/ingestion/v1` |
| External | Sitecore Edge GraphQL | `https://edge.sitecorecloud.io/api/graphql/v1` |
| External | Vercel | Cache revalidation after indexing |
| External | Workato | Scheduler — triggers IndexingApi via HTTP |

## Data Flow

```
Workato (scheduled)
    → GET /v1/indexing/products/initialize  (IndexingApi)
        → read products-index-updates (finished=false) from Firestore
        → map each doc to Sitecore Search document format
        → POST to https://discover-euc1.sitecorecloud.io/ingestion/v1
        → mark docs finished=true in Firestore
        → POST to Vercel revalidation endpoint
```

## Key Business Logic

- **Workato-triggered:** IndexingApi is NOT a continuously running service — Workato calls
  `GET /v1/indexing/products/initialize` on a schedule.
- **Batch processing:** reads all `finished=false` docs, processes in batch, marks `finished=true`.
- **Document mapping:** `products-index-updates` doc shape → Sitecore Search document schema.
  Locale-aware: each doc carries `culture` and `domain_id`.
- **UPDATE vs DELETE operations:** `operation` field in the Firestore doc determines whether the
  record is upserted or deleted from the search index.
- **Vercel revalidation:** after indexing, the API calls Vercel to bust ISR cache for affected pages.
- **SynchronizationJob:** runs separately (also Workato-triggered), copies product docs to
  `xmcloud-index-updates` so XM Cloud can also consume the same change feed.
- **EmulatorDetection required:** `FirestoreDataStorageService.cs:54` must have
  `builder.EmulatorDetection = EmulatorDetection.EmulatorOrProduction` — without this, the .NET
  SDK ignores `FIRESTORE_EMULATOR_HOST` and throws `InvalidOperationException` at startup.

## Data Models

### `products-index-updates` document
```
{
  data: { document: { fields: {...}, id, locale } },
  finished: false,
  operation: "Update" | "Delete",
  identifier: <string>,
  culture: <locale string>,
  domain_id: <string>,
  content_hash: <sha256>
}
```

### Sitecore Search Ingestion payload
```
POST https://discover-euc1.sitecorecloud.io/ingestion/v1
Content-Type: application/json
{
  documents: [{ id, locale, fields: { ... mapped product fields } }]
}
```

## Integration Tests

**Phase 3 (5 tests, ~30s):** `tests/indexing/` — IndexingApi runs in Docker, WireMock stubs
Sitecore Search Ingestion + Vercel. Tests seed `products-index-updates` docs, call the API,
assert WireMock received the ingestion POSTs and docs are marked `finished=true`.

```bash
# Build + start IndexingApi container (first build: ~5-10 min):
docker compose -f C:/projects/grohe/NEO/integration/docker-compose.yml --profile phase3 up -d

cd C:/projects/grohe/NEO/integration
.venv/Scripts/python.exe -m pytest tests/indexing/ -v
```

**WireMock stubs needed:** Sitecore Search Ingestion endpoint, Vercel revalidation endpoint.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.IndexingApi/Controllers/IndexingController.cs` | `GET /v1/indexing/products/initialize` handler |
| `grohe-neo-services/src/GroheNeo.IndexingApi/Services/` | Firestore reading, document mapping, ingestion posting |
| `grohe-neo-services/src/GroheNeo.IndexingApi/appsettings.Integration.json` | Local test config (WireMock URLs) |
| `grohe-neo-services/src/GroheNeo.Feature.SitecoreSearch/` | Ingestion + Discovery service wrappers |
| `grohe-neo-services/src/GroheNeo.Feature.Vercel/` | Vercel cache revalidation |
| `grohe-neo-services/src/GroheNeo.SynchronizationJob/` | XM Cloud sync job |
| `grohe-neo-data-loader/sync_product_index.py` | Upstream writer of `products-index-updates` |
| `integration/tests/indexing/` | Phase 3 integration tests |

## Known Issues & Gotchas

- **EmulatorDetection:** `FirestoreDataStorageService.cs` must have `EmulatorDetection.EmulatorOrProduction`
  or the service fails with `InvalidOperationException: Your default credentials were not found` when
  `FIRESTORE_EMULATOR_HOST` is set.
- **Git Bash path expansion:** `make wait-indexing-api` calls `--path /health` — Git Bash expands
  `/health` to `C:/Program Files/Git/health`. Tests call `_wait_for_indexing_api()` directly and
  are unaffected. Manual curl: `MSYS_NO_PATHCONV=1 curl http://localhost:8082/health`.
- **CrossApiServicesSettings.Integration.json:** must override `ApiServices.XmCloudApi.BaseAddress`
  to point to WireMock. File must be in csproj with `CopyToOutputDirectory: Always`.

## Common Ticket Patterns

- **Adding a new indexed field:** update the document mapper (fields from `PLProductContent` →
  Sitecore Search schema), update `products-index-updates` writer in `sync_product_index.py`.
- **Changing ingestion endpoint/format:** update `GroheNeo.Feature.SitecoreSearch` wrapper,
  update WireMock stub in Phase 3 tests.
- **Adding store indexing:** see `GroheNeo.StoreLocatorJob` — same pattern as product indexing
  but writes to `stores-index-updates`.
- **Triggering manual reindex:** call `GET /v1/indexing/products/initialize` directly on the
  running Cloud Run service (Workato webhook URL exposed).
