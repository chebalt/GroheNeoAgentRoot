# Product Filters

## What it does
Provides facet-based filtering for product lists and search results. Filters are not a separate
service — they are part of SearchApi's `POST /product/v1/search` response. The frontend sends
selected filter IDs back in subsequent requests; Sitecore Search computes updated facet counts
dynamically per query.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.SearchApi` | Returns facets in search response; accepts facet filters in request |
| Feature package | `@grohe/search-results` | Filter sidebar/drawer UI |
| Feature package | `@grohe/product-list` | PLP filter integration |
| External | Sitecore Search | Facet computation and filter application |
| External | XM Cloud | `SERP Filters/Filters` item — Sitecore-managed filter configuration |

## Data Flow

```
Browser (PLP/search results page)
    1. Initial request (no filters):
       POST /api/product/search { language, query, categories }
       → Response includes results + facets (all available filters with counts)

    2. User selects a filter value:
       POST /api/product/search { ..., facets: [{ name, ids: [base64id] }] }
       → Response includes filtered results + updated facet counts

    3. Multiple filters (AND within facet, OR across facets — depends on Sitecore config):
       POST /api/product/search { ..., facets: [{ name: "color", ids: [...] }, { name: "type", ids: [...] }] }
```

## Key Business Logic

- **Facets are dynamic:** computed by Sitecore Search based on current query + applied filters.
  Available filter options and counts change with each filtered request.
- **Facet ID encoding:** facet value IDs are base64-encoded Sitecore Search filter expressions.
  Pass them through unchanged — never hardcode or decode facet IDs.
- **Filter types:**
  - **Facet filters** (`facets[]`): color, installation, shape, material, etc. — from Sitecore Search
  - **Direct field filters** (`categories[]`): category ID, exact match
  - **Boolean filter** (`isSpareParts`): spare parts toggle
  - **Range filters** (`flowRateMin` / `flowRateMax`): numeric range for shower products
- **`isSpareParts` is not a facet:** it's a dedicated boolean param in `ProductsSearchParameters`,
  not part of the `facets[]` array.
- **Sitecore XM Cloud SERP Filters:** CMS-managed filter configuration at
  `Settings/SERP Filters/Filters` in XMCloud. Controls which facets appear in the UI and their
  display order/labels. The search API returns raw facets; XMCloud config drives UI presentation.
- **orderBy on filtered results:** `"relevance"` for keyword search, `"ranking"` for category
  browse. Filter changes should preserve the current `orderBy`.

## Data Models

### Facet filter request object
```
// Facet[] in ProductsSearchParameters.facets
[
  {
    name: string,             // facet name (e.g. "color", "installation_type")
    ids: string[]             // base64-encoded Sitecore filter expression IDs
  }
]
```

### Facets in response (Results.facets)
```
{
  [facetName: string]: FacetResult[]
}

// FacetResult
{
  name: string,     // display name of facet value
  count: int,       // number of products with this value
  id: string        // base64-encoded ID (pass back in next request to filter)
}
```

### Other filter params (from `ProductsSearchParameters`)
```
categories?: string[],        // Sitecore Search category IDs
isSpareParts?: bool,         // true = only spare, false = exclude spare, null = all
flowRateMin?: float,
flowRateMax?: float
```

## Integration Tests

Phase 5 tests cover SearchApi including facets — see `search.md`.
No dedicated filter-specific integration tests.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/Facet.cs` | Facet request model |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/FacetResult.cs` | Facet response model |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/FacetValueResult.cs` | Facet value with count |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/ProductsSearchParameters.cs` | All filter params |
| `grohe-neo-services/src/GroheNeo.SearchApi/Controllers/ProductsSearchController.cs` | Endpoint |
| `grohe-neo-services/src/GroheNeo.Feature.SitecoreSearch/Models/ConfigurationSearch.cs` | Search config |
| `grohe-neo-websites/packages/features/search-results/` | Filter sidebar UI |
| `grohe-neo-websites/packages/features/product-list/` | PLP filter integration |

## Known Issues & Gotchas

- **Facet IDs change between Sitecore Search deployments:** do not cache or hardcode facet IDs
  client-side across sessions. Always use IDs from the most recent response.
- **`isSpareParts: null` means "all":** passing `isSpareParts: false` excludes spare parts,
  not the same as not sending the field. Frontend must handle the three-state toggle carefully.
- **Flow rate filters are numeric ranges, not facets:** they are separate params, not in the
  `facets[]` array. Cannot be combined with facet filtering via the same mechanism.
- **Facet count vs total:** `facets.count` per value is the count with that value applied,
  assuming current other filters are active. Removing all filters changes counts.
- **SERP Filters in XMCloud** controls display, not search behavior: adding a facet to XMCloud
  SERP Filters only affects the UI display order/labels. The underlying facets from Sitecore
  Search are always returned regardless.

## Common Ticket Patterns

- **Add a new filter type:** configure facet in Sitecore Search console, add to XMCloud
  `Settings/SERP Filters/Filters`, update `@grohe/search-results` UI to render new facet.
- **Change filter display order:** update XMCloud SERP Filters item order (no code change needed).
- **Spare parts toggle:** `isSpareParts` boolean — add UI toggle to PLP, pass in search request.
- **Flow rate range slider:** `flowRateMin`/`flowRateMax` — add range slider to `@grohe/product-list`,
  pass values in search request.
- **Facet multi-select (OR):** default Sitecore Search behavior. If AND is needed, check
  Sitecore Search widget configuration.
