# Dynamic Navigation

## What it does
Serves the product-driven navigation menu — the part of the site header populated from Firestore
category data (not from Sitecore XM Cloud). The `ProductsDynamicNavigationApi` reads category
hierarchies and routing data from Firestore and returns them to the Next.js frontend via the
`/navigation-settings/` API route group.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.ProductsDynamicNavigationApi` | Reads Firestore categories, returns nav tree |
| Next.js routes | `/api/navigation-settings/` | BFF proxy to NavigationApi |
| Feature package | `@grohe/header` | Renders dynamic nav in the site header |
| Firestore | `PLCategory` | Category hierarchy per locale |
| Firestore | `CategoryRouting` | URL routing data for categories |
| Firestore | `cacheEntries` / `cacheRegions` | Response caching (in-service) |

## Data Flow

```
Browser (header component)
    → GET /api/navigation-settings/...  (Next.js BFF)
        → GET ProductsDynamicNavigationApi
            → read PLCategory + CategoryRouting from Firestore
            → assemble nav tree
            → cache response (Memory backend in integration tests)
            → return JSON nav structure
```

## Key Business Logic

- **Multi-tenant Firestore:** `ITenantContext` + `FirestoreDbResolver` resolve the correct
  Firestore database per locale/tenant at request time (reads `configuration` Firestore doc at startup).
- **Configuration seeding required:** `FirebaseConfigurationService` reads `configuration/config`
  doc at startup. Missing doc → `KeyNotFoundException` on `configurationDictionary["project_id"]`.
  Run `scripts/seed_config.py` before starting the container.
- **Blue-green aware:** reads the active database from config, so it always uses the current live DB.
- **Caching:** response cache uses Memory backend (Firestore cache disabled in integration tests
  via `appsettings.Integration.json: Cache: Backend: Memory`).
- **EmulatorDetection required:** both `FirebaseConfigurationService` (config bootstrap) and
  `FireStoreDbResolver.cs` (per-request resolver) must have
  `builder.EmulatorDetection = EmulatorDetection.EmulatorOrProduction`.

## Data Models

### Category document (`PLCategory`)
Category hierarchy with locale, parent/child relationships, URLs, display names.
Exact field shape: read `PLCategory` output model in data-loader `output_models/`.

### CategoryRouting document
Maps category IDs to URL slugs for navigation routing.

### Navigation response (API output)
JSON nav tree with nested categories, display names, URLs. Structure mirrors the header
component's TypeScript types in `@grohe/header`.

## Integration Tests

**Phase 4 navigation (5 tests, ~60s):** `tests/services/navigation/` — NavigationApi in Docker,
Firestore emulator seeded with categories from Phase 1 ETL data.

```bash
# Seed config first (required):
FIRESTORE_EMULATOR_HOST=localhost:8080 .venv/Scripts/python.exe scripts/seed_config.py

# Start Phase 4 containers (NavigationApi port 8083 + ProductsApi port 8084):
docker compose -f C:/projects/grohe/NEO/integration/docker-compose.yml --profile phase4 up -d

cd C:/projects/grohe/NEO/integration
.venv/Scripts/python.exe -m pytest tests/services/navigation/ -v
```

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.ProductsDynamicNavigationApi/Controllers/` | API endpoints, request handling |
| `grohe-neo-services/src/GroheNeo.ProductsDynamicNavigationApi/FireStoreDbResolver.cs` | Multi-tenant DB resolver (EmulatorDetection fix here) |
| `grohe-neo-services/src/GroheNeo.ProductsDynamicNavigationApi/appsettings.Integration.json` | Test config |
| `grohe-neo-services/src/GroheNeoProductDataCommon/FirebaseConfigurationService.cs` | Startup config reader (EmulatorDetection fix here) |
| `grohe-neo-services/src/GroheNeoProductDataCommon/` | Shared multi-tenant resolver, `ITenantContext` |
| `grohe-neo-data-loader/output_models/` | `PLCategory`, `CategoryRouting` model definitions |
| `grohe-neo-websites/packages/features/header/` | Frontend consumption of nav data |
| `integration/tests/services/navigation/` | Phase 4 nav integration tests |

## Known Issues & Gotchas

- **EmulatorDetection in two places:** both `FirebaseConfigurationService.cs` (reads config at
  startup) and `FireStoreDbResolver.cs` (per-request DB resolver) need the fix — missing either
  causes `InvalidOperationException: Your default credentials were not found`.
- **seed_config.py must run before containers start:** NavigationApi reads the config doc at
  startup. If the doc is missing, the service crashes on first request with `KeyNotFoundException`.
  `make infra-phase4-up` does this automatically.
- **Cache Backend: Memory:** integration tests set `Cache: Backend: Memory` in
  `appsettings.Integration.json` to avoid writing to Firestore `cacheEntries`/`cacheRegions`.
- **Port:** NavigationApi=8083, ProductsApi=8084 (both in phase4 profile).

## Common Ticket Patterns

- **Adding a nav field from Firestore:** update `PLCategory` output model in data-loader, update
  transformer, update the navigation API response mapper, update frontend types in `@grohe/header`.
- **Changing URL routing logic:** update `CategoryRouting` model + navigation controller mapper.
- **Cache tuning:** change cache TTL in `appsettings.json` → `Cache` section.
- **Multi-tenant changes:** update `ITenantContext` + `FirestoreDbResolver` in `GroheNeoProductDataCommon`.
