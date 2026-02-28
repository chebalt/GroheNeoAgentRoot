# Redirections

## What it does
Handles URL redirects (301), vanity URLs (subdomain and path-based), domain/locale normalization,
and reverse proxying to the Next.js frontend. Implemented as a YARP reverse proxy with a custom
middleware pipeline — not a traditional REST API. Redirect rules are stored in Firestore and
loaded from Excel via `ReverseProxyDataLoaderJob`.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.RedirectReverseProxy` | YARP reverse proxy + redirect middleware pipeline |
| .NET job | `GroheNeo.ReverseProxyDataLoaderJob` | Loads redirect rules from Excel → Firestore |
| Firestore | 6 collections | Redirects, IgnoredRoutePrefixes, LegacyDomainLocaleMapping, ValidLocales, SubdomainVanityURL, PathVanityURL |
| External | XM Cloud API | Language/market configuration |
| External | IP Intelligence API | Geolocation (optional) |
| External | Vercel | Downstream target of the proxy (with bypass token) |

## Data Flow

```
Incoming HTTP request (user browser)
    → IgnoreRouteMiddleware          (skip configured route prefixes)
    → VanitySubdomainMiddleware      (optional, if UseVanityMiddleware=true)
    → VanityPathMiddleware           (optional)
    → RootIdentificationMiddleware   (extract host, path)
    → RedirectLookupMiddleware       (Firestore query → 301 if match found)
    → SKUPatternMatchMiddleware      (match /sku/... patterns)
    → RewardShopMatchMiddleware      (reward shop routing)
    → DomainAndLocaleConsolidationMiddleware  (normalize domain/locale)
    → YARP ReverseProxy              (forward to Vercel)
```

## Key Business Logic

- **Firestore-driven redirects:** `RedirectLookupMiddleware` queries Firestore with the URL path,
  locale, query string, and host. Returns 301 with the `Location` header.
- **Fallback retry:** if first lookup (with query string) fails, retries without query string.
- **External vs internal redirects:** redirects marked as external skip domain normalization.
- **Query string appending:** configured redirects can include original query string in the
  destination URL.
- **Vanity subdomains/paths:** optional preprocessing controlled by `UseVanityMiddleware` config
  flag in `appsettings.json`.
- **Domain/locale normalization:** `DomainAndLocaleConsolidationMiddleware` ensures locale is
  in `xx-XX` format and maps legacy domains to current domain structure.
- **IP Intelligence:** optional geolocation used for market/locale detection. Disabled if
  `IP_INTELLIGENCE_API_KEY` is not set.
- **Vercel bypass token:** proxy adds a Vercel protection bypass token header for the downstream
  request (dev/staging environments).
- **`ReverseProxyDataLoaderJob` CLI:**
  - `--upd [1|2|3|4|5|6|all] <prefix>` — upload collection(s) from Excel
  - `--del <prefix>` or `--del file` — delete by prefix or from file
  Numbers map to: 1=Redirects, 2=IgnoredRoutePrefixes, 3=LegacyDomainLocaleMapping,
  4=ValidLocales, 5=SubdomainVanityURL, 6=PathVanityURL.

## Data Models

### Firestore Redirect document
```
{
  id: "<prefix>_<order>",    // e.g. "de-de_001"
  source: string,            // URL path to match
  destination: string,       // redirect target
  locale: string,
  host: string,
  isExternal: bool,
  includeQueryString: bool
}
```

### Firestore collections
| Collection | Purpose |
|---|---|
| `Redirects` | URL redirect rules |
| `IgnoredRoutePrefixes` | Routes to skip (e.g. `/api/`, `/_next/`) |
| `LegacyDomainLocaleMapping` | Old domain → current domain/locale mapping |
| `ValidLocales` | Accepted locale list |
| `SubdomainVanityURL` | Subdomain → URL mapping |
| `PathVanityURL` | Path → URL mapping |

## Integration Tests

None yet — RedirectReverseProxy has no dedicated integration tests in `integration/`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.RedirectReverseProxy/Program.cs` | Middleware pipeline registration, YARP setup |
| `grohe-neo-services/src/GroheNeo.RedirectReverseProxy/Middleware/RedirectLookupMiddleware.cs` | Core redirect logic, Firestore query |
| `grohe-neo-services/src/GroheNeo.RedirectReverseProxy/Middleware/DomainAndLocaleConsolidationMiddleware.cs` | Domain/locale normalization |
| `grohe-neo-services/src/GroheNeo.RedirectReverseProxy/Middleware/VanityPathMiddleware.cs` | Vanity path processing |
| `grohe-neo-services/src/GroheNeo.RedirectReverseProxy/Middleware/VanitySubdomainMiddleware.cs` | Vanity subdomain processing |
| `grohe-neo-services/src/GroheNeo.RedirectReverseProxy/Middleware/RootIdentificationMiddleware.cs` | Host/path extraction |
| `grohe-neo-services/src/GroheNeo.ReverseProxyDataLoaderJob/Program.cs` | Excel → Firestore loader |
| `grohe-neo-services/src/GroheNeo.RedirectReverseProxy/DependencyInjectionExtensions.cs` | DI, Firestore setup |

## Known Issues & Gotchas

- **Zero-coordinate-style validation:** bounding box logic not applicable here, but middleware
  order is critical — changing the order in `Program.cs` can break redirect/vanity logic.
- **Firestore read on every request:** `RedirectLookupMiddleware` queries Firestore per request
  for redirect matching. This is the hot path. Ensure Firestore indexes are appropriate.
- **`UseVanityMiddleware` config flag:** if vanity URLs are not working, check this flag in
  `appsettings.{env}.json`.
- **Excel format for loader job:** `ReverseProxyDataLoaderJob` reads a specific Excel schema.
  If columns change, update the loader model.
- **Prefix in document ID:** Firestore docs are keyed `<prefix>_<order>`. Uploading with a
  different prefix creates new docs — old docs with the old prefix remain unless deleted.

## Common Ticket Patterns

- **Add a redirect rule:** use `ReverseProxyDataLoaderJob --upd 1 <prefix>` with an Excel file
  containing the source/destination/locale/host columns.
- **Remove redirect rules:** `--del <prefix>` removes all docs with that prefix.
- **Add vanity subdomain:** update Excel with SubdomainVanityURL data, run `--upd 5 <prefix>`.
- **New locale added:** add to `ValidLocales` Firestore collection via `--upd 4 <prefix>`.
- **Debug redirect not firing:** check middleware order in `Program.cs`, verify doc exists in
  Firestore `Redirects` collection with correct host/locale/source fields.
