# Store Locator

## What it does
Lets users find nearby GROHE showrooms and retail partners by drawing a map bounding box or
providing a center point. Store data is indexed in Sitecore Search by `StoreLocatorJob` (Workato-
triggered). The frontend queries SearchApi's store locations endpoint — no dedicated read API
service. Results include certifications, contact info, distance from center.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.SearchApi` | Serves store search via Sitecore Search |
| .NET job | `GroheNeo.StoreLocatorJob` | Syncs external store data → `stores-index-updates` Firestore |
| .NET service | `GroheNeo.IndexingApi` | Reads `stores-index-updates`, posts to Sitecore Search Ingestion |
| Next.js route | `POST /api/stores/search` | BFF proxy to SearchApi |
| Feature package | `@grohe/locator` | Map UI + store card components |
| External | External stores API | Source of store/showroom data |
| Firestore | `stores-index-updates` | Change queue for store index updates |
| External | Sitecore Search | Store search index (geospatial queries) |

## Data Flow

```
Workato (scheduled) → StoreLocatorJob
    → fetch store data from external stores API
    → write to stores-index-updates (Firestore)
    → IndexingApi picks up finished=false docs
    → POST to Sitecore Search Ingestion API

Browser (store locator page) [optional JWT]
    → POST /api/stores/search  { language, west/south/east/north or centerLat/centerLon, zoom, filters }
        → SearchApi POST /stores/v1/search
            → Sitecore Search geospatial query
            → return store list with distance
```

## Key Business Logic

- **Bounding box OR center point:** request must have either a bounding box (west/south/east/north,
  all non-zero) OR center coordinates (centerLat/centerLon, both non-zero). All coordinates must
  be non-zero to be valid (zero = not provided).
- **Language format:** uses XMCloud format `xx-XX` (e.g. `en-GB`). Internally converted to
  Sitecore Search locale format (`en_GB` with underscore).
- **Store run arguments:** `StoreLocatorJob --run <locale> <yyyy-mm-dd>` or `run-all`.
  Env vars: `LOCALES_TO_BE_EXECUTED`, `DEFAULT_TIME_FROM`.
- **Certification flags:** boolean fields on `StoreLocationResult` — used for filter display
  and UI badges.
- **No Firestore read on search path:** SearchApi reads only Sitecore Search, not Firestore.
- **Facet filters:** base64-encoded facet IDs in `facets[]` array (same pattern as product search).
- **Distance calculation:** automatic when center coordinates provided. `distanceInKm` in response.
- **Optional JWT:** user UID passed if authenticated (for analytics context).

## Data Models

### `StoreLocationsSearchParameters`
```
{
  language: string,          // "en-GB" format
  west, south, east, north: double,   // bounding box (all non-zero to be valid)
  centerLat, centerLon: double,       // center point
  zoom: int,
  storeType?: string,
  design?: string,
  isWs?: bool,               // water systems certified
  isBath?: bool,             // bathroom solutions certified
  isSpa?: bool,
  isKitchen?: bool,
  facets?: Facet[]
}
```

### `StoreLocationResult`
```
{
  id: string,                // e.g. "RS-0003082-qa"
  name?: string,
  type?: string,             // "Showroom", etc.
  latitude, longitude: double,
  distanceInKm: double,
  address?: { street, postalCode, countryCode, city },
  mainPhone?, mainEmail?, url?: string,
  designGroups?: string[],
  designs?: string[],
  isGrohePlusMember: bool,
  isWatersystemsCertified: bool,
  isHygieneSolutionCertified: bool,
  isInstallationSystemsCertified: bool,
  isRapidoShowerframeCertified: bool,
  isShowerToiletsCertified: bool,
  isEverstreamCertified: bool,
  isBathroomSolutionsCertified: bool,
  overallQualityRating?: string,
  lastUpdateAt?: string
}
```

## Integration Tests

None yet — StoreLocatorJob/store search has no dedicated integration tests in `integration/`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.SearchApi/Controllers/StoreLocationsController.cs` | Store search endpoint |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/StoreLocationsSearchParameters.cs` | Request model |
| `grohe-neo-services/src/GroheNeo.SearchApi/Models/StoreLocationResult.cs` | Response model |
| `grohe-neo-services/src/GroheNeo.StoreLocatorJob/Program.cs` | Job entry point, CLI args |
| `grohe-neo-services/src/GroheNeo.IndexingApi/Controllers/StoreLocationsIndexingController.cs` | Store indexing endpoint |
| `grohe-neo-websites/apps/website/src/app/api/stores/search/route.ts` | Next.js proxy |
| `grohe-neo-websites/packages/features/locator/` | Map UI, store cards |
| `grohe-neo-services/src/GroheNeo.Feature.SitecoreSearch/Services/ISearchService.cs` | Search service interface |

## Known Issues & Gotchas

- **Zero coordinate = "not provided":** all coordinate fields default to `0.0`. A bounding box
  with any zero coordinate is treated as invalid. A bounding box that genuinely spans the prime
  meridian or equator would also fail — unlikely in practice.
- **Store ID format:** includes environment suffix in QA (e.g. `RS-0003082-qa`). PROD IDs don't
  have the suffix. Don't hardcode IDs across environments.
- **Language format must be `xx-XX`** (hyphen, uppercase country). SearchApi converts internally
  but the request must use XMCloud language format.
- **`StoreLocatorJob` is Workato-triggered:** not continuously running. If store data is stale,
  check Workato scheduler logs.

## Common Ticket Patterns

- **New certification type:** add boolean field to `StoreLocationResult`, update Sitecore Search
  index schema, update `StoreLocatorJob` data mapping, update `@grohe/locator` filter UI.
- **New store data field:** update external stores API mapping in `StoreLocatorJob`, update
  `StoreLocationResult`, update store card component.
- **Language support for store locator:** ensure Sitecore Search has a store index for the new
  locale's domain ID.
- **Map filter (e.g. filter by design):** add param to `StoreLocationsSearchParameters`,
  map to Sitecore Search facet query, update `@grohe/locator` filter UI.
