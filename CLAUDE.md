# CLAUDE.md — Grohe NEO Platform

## Project Overview

Full-stack headless e-commerce + content platform for GROHE (bathroom/kitchen fixtures). Four repos, one product.

| Repo | Path | Tech |
|---|---|---|
| `grohe-neo-data-loader` | `NEO/grohe-neo-data-loader/` | Python 3.13, ETL, Firestore, Google Drive |
| `grohe-neo-services` | `NEO/grohe-neo-services/` | .NET 8 microservices, Google Cloud Run |
| `integration` | `NEO/integration/` | pytest, Firestore emulator — cross-project test harness (Phase 1–6 ✅: 81 tests) |
| `grohe-neo-sitecore-xm-cloud` | `NEO/grohe-neo-sitecore-xm-cloud/` | Sitecore XM Cloud, C# resolvers |
| `grohe-neo-websites` | `NEO/grohe-neo-websites/` | Next.js 16, React 19, pnpm monorepo |

**Feature quick-reference:** `docs/features/` — one .md per feature (architecture, data flow, key files, gotchas, ticket patterns).

**Multi-agent workflow:** `.claude/agents/` — `grohe-neo-dev` (implementation across all 4 repos) and `neo-qa-engineer` (test validation, never modifies source). Both use Claude Opus and are invoked automatically via the Agent tool. Before implementing, the dev agent identifies the relevant feature and reads `docs/features/<feature>.md`, then passes the feature name to the QA agent so it can load the same context before testing. Just describe a task in the chat — the orchestrator chains them.

**Environments:** QA (testing) → UAT (staging) → PROD
**Cloud:** Google Cloud (Cloud Run, Firestore, Secret Manager, Cloud Build)
**CMS:** Sitecore XM Cloud + Sitecore Search
**E-commerce backend:** Hybris (SAP Commerce Cloud)
**Frontend hosting:** Vercel
**CI/CD:** Bitbucket Pipelines
**Main branch:** `develop`

---

## System Architecture & Data Flow

### Product Data Pipeline

```
Google Drive (CSV batches, per market/locale)
    ↓  [grohe-neo-data-loader — Cloud Run Job]
Google Firestore (product collections)
    ├── PLProductContent       → Products API
    ├── PLCategory             → Products API / Navigation API
    ├── PLVariant              → Products API
    ├── CategoryRouting        → Navigation API
    └── ProductIndexData
         ↓ [sync_product_index.py]
    products-index-updates (Firestore, operation=UPDATE|DELETE, finished=false)
         ↓ [Indexing API — triggered by Workato schedule]
    Sitecore Search Ingestion API
         → Sitecore Search index
              ↓ [Search API]
         Frontend (grohe-neo-websites)
```

### Frontend Request Flow

```
Browser / Vercel Edge
    ├── JSS GraphQL (graphql-request)
    │       → Sitecore XM Cloud Edge API  [layout, content, dictionary]
    └── Next.js API routes (52 routes)
            → .NET microservices (Google Cloud Run)
                ├── Products/Nav/Search  → Firestore + Sitecore Search
                ├── Cart/Order/User/Payment  → Hybris (SAP Commerce)
                ├── Forms  → (backend: Salesforce CRM)
                └── Project Lists  → Firestore + PDF generator
```

### Blue-Green Deployment (data-loader)

Config DB stores `database_en_gb: "products-en-gb-blue"`.
ETL loads new data to the opposite DB → updates config to point to it → calls `CLEAR_CACHE_URL`.
Previous DB retained for instant rollback.

---

## Environments

| Env | Code name | Service suffix | Data-loader config DB |
|---|---|---|---|
| QA | `testing` | `-testing` | `grohe-neo-product-testing-conf` |
| UAT | `staging` | `-staging` | `grohe-neo-product-staging-conf` |
| PROD | `production` | (none) | `grohe-neo-product-prod-conf` |

---

## Third-Party Integrations

| System | Used by | Purpose |
|---|---|---|
| **Hybris (SAP Commerce)** | Services: Cart, Order, User, Payment, Pricing | ERP, orders, customer data, pricing |
| **Google Firestore** | Data-loader + most Services | Product data store, index queues, caching |
| **Sitecore XM Cloud** | CMS repo, Services (XmCloud/Indexing APIs), Websites | Headless CMS, page layouts, content |
| **Sitecore Edge** | Websites (GraphQL) | CDN-delivered content, GraphQL endpoint |
| **Sitecore Search** | Services: Indexing API, Search API; Websites | Product & content search index |
| **Google Cloud Run** | Services | Hosting for all microservices and jobs |
| **Google Secret Manager** | Services | API keys, credentials |
| **Google Drive** | Data-loader | Source of product CSV batches |
| **IDP (OpenID Connect)** | Websites, Services | User authentication + JWT |
| **Vercel** | Websites | Frontend hosting, ISR/SSR, Edge runtime |
| **Workato** | External scheduler | Triggers Indexing API + Store Locator Job |
| **Google Places API** | Services: User API | Address autocomplete |
| **Google reCAPTCHA v3** | Services: Recaptcha API; Websites | Form spam protection |
| **Adyen** | Services: Order API | Payment processing |
| **Google Tag Manager** | Websites | Analytics orchestration |
| **Microsoft Clarity** | Websites | Session analytics |
| **OneTrust** | Websites | Cookie compliance |
| **Auth0** | Sitecore CMS (local dev) | Federated identity for CMS editors |
| **Azure Blob Storage** | Sitecore CMS | Media library |

---

## Firestore Collections Reference

| Collection | Written by | Read by | Purpose |
|---|---|---|---|
| `PLProductContent` | data-loader | Products API | Full product data per locale |
| `PLCategory` | data-loader | Products/Nav API | Category hierarchies |
| `PLVariant` | data-loader | Products API | Product variants (finish/size) |
| `CategoryRouting` | data-loader | Nav API | Category navigation routing |
| `ProductIndexData` | data-loader | data-loader sync | Source for Sitecore Search |
| `products-index-updates` | data-loader sync | Indexing API | Change queue (UPDATE/DELETE) |
| `stores-index-updates` | StoreLocatorJob | Indexing API | Store data change queue |
| `xmcloud-index-updates` | SynchronizationJob | Indexing API | XM Cloud index data |
| `cacheEntries` / `cacheRegions` | Products/Nav API | Products/Nav API | Response caching |

---

## grohe-neo-data-loader

**Runtime:** Python 3.13 Cloud Run Job (2 CPU, 4Gi RAM, 1hr timeout)

### Key Files

| File | Role |
|---|---|
| `entrypoint.sh` | Orchestrates all phases, reads Firestore config, blue-green switching |
| `main.py` | CLI: extract → transform → load |
| `pre-validation.py` | Validates CSV headers before ETL |
| `sync_product_index.py` | Syncs ProductIndexData → products-index-updates |
| `extractor.py` | Reads CSVs, validates rows via Pydantic |
| `transformer.py` | Denormalizes into 5 Firestore output models |
| `loader.py` | Writes JSON or dispatches to Firestore |
| `firestore_loader.py` | Batch-writes to Firestore |
| `google_drive_handler.py` | Downloads/uploads from Google Drive |

### Pipeline Phases

1. Load config from Firestore config DB (env-specific)
2. Resolve blue-green target database
3. Download CSV batch from Google Drive (auto-detects latest)
4. Pre-validate CSVs (headers only by default)
5. Run ETL (`main.py --to-firestore`)
6. Update config DB with new database name (blue-green switch)
7. Run sync (`sync_product_index.py`)
8. Call `CLEAR_CACHE_URL` (HTTP GET)
9. Upload summary reports to Google Drive

### Sync Logic

Compares `ProductIndexData` (main DB) vs `products-index-updates` (sync DB) per locale.
Uses SHA256 hash for change detection.
Sync doc: `{data: {document: {fields, id, locale}}, finished: false, operation: "Update"|"Delete", identifier, culture, domain_id, content_hash}`
External Sitecore crawler polls the collection and sets `finished: true` after processing.

### Environment Variables

`ENV` (QA/UAT/PROD), `LOCALE` (en_gb/de_de/nl_nl), `BATCH_FOLDER` (optional),
`LOG_LEVEL`, `GOOGLE_APPLICATION_CREDENTIALS`

---

## grohe-neo-services

**Tech:** .NET 8, Google Cloud Run, Refit, xUnit/Moq
**Solution:** `src/GroheNeoServices.sln`

### All API Services (17+)

| Service | Key Integrations |
|---|---|
| `GroheNeo.ProductsApi` | Firestore (multi-tenant), XM Cloud, PDF |
| `GroheNeo.SearchApi` | Sitecore Search Discovery API |
| `GroheNeo.IndexingApi` | Sitecore Search Ingestion, XM Cloud, Firestore, Vercel — **Workato-triggered** |
| `GroheNeo.ShoppingCartApi` | Hybris |
| `GroheNeo.OrderApi` | Hybris, Firestore, Adyen |
| `GroheNeo.UserApi` | Hybris, IDP, Google Places |
| `GroheNeo.PaymentApi` | Hybris |
| `GroheNeo.PricingApi` | Hybris |
| `GroheNeo.HybrisBearerTokenApi` | Hybris auth |
| `GroheNeo.RecaptchaApi` | Google reCAPTCHA v3 |
| `GroheNeo.XmCloudApi` | Sitecore Edge GraphQL, OAuth2 |
| `GroheNeo.ProductsDynamicNavigationApi` | Firestore, Sitecore Search |
| `GroheNeo.FormsApi` | Contact, quote, service, training forms |
| `GroheNeo.ProjectListsApi` | Firestore (multi-DB), Products API, XM Cloud, PDF |
| `GroheNeo.CodebookService` | Firestore |
| `GroheNeo.RedirectReverseProxy` | Firestore (redirect/vanity URL data) |
| `GroheNeo.TrainingApi` | IDP auth |

### Background Jobs (3)

| Job | Trigger | Purpose |
|---|---|---|
| `GroheNeo.StoreLocatorJob` | Workato | Syncs store locations → `stores-index-updates` |
| `GroheNeo.SynchronizationJob` | Workato | Copies `products-index-updates` → `xmcloud-index-updates` |
| `GroheNeo.ReverseProxyDataLoaderJob` | Manual | Loads redirect/vanity URLs from Excel → Firestore |

### Indexing API (Sitecore Search — Workato Flow)

1. Workato calls `GET /v1/indexing/products/initialize`
2. Reads `products-index-updates` (`finished=false`) from Firestore
3. Maps to Sitecore Search document format
4. POSTs to `https://discover-euc1.sitecorecloud.io/ingestion/v1`
5. Triggers Vercel cache revalidation

### External Endpoints

- **Sitecore Search Ingestion:** `https://discover-euc1.sitecorecloud.io/ingestion/v1`
- **Sitecore Search Discovery:** `https://discover-euc1.sitecorecloud.io/discover/v2/{domainId}`
- **Sitecore Edge GraphQL:** `https://edge.sitecorecloud.io/api/graphql/v1`
- **Sitecore OAuth:** `https://auth.sitecorecloud.io/oauth/token`

### Key Patterns

```csharp
// Result pattern
Result<T>.Success(value)
Result<T>.Failure("error message", StatusCodes.Status400BadRequest)

// Controller return
return ResponseHandler.HandleResult(result);

// DI — one extension method per service
public static IServiceCollection AddProjectDependencies(
    this IServiceCollection services, IConfiguration configuration)

// Validator
var validationResult = _validator.Validate(request);
if (!validationResult.IsSuccess)
    return Result<T>.Failure(validationResult.ErrorMessage!, validationResult.Status);
```

### Shared Libraries

| Library | Purpose |
|---|---|
| `GroheNeoShared` | Result<T>, IMap, ResponseHandler, caching, Secret Manager, logging |
| `GroheNeo.Foundation.ApiModels` | Result<T> / Result types |
| `GroheNeo.Foundation.ProjectApiSetup` | Standard API bootstrap (Swagger, CORS, health) |
| `GroheNeo.Foundation.Hybris` | Hybris auth, HybrisRequestValidator, GoogleIdTokenHandler |
| `GroheNeo.Foundation.GoogleFirestore` | Firestore abstraction |
| `GroheNeo.Foundation.GraphQlEdgeData` | XM Cloud GraphQL models |
| `GroheNeo.Foundation.DocumentGenerator` | PDF via PuppeteerSharp + DotLiquid |
| `GroheNeo.Feature.SitecoreSearch` | Ingestion + Discovery service wrappers |
| `GroheNeo.Feature.XmCloud` | Edge GraphQL service, OAuth2 |
| `GroheNeo.Feature.Vercel` | Vercel cache revalidation |
| `GroheNeoProductDataCommon` | Multi-tenant Firestore resolver, ITenantContext |

### Environment Config

- `appsettings.json` → base
- `appsettings.Testing.json` → QA
- `appsettings.Staging.json` → UAT
- `appsettings.Production.json` → PROD
- `appsettings.Integration.json` → local integration tests (IndexingApi, NavigationApi, ProductsApi, SearchApi)
- Sensitive values via `Environment.GetEnvironmentVariable("Key")!`
- Cloud Run service naming: `grohe-neo-{service}-testing` / `-staging` / (no suffix for prod)

### Firestore Emulator — Critical Pattern

**Any `FirestoreDbBuilder` in a service tested via the Firestore emulator must include:**

```csharp
builder.EmulatorDetection = Google.Api.Gax.EmulatorDetection.EmulatorOrProduction;
```

Without this, the .NET SDK ignores `FIRESTORE_EMULATOR_HOST` and fails with
`InvalidOperationException: Your default credentials were not found` at startup.
This applies to every builder in the service — including config bootstrapping
(`FirebaseConfigurationService`) and per-request resolvers (`FirestoreDbResolver`).
Both `GroheNeo.IndexingApi`, `GroheNeo.ProductsDynamicNavigationApi`, and
`GroheNeo.ProductsApi` have this fix applied.

### Testing

- xUnit 2.9.3 + Moq 4.20.72 + coverlet
- Naming: `[Method]_[Scenario]_[ExpectedBehavior]`
- Pattern: Arrange/Act/Assert, `CreateService()` factory method
- Target: 100% unit test coverage

---

## grohe-neo-sitecore-xm-cloud

**Tech:** Sitecore XM Cloud (SaaS headless CMS), C# .NET Framework 4.8, Helix architecture

> **Not just serialized items** — contains 4 custom C# rendering resolvers.

### Custom Resolvers (`src/src/helix/Project/GroheNeo.Project.Platform/RenderingContentsResolvers/`)

| Resolver | Purpose |
|---|---|
| `BreadcrumbsResolver.cs` | Breadcrumb trail, filters hidden items, handles language prefixes |
| `HeaderResolver.cs` | 3-level nav tree (TopNav, PrimaryNav, SecondaryNav) → JSON |
| `FooterResolver.cs` | 5 footer columns + bottom nav → JSON |
| `TableResolver.cs` | Table → Rows → Cells → JSON |

### Serialized Items

- **3,909 YAML files** in `src/src/items/`
- **11 module definitions** (`*.module.json`) — templates, renderings, layouts, site structure, workflows, roles, dictionary

### Deployment Pipelines

- `deployment-to-qa` / `deployment-to-uat` / `deployment-by-tag`
- `promote-from-qa-to-uat` / `promote-from-uat-to-prod`
- Build image: `mcr.microsoft.com/dotnet/sdk:8.0`
- Uses `dotnet sitecore` CLI for XM Cloud deployments

### Local Dev

Docker Compose: traefik, mssql (SQL Server 2017), solr (8.11.2), Sitecore CM, rendering host
External local deps: Azure Blob Storage, Auth0, Sitecore Edge

---

## grohe-neo-websites

**Tech:** Next.js 16.1.1 (App Router), React 19.2.3, pnpm 10, Turborepo, Biome

### Workspace Structure

```
apps/website/          Next.js app (52 API routes)
apps/storybook/        Storybook
jss/                   Sitecore JSS layer (api, components, atoms, types, utils)
packages/core/         api, auth, env, schemas, hooks, store, types, utils, constants
packages/features/     cart, content, footer, header, locator, my-account,
                       payment-methods, product, project-lists, tracking
packages/ui/           design-system, fonts, icons, shared, tailwind-config
automation/            Cypress + Playwright E2E tests
```

All packages use `@grohe/` namespace. Internal deps: `"workspace:*"`.

### Key Commands

```bash
pnpm dev:website          # Next.js dev server
pnpm build:website        # Production build
pnpm type:check           # TypeScript check (all packages)
pnpm biome:check          # Lint + format check
pnpm biome:fix            # Auto-fix lint/format
pnpm test:coverage        # Vitest with coverage
pnpm changeset            # Document a change
```

### Code Style (Biome — NOT ESLint/Prettier)

- Tabs (width 2), single quotes (JS/TS), double quotes (JSX attrs)
- Semicolons omitted when safe, trailing commas everywhere
- Line width 120, LF endings
- Tailwind classes must be sorted (`useSortedClasses: error`)

### Critical Lint Rules

- `noExplicitAny: error` — use `unknown` + narrowing
- `noConsole: error`
- `noProcessEnv: error` — use `@grohe/env` only
- `useImportType / useExportType: error`
- `@grohe/icons` barrel import forbidden — use direct path imports
- `next/link` forbidden — use `@grohe/shared/components/Link`

### Environment Variables (`@grohe/env` package)

Access pattern:
```typescript
import { serverEnv } from '@grohe/env/website.server'
import { clientEnv } from '@grohe/env/website.client'
```

Never use `process.env` directly (except inside `packages/core/env/`).

Key server-side required: all microservice `*_ENDPOINT` vars, `PUBLIC_URL`, `LOCALE_MAPPING`,
`MAP_API_KEY`, `PDP_PAGE_TEMPLATE_ID`, `PLP_PAGE_TEMPLATE_ID`

Key client-side required: `SITECORE_EDGE_CONTEXT_ID`, `SITECORE_XMC_DOMAIN`, plus some `*_ENDPOINT`s

### Import Conventions

```typescript
// correct — explicit subpath
import { Button } from '@grohe/design-system/actions-inputs/Button'
import { IconArrowRight16 } from '@grohe/icons/neo-16x16/arrow-right-16.tsx'
import { cn } from '@grohe/utils'

// wrong — barrel import (lint error)
import { Button } from '@grohe/design-system'
```

### Icon Sets

`neo-16x16`, `neo-24x24`, `neo-48x48`, `tabler-outline`, `tabler-filled`, `files-48x48`, `social`, `custom`

### Sitecore JSS Component Pattern

```typescript
import { withValidatedProps } from '@grohe/jss-utils'
import { MyComponentSchema } from './MyComponent.schema'

export const Default = withValidatedProps(MyComponentSchema)(async (props) => {
  return <div>...</div>
})
```

Schema (Zod + `@grohe/jss-types`):
```typescript
export const MySchema = JssDatasourcePropsSchema.extend({
  fields: z.object({ title: JsonStringValueSchema })
})
```

### Sitecore XM Cloud GraphQL

- Library: `graphql-request` via `jss/api/client.ts`
- Endpoint: `https://edge-platform.sitecorecloud.io/v1/content/api/graphql/v1?sitecoreContextId={ID}`
- Auth: OAuth2 client credentials → JWT

### Next.js API Routes (52 routes in `apps/website/src/app/api/`)

Groups: `auth/`, `product/`, `cart/`, `order/`, `user/`, `content/`, `forms/`,
`project-lists/`, `editing/` (Sitecore JSS), `navigation-settings/`, `stores/`, `locales/`, `sitemaps/`

Auth pattern: routes wrapped with `withAuth()`, JWT via `getVerifiedJWT()`.

### State Management

- **Zustand** (`@grohe/store`) — global client state (auto-reset in tests)
- **TanStack React Query v5** — server state / data fetching
- **react-hook-form** + Zod — forms

### Testing

- Unit: Vitest + Testing Library + happy-dom (tests in `__tests__/` dirs)
- E2E: Cypress (API/functional) + Playwright (visual/component)
- Run single test: `pnpm vitest run path/to/file.test.ts`

### CI/CD

- Node 22.12.0, pnpm 10, frozen lockfile
- Pre-commit (lefthook): `biome:fix` on staged files
- Pre-push: `pnpm install --frozen-lockfile` + `biome:check` + `type:check`
- Default pipeline: lint + type check + Vitest coverage + Playwright smoke tests
- Nightly: full E2E suite; reports emailed via Gmail SMTP + deployed to Vercel
