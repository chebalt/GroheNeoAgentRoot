# My Account

## What it does
Allows authenticated users to view and manage their profile (name, company, language), addresses
(CRUD), password, credit cards, order history (see checkout.md), and market-specific settings.
All operations require JWT. Address autocomplete uses Google Places API and is available without
login. UserApi proxies user data between IDP and Hybris.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.UserApi` | User profile, addresses, market config |
| Next.js routes | `/api/user/` (10+ routes) | BFF proxy — adds locale, handles 204→200 |
| Feature package | `@grohe/my-account` | My account UI pages |
| External | Hybris (SAP Commerce) | Address storage, market config, ERP user data |
| External | IDP (OpenID Connect) | JWT auth, user attribute updates |
| External | Google Places API | Address autocomplete + place detail lookup |

## Data Flow

```
Browser (My Account pages) [all routes require JWT via withAuth middleware]
    → GET  /api/user/info                    → GET /v1/info (UserApi)
    → PUT  /api/user/info                    → PUT /v1/info (UserApi → IDP)
    → GET  /api/user/addresses/get           → GET /v1/address (UserApi → Hybris)
    → POST /api/user/addresses/create        → POST /v1/address
    → PUT  /api/user/addresses/edit          → PUT /v1/address
    → DELETE /api/user/addresses/delete      → DELETE /v1/address
    → POST /api/user/addresses/autocomplete  → POST /v1/addressAutocomplete (Google Places)
    → GET  /api/user/hybris-info             → GET /v1/user-erp (UserApi → Hybris)
    → GET  /api/user/market-config           → GET /v1/marketConfig (UserApi → Hybris)
    → PUT  /api/user/password                → PUT /v1/users/password (UserApi → IDP)
    → DELETE /api/user                       → DELETE /v1/users (UserApi → IDP)
```

## Key Business Logic

- **All routes use `withAuth` middleware** except address autocomplete and address detail
  (Google Places — no auth needed).
- **Dual address sources:** delivery AND billing addresses fetched separately from Hybris, then
  merged by ID into a single response list.
- **Locale parsing:** expects `xx-YY` format. Country code extracted as `[3:]` substring for
  Hybris API calls. Do not pass `xx-yy` (lowercase country).
- **Market config anonymous:** even for authenticated requests, `GetMarketConfig` uses an
  anonymous Hybris token (sets `AuthorizationToken = null`).
- **204 → 200 wrapping:** Next.js routes convert Hybris 204 No Content responses to 200 OK
  with `{success: true}`. Frontend code must handle both patterns if you bypass the BFF.
- **JWT claim extraction:** `IIdpTokenHelper` extracts `userId`, `locale`, `country`, `email`
  from JWT claims at the controller level — reused for all downstream calls.
- **Address `VisibleInAddressBook`:** when assigning a checkout address, it's set to `false`
  to prevent it appearing in the address book. Address book CRUD uses separate endpoints.
- **Google Places locale mapping:** `POST /v1/addressAutocomplete` accepts custom locale but
  may convert format for Places API. API key from env config.
- **`ChangeAttributesRequest`:** separates standard user attributes (email, firstName, etc.)
  from Neo-specific attributes (invitationCode, companyPosition, vatin, userType).

## Data Models

### `ChangeAttributesRequest`
```
{
  userAttributes: {
    email, salutation, firstName, lastName,
    language, country, company, mobilePhone,
    address, termsAndConditions, privacyPolicy
  },
  neoAttributes?: {
    invitationCode, companyAddition, companyPosition,
    userType, vatin
  }
}
```

### Address models
```
// CreateOrUpdateAddressRequest
{
  address: {
    id?, firstName, lastName, streetAndNumber,
    city, postalCode, country,
    defaultAddress: bool,
    deliveryAddress: bool,
    billingAddress: bool
  },
  locale: string
}

// Autocomplete request
{ input: string, locale: string }

// Autocomplete response
{ suggestions: [{ placeId, mainText, secondaryText }] }

// Address detail response
{ formattedAddress, streetNumber, streetName, city, postalCode, country }
```

## Integration Tests

None yet — UserApi has no dedicated integration tests in `integration/`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.UserApi/Controllers/UserController.cs` | User info, password, account deletion |
| `grohe-neo-services/src/GroheNeo.UserApi/Controllers/AddressController.cs` | Address CRUD, market config, Google Places |
| `grohe-neo-services/src/GroheNeo.UserApi/Services/AddressService.cs` | Address business logic, Hybris merge |
| `grohe-neo-services/src/GroheNeo.UserApi/Services/GooglePlaces/GooglePlacesService.cs` | Google Places wrapper |
| `grohe-neo-services/src/GroheNeo.UserApi/DependencyInjectionExtensions.cs` | DI, mappers, validators |
| `grohe-neo-websites/apps/website/src/app/api/user/info/route.ts` | User info GET/PUT proxy |
| `grohe-neo-websites/apps/website/src/app/api/user/addresses/get/route.ts` | Address list proxy |
| `grohe-neo-websites/packages/features/my-account/` | My account UI |

## Known Issues & Gotchas

- **Locale case sensitivity:** `xx-YY` format is expected. `xx-yy` (all lowercase) may work in
  some paths but country code extraction (`locale[3:]`) gives lowercase country — verify Hybris
  accepts it.
- **Market config uses anonymous token** even for authenticated users. If you see unexpected
  pricing/shipping options, check that `AuthorizationToken` is null for this call.
- **Dual address fetch:** addresses are fetched in two separate Hybris calls (delivery + billing),
  then merged. If a user has both delivery and billing set to the same address, it appears once.
- **Google Places API key:** stored in environment config (Secret Manager in GCP). If
  autocomplete fails, verify the API key quota has not been exceeded.

## Common Ticket Patterns

- **New user attribute:** add to `ChangeAttributesRequest.userAttributes`, update IDP mapper,
  update `GetUserResponse`, update frontend form in `@grohe/my-account`.
- **New Neo attribute:** add to `ChangeAttributesRequest.neoAttributes`, update IDP mapper.
- **New address field:** update `AddressRequest`, `HybrisAddress`, Hybris mapper.
- **Market config field:** update `GetMarketConfigResponse`, update Hybris market config mapper.
- **Account deletion:** `DELETE /v1/users` calls IDP deregister. Check IDP for any cascading
  cleanup (Hybris account, consent records).
