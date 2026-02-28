# Pricing

## What it does
Returns real-time product prices from Hybris (SAP Commerce Cloud). Prices are market-specific
and optionally user-specific (registered users may see different prices). PricingApi is called
client-side on PDP and PLP pages — prices are never included in SSR responses.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.PricingApi` | Fetches prices from Hybris, caches 5 min |
| Next.js route | `POST /api/product/pricing` | BFF wrapper — batches SKUs |
| External | Hybris (SAP Commerce) | Source of pricing data |
| External | IDP (OpenID Connect) | JWT to identify user for user-specific pricing |

## Data Flow

```
Browser (PDP/PLP — client-side, after SSR)
    → POST /api/product/pricing  { sku: "123|456|789", locale: "de-de" }
        → PricingApi
            → extract user email from JWT (or use "anonymous")
            → check in-memory cache (key: sku-locale-userId, TTL 5 min)
            → if miss: GET Hybris /product/v1/price?sku=...&locale=...
            → cache result
            → return price list
```

## Key Business Logic

- **JWT optional:** anonymous users get prices too. JWT is parsed to extract user email for
  user-specific pricing tiers. Falls back to `"anonymous"` if no valid JWT.
- **Token parsing:** handles both `"Bearer {token}"` and raw token formats.
  Uses `IdpTokenHelper` to extract email claim without RSA signature validation.
- **Cache key:** `HYBRIS-PRICING-API-GET-PRICES-{skus}-{locale}-{userId}` — 5-minute in-memory
  TTL. Cache is per-sku-set, not per-sku, so batching matters.
- **Batch pricing:** SKUs are pipe-delimited (`123|456|789`). Next.js route POSTs all SKUs in
  one call; service splits them for Hybris.
- **Mock pricing:** `useMock=true` query param bypasses Hybris and uses `MockPricingApi`.
  Controlled via keyed DI: `[FromKeyedServices("Mock")] / [FromKeyedServices("Hybris")]`.
- **Partial content (206):** if some SKUs fail pricing, service can return 206 with available
  prices. Full success = 200.
- **GoogleIdTokenHandler:** custom HTTP handler for Hybris OAuth integration.

## Data Models

### Request (POST body to Next.js, forwarded to service)
```
{
  sku: "123|456|789",   // pipe-delimited for batch
  locale: "de-de",
  useMock: false        // optional, defaults false
}
```

### Response
```
{
  prices: [{
    sku: string,
    value: decimal,
    currencyIso: string,
    ...                 // additional market-specific fields
  }]
}
```

## Integration Tests

None yet — PricingApi has no dedicated integration tests in `integration/`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.PricingApi/Controllers/PricingController.cs` | Single endpoint |
| `grohe-neo-services/src/GroheNeo.PricingApi/Services/PricingService.cs` | Caching + orchestration (132 lines) |
| `grohe-neo-services/src/GroheNeo.PricingApi/Services/Hybris/HybrisPricingApi.cs` | Hybris HTTP client |
| `grohe-neo-services/src/GroheNeo.PricingApi/Services/Hybris/MockPricingApi.cs` | Mock implementation |
| `grohe-neo-services/src/GroheNeo.PricingApi/DependencyInjectionExtensions.cs` | Keyed DI setup |
| `grohe-neo-services/src/GroheNeo.PricingApi/Mappings/PriceMapper.cs` | Hybris → response mapping |
| `grohe-neo-websites/apps/website/src/app/api/product/pricing/route.ts` | Next.js POST wrapper (42 lines) |

## Known Issues & Gotchas

- **Prices are always client-side:** never included in SSR/ISR Next.js output. If prices appear
  to be stale, check the 5-minute in-memory cache — it does not respect Hybris price changes within
  the TTL window.
- **Pipe delimiter:** SKUs must be pipe-delimited, not comma-delimited. Wrong delimiter = partial
  results or 400.
- **Mock mode:** `useMock=true` is for dev/testing only — ensure it's not set in production
  requests. Keyed DI selects implementation at startup based on config, not per-request flag.
  (Check if `useMock` is a query param or config-driven — verify in `PricingController.cs`.)
- **Partial 206:** if downstream pricing fails for some SKUs, the response may be 206.
  Frontend must handle partial pricing gracefully (show "-" for missing prices).

## Common Ticket Patterns

- **New price field from Hybris:** update `PriceMapper.cs`, update the response type in
  `PricingApi` and frontend types.
- **Cache TTL change:** update TTL in `PricingService.cs` IMemoryCache options.
- **Per-user pricing:** JWT email is already passed to Hybris — verify Hybris basesite config
  has user price groups configured.
- **Adding a market:** verify Hybris basesite exists for the new locale in `AuthorizationService`.
