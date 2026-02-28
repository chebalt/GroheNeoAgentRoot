# Product Specification

## What it does
Displays technical product specifications on the PDP — dimensions, materials, certifications,
technical data — rendered in the `PDPAccordion` component. External specification sheet PDFs
are proxied through a Next.js route. Project list exports include specifications as PDF documents
generated server-side by ProjectListsApi using PuppeteerSharp + DotLiquid.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.ProductsApi` | Returns spec data as part of product detail (Firestore) |
| .NET service | `GroheNeo.ProjectListsApi` | Generates specification PDF documents |
| Next.js route | `GET /api/product/specification?url=` | Proxy for external spec sheet PDFs |
| Next.js route | `POST /api/product/detail` | Product detail including spec sections |
| Next.js route | `POST /api/project-lists/export-document` | Project list PDF with specs |
| Feature package | `@grohe/product` | `PDPAccordion` component — renders spec sections |
| Firestore | `PLProductContent` | Specification data stored in `details` array |
| External | XM Cloud | Page layout, section labels |

## Data Flow

```
Browser (PDP page)
    → POST /api/product/detail?sku=...&locale=...
        → ProductsApi GET /neo/product/v1/{sku}
            → read PLProductContent.details from Firestore
            → return spec sections in product payload

    → PDPAccordion renders "specification" section from response

    → (spec sheet PDF) GET /api/product/specification?url=https://external.pdf
        → Next.js fetches external PDF URL, streams response — no processing

    → (project list PDF) POST /api/project-lists/export-document
        → ProjectListsApi
            → fetches product detail per SKU from ProductsApi
            → generates PDF via PuppeteerSharp + DotLiquid
```

## Key Business Logic

- **Spec data is in `PLProductContent.details`:** the product detail response contains a `details`
  array of sections. The "specification" section contains subsections (dimensions, materials, etc.).
- **Dimension drawing extraction:** the `detail/route.ts` has special handling for the
  "specification" section — looks for a "dimension-drawing" subsection and extracts images from
  `dimentional-drawing` and `dimentional-drawing-inches` fields. **Note:** the field name has a
  typo in the actual code (`dimentional` not `dimensional`) — do not correct it without updating
  the data-loader output model too.
- **`onlySizeDrawing` param:** passing `?onlySizeDrawing=true` to the detail route extracts
  only the dimension drawing images, skipping other spec content.
- **Spec sheet proxy:** `GET /api/product/specification?url=...` is a simple pass-through proxy —
  no caching, no modification. URL must be a valid external HTTPS URL. Typically used for
  Grohe's CDN-hosted product spec PDFs.
- **Project list specification PDF:** `CreateSpecificationDocumentRequest` includes:
  `specificationFormValues` (headline, description, language, contact details, VAT inclusion),
  `sustainabilitySection`, and `projectListId`. ProductsApi is called internally for each product.
- **Price formatting in PDF:** gross/net price calculated based on `include: ["include_vat"]` flag.
- **ETL data required for PDF:** see `project-list.md` — PLProductContent must be populated.

## Data Models

### Specification section in `PLProductContent.details`
```
// ProductDetailResponse.details (array)
[{
  section: "specification",
  subsections: [{
    id: "dimension-drawing",
    value: {
      "dimentional-drawing": [imageUrl, ...],         // note: typo in field name
      "dimentional-drawing-inches": [imageUrl, ...]   // imperial dimensions
    }
  }, {
    id: "technical-data",
    value: { ... }
  }]
}]
```

### Specification proxy route
```
GET /api/product/specification?url=https://media.grohe.com/path/to/spec.pdf
→ 200 OK, Content-Type: application/pdf
(no auth required — public external PDF)
```

### Project list spec export request
```
POST /api/project-lists/export-document
{
  projectListId: string,
  locale: string,
  specificationFormValues: {
    headline, description, language,
    coverImage, logoImage,
    reference: string,
    specifications: bool,
    include: string[],      // ["include_vat"]
    contactDetails: {...}
  },
  sustainabilitySection: {...}
}
→ Response: application/pdf
```

## Integration Tests

**Phase 6 test 10 (PDF):** `tests/services/project-lists/test_project_lists.py::test_10`
generates a specification PDF. Requires PLProductContent data in Firestore (run Phase 1 first).
See `project-list.md` for setup.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-websites/apps/website/src/app/api/product/specification/route.ts` | External PDF proxy |
| `grohe-neo-websites/apps/website/src/app/api/product/detail/route.ts` | Dimension drawing extraction |
| `grohe-neo-services/src/GroheNeo.ProductsApi/Controllers/MiddlewareController.cs` | Product detail endpoint |
| `grohe-neo-websites/apps/website/src/app/api/project-lists/export-document/route.ts` | PDF export route |
| `grohe-neo-services/src/GroheNeo.ProjectListsApi/Controllers/ProjectListsController.cs` | `POST /specificationDocument` |
| `grohe-neo-services/src/GroheNeo.ProjectListsApi/Services/ISpecificationDocumentService.cs` | PDF generation |
| `grohe-neo-services/src/GroheNeo.Foundation.DocumentGenerator/` | PuppeteerSharp + DotLiquid PDF library |
| `grohe-neo-websites/packages/features/product/` | `PDPAccordion` component |

## Known Issues & Gotchas

- **`dimentional` typo in field name:** the field is named `dimentional-drawing` (missing 's')
  in both the Firestore document and the `detail/route.ts` extraction logic. Do not "fix" this
  typo in isolation — it must be updated in the data-loader output model, transformer, and
  Next.js route at the same time.
- **Spec sheet proxy has no auth or rate limiting:** any valid URL can be passed. If abuse is
  a concern, add URL validation/allowlist to `specification/route.ts`.
- **Project list PDF requires ProductsApi:** ProjectListsApi calls ProductsApi directly
  (not WireMock) for product data. Both services must be running (Phase 6 profile).
- **ETL data for PDF:** if PDF generation fails with "product not found", PLProductContent is
  empty. Run Phase 1 pipeline tests (`make test-pipeline`) to populate Firestore.

## Common Ticket Patterns

- **Add a new spec section:** update `PLProductContent.details` shape in data-loader output
  models, update transformer to populate the new section, update `PDPAccordion` to render it.
- **Add a field to the specification PDF:** update `CreateSpecificationDocumentRequest`, update
  `ISpecificationDocumentService` implementation, update DotLiquid PDF template.
- **Fix spec sheet PDF not loading:** check that the external URL is accessible from the Next.js
  server runtime (Vercel edge function or serverless function) — URL might be IP-restricted.
- **Dimension drawing not showing:** check `PLProductContent.details` for the product SKU in
  Firestore — verify the "dimension-drawing" subsection and the `dimentional-drawing` field
  (with the typo) are populated by the data-loader.
