# Product Detail Page (PDP)

## What it does
Displays full product detail: images, descriptions, technical specs, variants (finish/size),
pricing, and related content. The ProductsApi reads from Firestore (multi-tenant, locale-scoped),
assembles the product view, and returns it to the Next.js frontend. Pricing is fetched separately
from PricingApi on the client side.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.ProductsApi` | Reads product data from Firestore, assembles PDP payload |
| Next.js routes | `/api/product/detail`, `/api/product/eco-configs` | BFF proxy to ProductsApi |
| Feature package | `@grohe/product` | `PDPMediaGallery`, `PDPProductMain`, `PDPAccordion` components |
| Firestore | `PLProductContent` | Full product content per locale |
| Firestore | `PLVariant` | Product variants (finish, size options) |
| Firestore | `cacheEntries` / `cacheRegions` | Response cache (in-service, Memory in tests) |
| External | XM Cloud | CMS content (descriptions, marketing copy) |
| External | PricingApi | Prices fetched separately (Hybris) |

## Data Flow

```
Browser (PDP page)
    → Next.js page (SSR/ISR)
        → GET /api/product/detail?sku=...&locale=...  (Next.js BFF)
            → ProductsApi
                → read PLProductContent from Firestore (multi-tenant DB)
                → read PLVariant from Firestore
                → optional XM Cloud enrichment
                → return product payload
    → (client-side) GET /api/product/pricing?sku=...&locale=...
        → PricingApi → Hybris
```

## Key Business Logic

- **Multi-tenant Firestore:** `ITenantContext` + `FirestoreDbResolver` resolve the active Firestore
  database for the requested locale. Config doc read at startup via `FirebaseConfigurationService`.
- **Blue-green aware:** reads the active DB name from config — always uses current live product data.
- **Variant resolution:** PLVariant docs link to the base product by SKU, allowing UI to render
  finish/size selectors and switch between variant pages.
- **Locale scoping:** all Firestore queries include locale as a filter/partition key.
- **Caching:** Memory backend in integration tests (`appsettings.Integration.json`); Firestore cache
  in production (`cacheEntries`/`cacheRegions` collections).
- **XM Cloud enrichment:** optional overlay of CMS content onto Firestore product data.
- **EmulatorDetection:** `FireStoreDbResolver.cs` in ProductsApi must have
  `builder.EmulatorDetection = EmulatorDetection.EmulatorOrProduction`.
- **Configuration seeding required:** `FirebaseConfigurationService` reads `configuration/config`
  at startup — missing doc causes `KeyNotFoundException`.

## Data Models

### `PLProductContent` document (key fields)
```
{
  BaseSKU: string,       // top-level product identifier
  locale: string,
  ProductName: string,
  Description: string,
  Features: [...],
  Media: [...],          // image URLs
  Category: string,
  CategoryPath: string,
  IsAccessory: bool,
  ...
}
```

### `PLVariant` document
```
{
  BaseSKU: string,       // parent product
  VariantSKU: string,   // this variant
  FinishCode: string,
  FinishName: string,
  SizeCode: string,
  SizeName: string,
  locale: string,
  ...
}
```

## Integration Tests

**Phase 4 products (5 tests, ~60s):** `tests/services/products/` — ProductsApi in Docker,
Firestore emulator seeded with ETL data from Phase 1.

```bash
# Seed config first (required):
FIRESTORE_EMULATOR_HOST=localhost:8080 .venv/Scripts/python.exe scripts/seed_config.py

# Start Phase 4 containers (NavigationApi port 8083 + ProductsApi port 8084):
docker compose -f C:/projects/grohe/NEO/integration/docker-compose.yml --profile phase4 up -d

cd C:/projects/grohe/NEO/integration
.venv/Scripts/python.exe -m pytest tests/services/products/ -v
```

**C# field name casing:** Models are PascalCase; ASP.NET Core serializes to camelCase.
Phase 4 tests check `body.get("sku") or body.get("SKU")` to handle both.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.ProductsApi/Controllers/` | API endpoints, request handling |
| `grohe-neo-services/src/GroheNeo.ProductsApi/FireStoreDbResolver.cs` | Multi-tenant DB resolver (EmulatorDetection fix) |
| `grohe-neo-services/src/GroheNeo.ProductsApi/appsettings.Integration.json` | Test config (Memory cache, WireMock URLs) |
| `grohe-neo-services/src/GroheNeoProductDataCommon/FirebaseConfigurationService.cs` | Startup config reader |
| `grohe-neo-services/src/GroheNeoProductDataCommon/` | Shared `ITenantContext`, `FirestoreDbResolver` |
| `grohe-neo-data-loader/output_models/` | `PLProductContent`, `PLVariant` model definitions |
| `grohe-neo-websites/packages/features/product/` | `PDPMediaGallery`, `PDPProductMain`, `PDPAccordion` |
| `integration/tests/services/products/` | Phase 4 product integration tests |

## Known Issues & Gotchas

- **EmulatorDetection in two places:** both `FirebaseConfigurationService.cs` and
  `FireStoreDbResolver.cs` must have the fix (see dynamic-navigation.md for detail).
- **seed_config.py must run before container starts:** ProductsApi reads config doc at startup.
  Missing doc → crash on first request. `make infra-phase4-up` does this automatically.
- **Phase 6 dependency:** ProjectListsApi calls ProductsApi directly (not via WireMock) to build
  PDF product details — both services must be running for Phase 6 PDF test.
- **Cache Backend: Memory** in integration test config — prevents Firestore writes during tests.
- **Pricing is separate:** PDP page loads price via a separate `/api/product/pricing` client-side
  call. ProductsApi does NOT return price.

## Common Ticket Patterns

- **Adding a new product field:** update `PLProductContent` in data-loader output models, update
  transformer, update ProductsApi response mapper, update frontend types in `@grohe/product`.
- **New variant attribute:** update `PLVariant` model, transformer, and variant mapper in ProductsApi.
- **XM Cloud CMS content change:** update Sitecore rendering or field binding — no Firestore change needed.
- **Cache TTL change:** update `appsettings.json` → `Cache` section in ProductsApi.
