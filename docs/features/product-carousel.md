# Product Carousel

## What it does
Renders horizontally scrollable product carousels on content pages (homepage, landing pages,
campaign pages). Carousel content and layout are defined in Sitecore XM Cloud; product data
is fetched from ProductsApi by SKU. The `@grohe/content` feature package contains the carousel
React components consumed by Sitecore JSS.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.XmCloudApi` | Serves inspiration guides, pages, markets, country selector content |
| .NET service | `GroheNeo.ProductsApi` | Product data for carousel cards (by SKU) |
| Next.js routes | `/api/navigation-settings/[locale]` | Navigation/market config |
| Feature package | `@grohe/content` | Carousel components (Sitecore JSS renderings) |
| External | Sitecore XM Cloud | Carousel item definitions, page layouts |
| External | Sitecore Edge GraphQL | Layout data + CMS content delivery |

## Data Flow

```
Sitecore JSS (Next.js page render)
    → XM Cloud Edge GraphQL → page layout + carousel rendering fields
    → Carousel component (in @grohe/content) receives CMS fields:
        - list of product SKUs from XMCloud datasource
        - heading, intro copy from XMCloud fields
    → component fetches product cards:
        GET /api/product/... or POST /api/product/detail?sku=...&locale=...
            → ProductsApi → Firestore PLProductContent
    → renders carousel UI

    (separately) XmCloudApi endpoints for server-side data:
    → GET product and inspiration guide content
    → GET page layouts
    → GET markets / country selector / languages
```

## Key Business Logic

- **Two-layer data model:** XMCloud defines which products appear (editorial selection by SKU),
  while ProductsApi provides the current product data (name, image, category). XMCloud is the
  source of carousel structure; Firestore is the source of product content.
- **CMS-driven carousel configuration:** carousels are configured in Sitecore Content Editor
  (datasource items). Authors select products by SKU; XMCloud delivers the SKU list to the
  component at render time.
- **Sitecore JSS component pattern:** carousel components use `withValidatedProps(Schema)` and
  a Zod schema to validate XMCloud rendering fields before use.
- **XmCloudApi controllers:** `ProductAndInspirationGuidesController` serves featured product
  and guide data for specific carousel types (not all carousel types need this). `PagesController`
  serves page-level data. `CountrySelectorController` and `LanguagesController` for market/language
  selection carousels.
- **Variant ordering from XMCloud:** `GetVariantOrderingSettings` used in ProductsApi when
  building carousel product cards — same as PDP variant handling.
- **Multi-language:** carousel content is locale-specific in XMCloud. The Sitecore Edge request
  includes the language; product API requests include the locale.

## Data Models

### XMCloud rendering fields (carousel datasource — Sitecore schema)
```
// Depends on carousel type. Common fields:
{
  heading: { value: string },
  description: { value: string },
  products: { value: [{ id: string, fields: { sku: { value: string } } }] }
}
```

### ProductsApi call for carousel cards
```
GET /neo/product/v1/{sku}?locale=de-de&tagsCount=3
// Returns PLProductContent fields: name, images, category, tags, etc.
// See pdp.md for full model
```

### XmCloudApi endpoints (examples)
```
GET /v1/product-inspiration-guides?locale=...
GET /v1/pages?locale=...
GET /v1/country-selector?locale=...
GET /v1/markets?locale=...
```

## Integration Tests

None yet — no integration tests for carousel components or XmCloudApi.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.XmCloudApi/Controllers/ProductAndInspirationGuidesController.cs` | Inspiration guide/product content |
| `grohe-neo-services/src/GroheNeo.XmCloudApi/Controllers/PagesController.cs` | Page-level content |
| `grohe-neo-services/src/GroheNeo.XmCloudApi/Controllers/CountrySelectorController.cs` | Country selection carousel |
| `grohe-neo-services/src/GroheNeo.XmCloudApi/Controllers/LanguagesController.cs` | Language selection |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Controllers/MiddlewareController.cs` | Product detail for cards |
| `grohe-neo-websites/packages/features/content/` | Carousel React components (JSS renderings) |
| `grohe-neo-websites/jss/` | Sitecore JSS layer (`withValidatedProps`, schema utils) |
| `grohe-neo-sitecore-xm-cloud/src/src/helix/` | XMCloud component definitions and renderings |

## Known Issues & Gotchas

- **Carousel content is CMS-authored:** product SKUs in carousels are selected by content editors
  in Sitecore. If a carousel shows incorrect products, check the XMCloud datasource item, not
  the code.
- **XMCloud rendering fields vs API fields:** XMCloud delivers content as JSON rendering fields.
  The component schema must match the XMCloud template field names exactly. Mismatches cause
  `withValidatedProps` to render nothing (Zod validation failure, no error thrown by default).
- **Lazy loading of product data:** carousel components may load product cards lazily (after
  initial render) to avoid blocking page SSR. If carousel cards are empty on SSR, check whether
  product fetching happens client-side.
- **XmCloudApi OAuth2:** XmCloudApi authenticates to Sitecore using OAuth2 client credentials.
  If `appsettings.Integration.json` dummy credentials are missing, `ValidateOnStart` will throw.

## Common Ticket Patterns

- **New carousel component type:** create Sitecore rendering in XMCloud, create JSS component
  in `@grohe/content`, register in component map.
- **Add a product field to carousel cards:** update ProductsApi response mapper, update carousel
  component props, update Zod schema.
- **New XmCloudApi endpoint for carousel:** add controller + service in `GroheNeo.XmCloudApi`,
  add Next.js route if needed, add frontend fetch in `@grohe/content` component.
- **Carousel ordering changed by editor:** purely in XMCloud CMS — no code change. Authors
  reorder datasource items in Content Editor.
- **Carousel not rendering (blank):** first check Zod schema validation (component props don't
  match XMCloud template), then check ProductsApi responses.
