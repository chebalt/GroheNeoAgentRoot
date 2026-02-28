# Project List

## What it does
Lets authenticated users save products into named project lists (wishlists for trade/professional
buyers), and export them as PDF specification documents. ProjectListsApi persists lists in Firestore,
calls ProductsApi directly for product detail, and generates PDFs via PuppeteerSharp + DotLiquid.
Dictionary strings are fetched from XM Cloud.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.ProjectListsApi` | CRUD for project lists + PDF generation |
| Next.js routes | `/api/project-lists/` | BFF proxy (CRUD + export-document) |
| Feature package | `@grohe/project-lists` | Project list UI |
| Firestore | `project-lists` collection | Stores project list docs (PascalCase fields) |
| External | ProductsApi | Fetches product details for PDF (direct service call) |
| External | XM Cloud | Dictionary strings for PDF labels |
| External | IDP (OpenID Connect) | JWT auth — `Authorization` header, `sub` claim = UserId |

## Data Flow

```
Browser (authenticated user)
    → CRUD: GET/POST/PUT/DELETE /api/project-lists/...  (Next.js BFF)
        → ProjectListsApi → Firestore (project-lists collection)

    → PDF export: POST /api/project-lists/export-document
        → ProjectListsApi
            → reads project-lists doc from Firestore
            → calls ProductsApi for each product's detail
            → calls XM Cloud for dictionary strings
            → generates PDF via PuppeteerSharp + DotLiquid
            → returns PDF bytes
```

## Key Business Logic

- **JWT auth:** `GetClaimValue()` strips "OndusBearer" prefix then calls `ReadJwtToken()` (no RSA
  signature check). `sub` claim = `UserId`. Tests send raw JWT (no "Bearer " prefix) as
  `Authorization` header value.
- **UserId scoping:** all project list operations scope by `UserId` from JWT — users can only
  see/edit their own lists.
- **Multi-DB Firestore:** ProjectListsApi uses `DependencyInjectionExtensions.cs` with
  `EmulatorDetection.EmulatorOrProduction` on both `FirestoreDbBuilder` instances.
- **ProductsApi direct call:** PDF generation calls real ProductsApi (not WireMock) in Phase 6
  integration tests. ProjectListsApi `ProductApiBaseUrl=http://products-api:8080`.
- **XM Cloud:** only for dictionary strings in PDF. WireMock stubs: IDP token + GraphQL endpoint
  + API key endpoint.
- **ETL data required for PDF:** the PDF test (test 10) uses real PLProductContent docs
  (SKU `1039960000`, locale `de-DE`) — run Phase 1 ETL or `make test-pipeline` first.
- **`ConfigurationXmCloud` ValidateOnStart:** requires non-empty `EnvironmentId`, `EdgeClientId`,
  `EdgeClientSecret`, `AutomationClientId`, `AutomationClientSecret` — dummy values in
  `appsettings.Integration.json`.
- **`ITokenApi.GetToken()`** (GET /tokenapi/token) is NOT called for authenticated requests —
  only for anonymous users.

## Data Models

### Firestore `project-lists` document (PascalCase fields)
```
{
  Id: string,                   // e.g. "integration-test-list-001"
  UserId: string,               // JWT sub claim
  ProjectListName: string,
  Items: [{
    BaseSKU: string,
    Quantity: int,
    ...
  }],
  CreatedTimestamp: Timestamp,  // must be DateTimeKind.Utc
  UpdatedTimestamp: Timestamp   // must be DateTimeKind.Utc
}
```

### PDF export request (`/api/project-lists/export-document`)
```
{
  projectListId: string,
  locale: string,
  specificationFormValues: {
    headline, description, language,
    coverImage, logoImage,
    reference,
    specifications: bool,
    include: string[],          // e.g. ["include_vat"]
    contactDetails: {...}
  },
  sustainabilitySection: {...}
}
```

## Integration Tests

**Phase 6 (10 tests, ~30–60s):** `tests/services/project-lists/` — CRUD + PDF.

```bash
# Seed config (required for ProductsApi):
FIRESTORE_EMULATOR_HOST=localhost:8080 .venv/Scripts/python.exe scripts/seed_config.py

# Start Phase 6 (ProjectListsApi port 8086 + ProductsApi port 8084):
docker compose -f C:/projects/grohe/NEO/integration/docker-compose.yml --profile phase6 up -d

# For PDF test (test 10): ETL data must already be in Firestore
# (run make test-pipeline first)

cd C:/projects/grohe/NEO/integration
FIRESTORE_EMULATOR_HOST=localhost:8080 PROJECT_LISTS_API_HOST=localhost:8086 \
  .venv/Scripts/python.exe -m pytest tests/services/project-lists/ -v
```

**WireMock stubs:** `fixtures/mocks/project-lists/` — IDP token, XMCloud GraphQL (returns empty
dict), XMCloud API key.
**Seeded fixtures:** `integration-test-list-001` (read/update/PDF) + `integration-test-list-002` (delete).
Test 9 deletes `integration-test-list-002`; test 10 generates PDF for `integration-test-list-001`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.ProjectListsApi/Controllers/ProjectListsController.cs` | All CRUD + PDF endpoints |
| `grohe-neo-services/src/GroheNeo.ProjectListsApi/DependencyInjectionExtensions.cs` | Firestore setup, EmulatorDetection, ProductsApi client |
| `grohe-neo-services/src/GroheNeo.ProjectListsApi/Services/ISpecificationDocumentService.cs` | PDF generation interface |
| `grohe-neo-services/src/GroheNeo.ProjectListsApi/appsettings.Integration.json` | WireMock URLs, dummy XMCloud credentials |
| `grohe-neo-services/src/GroheNeo.Foundation.DocumentGenerator/` | PuppeteerSharp + DotLiquid PDF library |
| `grohe-neo-websites/apps/website/src/app/api/project-lists/` | Next.js CRUD + export-document routes |
| `grohe-neo-websites/packages/features/project-lists/` | Project list UI components |
| `integration/tests/services/project-lists/` | Phase 6 integration tests |

## Known Issues & Gotchas

- **`UpdateProjectListRequestStorageMapper` bug (fixed):** was `UpdatedTimestamp = input.CreatedTimestamp` —
  fixed to `DateTime.SpecifyKind(input.UpdatedTimestamp, DateTimeKind.Utc)`. Also added
  `DateTime.SpecifyKind(..., DateTimeKind.Utc)` to `CreatedTimestamp` to prevent Firestore
  "Conversion from DateTime to Timestamp requires Utc" on re-read.
- **ETL data required for PDF test:** PLProductContent docs must be in Firestore. If you get
  an empty PDF or 404 product, run Phase 1 pipeline tests first.
- **JWT format:** tests send raw JWT (no "Bearer " prefix). Service strips "OndusBearer" prefix
  internally — raw token works.
- **ProductsApi must be in phase6 profile:** ProjectListsApi calls it directly, so both must start.
  `depends_on: products-api` in docker-compose.
- **EmulatorDetection in two FirestoreDbBuilder instances** in `DependencyInjectionExtensions.cs`.

## Common Ticket Patterns

- **Adding a field to project list items:** update Firestore model, add mapper in
  `UpdateProjectListRequestStorageMapper`, update frontend types in `@grohe/project-lists`.
- **PDF template change:** update DotLiquid template in `GroheNeo.Foundation.DocumentGenerator`.
- **New PDF section (e.g., sustainability):** add to `CreateSpecificationDocumentRequest`,
  update `ISpecificationDocumentService`, update PDF template.
- **Auth changes:** JWT claim extraction is in controller — change `GetClaimValue()` call.
