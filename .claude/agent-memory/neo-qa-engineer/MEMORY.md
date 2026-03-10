# QA Engineer Agent Memory

## Vitest Mock Patterns (grohe-neo-websites)

- `vi.mock()` factories are hoisted to top of file. Cannot reference variables declared
  outside the factory. Use `vi.hoisted()` to define mock functions that are used inside
  `vi.mock()` factories:
  ```typescript
  const { mockFn } = vi.hoisted(() => ({ mockFn: vi.fn() }))
  vi.mock('module', () => ({ fn: mockFn }))
  ```
- Test files must be in `__tests__/` directories: `.test.ts` for utils, `.test.tsx` for components.
- Vitest globals are enabled (`describe`, `it`, `expect`, `vi` available without imports).
- The `@grohe/jss-api/client` module exports `client` (GraphQLClient) and `gql` (template tag).
  Mock `gql` as: `gql: (strings: TemplateStringsArray) => strings.join('')`

## Known Pre-existing Issues

- `pnpm type:check` fails on Windows due to `@grohe/icons` setup task (svgo glob issue).
  Run `tsc --noEmit` in the specific package directory instead to check types.

## ExportSpecificationForm Dual Code Path

- `ExportSpecificationForm.tsx` has a default export component that is NOT used by the app.
  The app renders `ExportSpecificationFormContainer` -> `ExportSpecificationFormPage`.
- Only `useExportSpecificationForm` hook is imported from `ExportSpecificationForm.tsx`.
- Any changes to `ExportMutationArgs` must update BOTH `ExportSpecificationFormContainer.tsx`
  AND `ExportSpecificationForm.tsx` to avoid TS errors (or the legacy component should be removed).

## Biome Check Execution Pattern

- Do NOT run `pnpm --filter @grohe/<package> biome:check` -- most packages lack that script.
- Instead run `pnpm biome check <file-paths>` directly from `grohe-neo-websites/` root.
- Biome enforces LF line endings -- CRLF files will fail. Common on Windows when files are
  created by editors that default to CRLF.

## .NET Test Projects -- Constructor Patterns

- ProductsApiTests: `FirestoreDataService` constructor takes 6 dependencies:
  `IFirestoreDataProvider`, `IFirestoreDbDataProvider`, `IProductDataRequestValidator`,
  `ICategoryRequestValidator`, `IResponseCache`, `ISiteMapsService`
- ShoppingCartApiTests: `ShoppingCartService` constructor takes multiple dependencies
  including `IInstallationFlagService` (added EDSD-2910).
- Always check existing test files for the `CreateService()` factory method pattern before
  writing new tests -- copy the exact constructor signature.

## Optional DI Pattern (Inter-Service Communication)

- When Service A calls Service B via Refit, the Refit client interface is registered
  conditionally based on config availability (e.g., `ProductsApiBaseUrl`).
- The consuming service accepts the Refit client as nullable (`IProductsApi?`).
- Test both paths: client available (mock returns data) and client null (graceful fallback).
- Example: ShoppingCartApi -> ProductsApi for installation flags.

## Sitecore YAML Verification Checklist

- All GUIDs must be unique across the entire `items/` tree
- Template ID `455a3e98-a627-4b40-8035-e683a0331ac7` is standard Sitecore field template
- Field types to verify: Checkbox (Shared=1), General Link, Rich Text, Single-Line Text
- Check `__Sortorder` for field ordering within templates

## Package Test Scripts

- `@grohe/product-list` and `@grohe/product` have NO `test:coverage` script -- run via root `pnpm vitest run <path>`
- Heavy deps for ProductCard tests: mock `useAddToCartMutation`, `useCookie`, `showToast`,
  `useEcoParticipationLabel`, `useFormattedPrice`, `hidePriceForNonTransactable`,
  `AddProductToList`, `useAddProduct`, `next/navigation`, `useMaxVisibleColorsCount`

## Zoovu Configure-and-Buy (EDSD-2910)

- PLP `configureAndBuyBaseUrl` from Sitecore `ConfigureAndBuyLink` on PLP datasource; PDP has separate field
- Empty `configureAndBuyBaseUrl` ('' fallback) is falsy -- prevents Zoovu URL assembly in `useRenderProductCard`
- PDP checks only `isZoovuConfigurable`; PLP checks BOTH plus assembled `zoovuConfigLink`
- Search API: `isZoovuConfigurable` (bool?), `zoovuConfigLink` (string?) -- camelCase via JsonPropertyName

## POST Endpoint + HttpTenantContext Incompatibility (EDSD-2910 Bug)

- ProductsApi `HttpTenantContext` reads `locale` from query string ONLY (line 24 of `FireStoreDbResolver.cs`)
- All existing endpoints are GET with `?locale=...` query param -- this works
- New POST `/product/v1/installation-flags` passes locale in JSON body -- HttpTenantContext gets empty locale
- Result: `InvalidOperationException: database config for locale '' (key 'database_') not found` -> 500
- ShoppingCartApi Refit client also sends locale in body only -> same 500
- Fix: either add `[Query] string locale` to Refit call, or change endpoint to use query param

## Running ProductsApi Locally Against Emulator

Required env vars (from docker-compose):
```
ASPNETCORE_ENVIRONMENT=Integration
FIRESTORE_EMULATOR_HOST=localhost:8080
configuration_project_id=demo-project
configuration_table=(default)
NeoXMCloudApiBaseUrl=http://localhost:8081
GCLOUD_PROJECT=demo-project
```
Must run in Release mode (`--configuration Release`) to skip `#if DEBUG` credential loading.
Seed `configuration/config` doc with `database_<locale>` entries before starting.

## CSV Fixture Zoovu Data

- SKU `30591000INST` has `is_zoovu_configurable=TRUE` and `zoovu_config_link=?aid%5B2788008%5D=265050665&step=1`
- Only available in it-IT locale in the fixture data (not en-GB)
- Non-configurable SKU for testing: `00016000` (it-IT)
