# Product Catalogue

## What it does
Supports browsing the full product range by category — listing products under a category node,
navigating category hierarchies, and generating sitemaps. ProductsApi reads category and product
data from Firestore; SearchApi provides product listing/search within categories. This is the
data layer that underlies PLP when browsing by category rather than searching by keyword.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.ProductsApi` | Category hierarchy, product detail, variants, sitemaps |
| .NET service | `GroheNeo.SearchApi` | Product listing within categories (via `categories[]` param) |
| Next.js routes | `POST /api/product/detail`, `POST /api/product/search` | BFF proxies |
| Feature package | `@grohe/product-list` | PLP grid, category navigation |
| Firestore | `PLCategory` | Category hierarchy per locale |
| Firestore | `PLProductContent` | Product content per locale |
| Firestore | `PLVariant` | Product variants |
| Firestore | `CategoryRouting` | URL paths for category navigation |
| External | XM Cloud | Page layouts, variant ordering settings |

## Data Flow

```
Browser (category browse page — SSR/ISR)
    → ProductsApi GET /neo/product/v1/category?locale=...&path=...
        → read PLCategory from Firestore
        → return category metadata, children, product list (for sitemaps)

    → SearchApi POST /product/v1/search { language, query, categories: [categoryId] }
        → Sitecore Search query with category filter
        → return ProductResult[] with facets

    → (optional) ProductsApi GET /neo/product/v1/{sku}?locale=...
        → product detail for category product cards
```

## Key Business Logic

- **Category lookup modes:** query by `id`, `parentId`, `path`, or none (all categories). Only
  one should be provided per request.
- **Path-based routing:** `CategoryRouting` Firestore collection maps URL slugs to category IDs.
  Used by Next.js SSR to resolve URL → category metadata before rendering.
- **Locale fallback:** if a category/product document is missing for the requested locale,
  the service falls back to the configured `fallback_locale` (usually `en_gb`).
- **`noCache` bypass:** `?noCache=true` skips the response cache — useful after ETL for
  immediate content validation.
- **Cache invalidation endpoint:** `GET /neo/product/v1/clearcache` with params
  `getProductData`, `getCategoryData`, `getCategoryDataByPath`, etc. Called by data-loader's
  `CLEAR_CACHE_URL` after ETL completes.
- **Sitemap generation:** `GET /neo/product/v1/productsitemap` and `categorysitemap` return
  XML sitemaps chunked for large catalogues. Locale param required.
- **Tag limiting:** `?tagsCount=N` controls max tags per product in category listing response.
  Default 3.
- **Variant ordering from XMCloud:** same as PDP — `GetVariantOrderingSettings` may be called
  for category product cards.

## Data Models

### Category endpoints
```
GET /neo/product/v1/category?locale=de-de&path=/bathroom/mixers
// Returns:
{
  id: string,
  name: string,
  path: string,
  parentId?: string,
  children?: CategoryResponse[],
  // additional category metadata
}
```

### Product detail (from Firestore PLProductContent)
```
GET /neo/product/v1/{sku}?locale=de-de&tagsCount=3&noCache=false
// See pdp.md for PLProductContent structure
```

### Variant lookup
```
GET /neo/product/v1/variants?sku=...&locale=de-de
// Returns array of PLVariant documents — finish/size variants
```

### Cache clear endpoint
```
GET /neo/product/v1/clearcache?locale=de-de
  &getProductData=true
  &getCategoryData=true
  &getCategoryDataByPath=true
  &getProductVariants=true
  &generateProductPdfDocument=true
  &PDPSiteMap=true
  &PLPSiteMap=true
```

## Integration Tests

Phase 4 tests cover ProductsApi (product detail + category access) — see `pdp.md`.
No dedicated catalogue-specific integration tests beyond Phase 4.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.ProductsApi/Controllers/MiddlewareController.cs` | All ProductsApi endpoints |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Services/Firestore/Categories/ICategoriesService.cs` | Category service interface |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Services/Firestore/SiteMaps/ISiteMapsService.cs` | Sitemap generation |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Services/Firestore/ProductData/IProductDataService.cs` | Product data service |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Services/Firestore/Variants/IVariantsService.cs` | Variant lookup |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Services/IMiddlewareService.cs` | Service orchestration |
| `grohe-neo-data-loader/output_models/` | PLCategory, CategoryRouting, PLProductContent models |
| `grohe-neo-websites/packages/features/product-list/` | Category browse UI |

## Known Issues & Gotchas

- **Category by path vs by ID:** XMCloud and Next.js use path-based routing; Sitecore Search uses
  category IDs. The `CategoryRouting` collection bridges the two — if path-based lookups fail,
  check that `CategoryRouting` was populated by the data-loader.
- **Fallback locale silently returns different data:** if a locale is missing, fallback to
  `en_gb` happens silently. Users may see English content instead of their language. Monitor
  data-loader runs to ensure all locales are populated.
- **`noCache=true` on hot pages:** use sparingly. Cache exists for performance — calling
  with `noCache=true` on every request degrades ProductsApi performance.
- **Sitemap chunking:** for large catalogues, sitemaps are split into chunks. The sitemap index
  file links to chunk files. Verify sitemap chunk URLs are accessible by search engines.
- **EmulatorDetection and seed_config.py:** same requirements as PDP — see `pdp.md`.

## Common Ticket Patterns

- **Add a new category field (e.g. badge):** update `PLCategory` in data-loader output models,
  update transformer, update category API response mapper, update `@grohe/product-list` UI.
- **Change category URL structure:** update `CategoryRouting` model and data-loader transformer.
  Update Next.js dynamic route to match new path pattern.
- **Cache invalidation after ETL:** data-loader already calls `CLEAR_CACHE_URL` in `entrypoint.sh`.
  If cache isn't cleared, verify `CLEAR_CACHE_URL` env var points to the right ProductsApi instance.
- **New locale sitemap:** ensure ETL has run for the new locale and the sitemap endpoint
  is called with the new locale param.
- **Category page 404:** check `CategoryRouting` doc exists for the path + locale combination.
