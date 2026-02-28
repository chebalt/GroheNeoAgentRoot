# Search

## What it does
Provides product and content search via Sitecore Search Discovery API. The SearchApi translates
Next.js search requests (keyword, filters, locale) into Sitecore Search queries, returns ranked
results, and supports autosuggest. SearchApi has NO Firestore dependency — it talks only to
Sitecore Search.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.SearchApi` | Translates requests → Sitecore Search queries, returns results |
| Next.js routes | `/api/autosuggest`, `/api/product/search`, `/api/content/search` | BFF proxy to SearchApi |
| Feature package | `@grohe/search-results` | Search results UI |
| External | Sitecore Search Discovery API | `https://discover-euc1.sitecorecloud.io/discover/v2/{domainId}` |
| External | XM Cloud | CMS content fields in search results; variant ordering settings |

## Data Flow

```
Browser (search results / autosuggest)
    → GET /api/autosuggest?q=...&lang=...      (Next.js BFF)
    → GET /api/product/search?q=...&lang=...   (Next.js BFF)
        → SearchApi
            → POST https://discover-euc1.sitecorecloud.io/discover/v2/{domainId}
            → optional: IXmCloudService.GetVariantOrderingSettings()
            → return ranked results
```

## Key Business Logic

- **No Firestore dependency:** SearchApi does not read Firestore — only Sitecore Search.
  Only WireMock is needed for integration tests (no Firestore emulator, no seed_config.py).
- **Language format:** `"lang"` key (not `"language"`); must use XM Cloud format `xx-xx`
  (e.g. `"de-de"`). Sending `"de"` alone returns 400.
- **Query parameter:** `"q"` (not `"query"`).
- **Domain ID:** each locale maps to a Sitecore Search `domain_id`; configured in
  `appsettings.json → SourceLocales`.
- **SourceLocales required:** `appsettings.Integration.json` sets
  `"SourceLocales": {"integration": ["de_de"]}` — without it, controllers return 500
  (source not found for locale).
- **Variant ordering via XM Cloud:** `IXmCloudService.GetVariantOrderingSettings` is called
  to sort product variants. Returns `ApiResponse<T>` — WireMock returns 404, `Content` is null,
  mapper accepts null gracefully (XM Cloud graceful fallback).
- **CrossApiServicesSettings override:** Integration test config overrides
  `ApiServices.XmCloudApi.BaseAddress` → WireMock URL.
- **Autosuggest vs full search:** separate endpoints with different Sitecore Search query shapes.

## Data Models

### Search request
```
GET /api/product/search?q={term}&lang={xx-xx}&page={n}&pageSize={n}&filters={...}
```

### Search response (key fields)
```
{
  total: number,
  results: [{
    sku: string,
    name: string,
    category: string,
    imageUrl: string,
    url: string,
    ...
  }],
  facets: [{
    name: string,
    values: [{ value, count }]
  }]
}
```

### Autosuggest response
```
{
  suggestions: [{ term: string, products: [...] }]
}
```

## Integration Tests

**Phase 5 (5 tests, ~30s):** `tests/services/search/` — SearchApi in Docker, WireMock stubs
Sitecore Search Discovery API + XM Cloud. No Firestore emulator needed.

```bash
# Start Phase 5 containers (SearchApi port 8085):
docker compose -f C:/projects/grohe/NEO/integration/docker-compose.yml --profile phase5 up -d

cd C:/projects/grohe/NEO/integration
SEARCH_API_HOST=localhost:8085 .venv/Scripts/python.exe -m pytest tests/services/search/ -v
```

**WireMock stubs:** Sitecore Search Discovery endpoint + XM Cloud variant ordering endpoint
(returns 404 → graceful null handling in mapper).

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.SearchApi/Controllers/` | Autosuggest + product/content search endpoints |
| `grohe-neo-services/src/GroheNeo.SearchApi/appsettings.Integration.json` | `SourceLocales` config, WireMock URL |
| `grohe-neo-services/src/GroheNeo.Feature.CrossApiServices/CrossApiServicesSettings.Integration.json` | XM Cloud URL override for tests |
| `grohe-neo-services/src/GroheNeo.Feature.SitecoreSearch/` | Discovery API service wrapper |
| `grohe-neo-services/src/GroheNeo.Feature.XmCloud/` | XM Cloud service (variant ordering) |
| `grohe-neo-websites/packages/features/search-results/` | Search results UI components |
| `grohe-neo-websites/apps/website/src/app/api/autosuggest/` | Autosuggest Next.js route |
| `integration/tests/services/search/` | Phase 5 search integration tests |

## Known Issues & Gotchas

- **Language format is `xx-xx` not `xx`:** `"de"` → 400 Bad Request. Always use `"de-de"`, `"en-gb"` etc.
- **Query key is `q` not `query`:** sending `query=...` returns no results, not an error.
- **XM Cloud graceful fallback:** `GetVariantOrderingSettings` returns null when XM Cloud is
  unavailable — the mapper must handle null `settings.Content` (already implemented).
- **CrossApiServicesSettings.Integration.json** must have `CopyToOutputDirectory: Always` in csproj
  and must be loaded AFTER `CrossApiServicesSettings.json` to override the production XM Cloud URL.
- **SourceLocales runtime validation:** the locale must exist in `SourceLocales` config — missing
  locale causes 500, not 400. Add to `appsettings.Integration.json` for test runs.

## Common Ticket Patterns

- **Adding a new search filter:** update Sitecore Search query builder to include new facet,
  update `search-results` package to render the new filter UI.
- **Adding a new result field:** update the Sitecore Search document schema (via IndexingApi
  mapper), update the search response mapper, update frontend types.
- **New locale support:** add to `SourceLocales` in appsettings per environment, verify domain_id
  mapping in Sitecore Search console.
- **Autosuggest tuning:** update Sitecore Search query parameters (suggestion count, entity types)
  in SearchApi service.
