# PLP (Product List Page)

## What it does
Displays paginated, filterable lists of products within a category or for a search query.
ProductsApi provides category structure; SearchApi provides the product results, facets, and
sorting. The PLP page is an SSR/ISR Next.js page that calls both services.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.ProductsApi` | Category hierarchy, category page metadata |
| .NET service | `GroheNeo.SearchApi` | Product search results, facets, pagination |
| Next.js routes | `POST /api/product/search` | BFF proxy to SearchApi |
| Feature package | `@grohe/product-list` | PLP UI — product grid, pagination |
| Feature package | `@grohe/search-results` | Filter UI, facet components |
| Firestore | `PLCategory` | Category data for navigation and page metadata |
| External | Sitecore Search | Search index for product results and facets |
| External | XM Cloud | Page layout, CMS content |

## Data Flow

```
Browser (PLP page — SSR/ISR)
    → Next.js page fetches category metadata from ProductsApi
    → Next.js page or client fetches products from SearchApi via /api/product/search

POST /api/product/search  →  SearchApi  POST /product/v1/search
    → Sitecore Search geospatial/category query
    → return ProductResult[], facets, total
```

## Key Business Logic

- **Category filtering:** `categories?: string[]` in `ProductsSearchParameters` — filter by
  Sitecore Search category IDs. PLP passes the category ID for the current browse path.
- **Pagination:** `limit` (results per page) + `offset` (skip). Both clamped to config min/max.
  Default ordering: `"ranking"` (not `"relevance"` — ranking is editorial order for PLPs).
- **Facets:** Sitecore Search returns facets dynamically based on results. Client sends
  base64-encoded facet IDs to filter. Facet counts update on each request.
- **Spare parts filtering:** `isSpareParts?: bool` — `true` = only spare parts, `false` = exclude
  spare parts, `null` = all.
- **Flow rate range:** `flowRateMin` / `flowRateMax` for shower-related product filtering.
- **Locale:** `language` param in XMCloud format `xx-XX` (e.g. `de-DE`). Converted internally
  to Search locale (`de_DE`).
- **Variant ordering from XMCloud:** `IXmCloudService.GetVariantOrderingSettings` called to
  determine finish/size display order. Graceful null handling if XMCloud unavailable.
- **SKU auto-detection:** if `query` looks like a SKU, it's extracted and filtered by SKU.
- **Analytics context:** optional `context.user.uuid` and `context.browser.*` fields for
  Sitecore Search personalization/analytics.

## Data Models

### `ProductsSearchParameters`
```
{
  language: string,          // "de-DE" format
  query: string,             // search term or category context
  limit: int,                // results per page (clamped to config)
  offset: int,               // pagination offset
  skus?: string[],
  categories?: string[],     // category IDs for PLP
  isSpareParts?: bool,
  facets?: Facet[],          // [{ name, ids: [base64-encoded-id] }]
  numberOfTags: int,         // default 3
  flowRateMin?: float,
  flowRateMax?: float,
  orderBy: string,           // "relevance" | "ranking"
  context?: {
    user: { uuid: string },
    browser: { app_type, desktop: bool, user_agent }
  }
}
```

### `Results<ProductResult>` response
```
{
  rfk_id: string,
  entity: string,
  total: int,
  results: ProductResult[],
  facets: { [facetName]: FacetResult[] }
}
```

See `search.md` for `ProductResult` fields (shared with product search).

## Integration Tests

Phase 5 tests cover SearchApi (autosuggest + product search) — see `search.md`.
No dedicated PLP integration tests that combine ProductsApi + SearchApi together.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.SearchApi/Controllers/ProductsSearchController.cs` | `POST /product/v1/search` |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/ProductsSearchParameters.cs` | Request model |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/ProductResult.cs` | Result model |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/BaseLimitedSearchParameters.cs` | Limit/offset base |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Controllers/MiddlewareController.cs` | Category endpoints |
| `grohe-neo-websites/apps/website/src/app/api/product/search/route.ts` | Next.js proxy |
| `grohe-neo-websites/packages/features/product-list/` | PLP UI components |
| `grohe-neo-websites/packages/features/search-results/` | Filter/facet components |

## Known Issues & Gotchas

- **`orderBy: "ranking"` is the PLP default** (not `"relevance"` which is for keyword search
  results). If PLP order looks wrong, check which value is being sent.
- **Limit clamping is silent:** if `limit` exceeds config max, a warning is logged and the value
  is clamped. The response will have fewer results than requested without an error — check logs
  if results seem truncated.
- **Facet IDs are base64-encoded Sitecore expressions:** don't try to decode/inspect them;
  pass them through as received in the facets response.
- **Empty category query returns 200 OK** (not 204 or 400). Frontend must handle zero results.
- **Language format `xx-XX` required** (hyphen, uppercase country). See `search.md` for details.
- **XMCloud variant ordering graceful null:** already handled — `GetVariantOrderingSettings`
  can return null without crashing.

## Common Ticket Patterns

- **Add new facet to PLP:** add Sitecore Search facet configuration in the search console,
  add to `@grohe/search-results` filter UI, add request param if needed.
- **Change PLP sort order:** update `orderBy` default in the frontend request.
- **Category-based PLP:** pass `categories: [categoryId]` in the search request.
- **New PLP result field:** see `search.md` — involves updating indexing and search mapping.
- **Flow rate filter:** already implemented — `flowRateMin` / `flowRateMax` params.
