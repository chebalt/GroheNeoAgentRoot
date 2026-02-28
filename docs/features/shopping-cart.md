# Shopping Cart

## What it does
Manages the user's shopping cart — adding/removing products, changing quantities, applying vouchers,
assigning addresses, and promoting an anonymous cart to an authenticated one on login. ShoppingCartApi
proxies all operations to Hybris (SAP Commerce Cloud). Both anonymous and authenticated users are
supported via the same endpoints.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.ShoppingCartApi` | Cart CRUD operations via Hybris |
| Next.js routes | `/api/cart/` (4 routes) | BFF proxy to ShoppingCartApi |
| Feature package | `@grohe/cart` | Cart UI, checkout flow components |
| External | Hybris (SAP Commerce) | Source of truth for cart state, pricing |
| External | IDP (OpenID Connect) | JWT auth (optional — cart works for anonymous users) |

## Data Flow

```
Browser (cart icon / cart page)
    → GET /api/cart/get?locale=...          (anonymous or authenticated)
    → POST /api/cart/change-entry-quantity   (update quantity)
    → POST /api/cart/delete-entry            (remove item)
    → POST /api/cart/assign-addresses        (set delivery + billing)
        → ShoppingCartApi
            → Hybris cart API (baseSiteId from locale)
            → anonymous: uses cookie cart ID; authenticated: uses Hybris logged-in cart
            → return CartDetailResponse
```

## Key Business Logic

- **Anonymous vs authenticated:** anonymous users get a cart ID stored in a cookie
  (`getAnonCartCookieName(locale)`). Authenticated users' cart is managed via Hybris user session.
  Service branches on `userId == HybrisConstants.AnonymousUser`.
- **Cart promotion:** on login, anonymous cart is merged into the authenticated cart via
  `POST /promote`. This happens in the Next.js auth callback after token exchange.
- **Auto-create cart:** if anonymous user has no cart ID, Hybris creates one and the new ID is
  returned to the client for cookie storage.
- **Locale → BaseSiteId:** locale is required in all requests; `AuthorizationService` resolves
  the Hybris `BaseSiteId` from it.
- **Address assignment:** `SetAddressRequest` sets both delivery and billing addresses. Before
  assignment, `VisibleInAddressBook = false` is set on the address (prevents it appearing in address
  book). Italy-specific: `fiscalCode` field.
- **Vouchers:** add/remove via dedicated endpoints. Applied promotions included in cart detail.
- **Refit HTTP client:** `HybrisCartService` uses Refit for Hybris API calls.
- **GoogleIdTokenHandler:** custom HTTP handler for Hybris OAuth token exchange.

## Data Models

### `CartDetailResponse` (key fields)
```
{
  cartId: string,
  subtotal: float, VAT: float, VATPercentage: float,
  shippingPrice: float, totalPrice: float,
  currencyISO: string,
  totalNumberOfItems: long,
  entries: [{
    entryNumber: int?,
    quantity: long?,
    totalPrice: PriceResponse,
    product: ProductResponse
  }],
  appliedPromotions: PromotionResponse[],
  deliveryAddress: AddressResponse,
  billingAddress: AddressResponse,
  paymentInfo: PaymentInfoResponse
}
```

### `AddEntryRequest`
```
{
  sku: string,           // required
  quantity: int,         // required
  cartId: string?,       // anonymous cart ID (from cookie)
  locale: string,        // required
  authorizationToken: string?
}
```

### `SetAddressRequest`
```
{
  deliveryAddressId: string,    // required
  billingAddressId: string,     // required
  locale: string,               // required
  fiscalCode: string?           // Italy only
}
```

## Integration Tests

None yet — ShoppingCartApi has no dedicated integration tests in `integration/`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.ShoppingCartApi/Controllers/ShoppingCartController.cs` | All 9 endpoints |
| `grohe-neo-services/src/GroheNeo.ShoppingCartApi/Services/ShoppingCartService.cs` | Core business logic (679 lines) |
| `grohe-neo-services/src/GroheNeo.ShoppingCartApi/Services/Hybris/HybrisCartService.cs` | Hybris HTTP client |
| `grohe-neo-services/src/GroheNeo.ShoppingCartApi/DependencyInjectionExtensions.cs` | Refit client setup |
| `grohe-neo-services/src/GroheNeo.ShoppingCartApi/Models/Api/CartDetailResponse.cs` | Response models |
| `grohe-neo-websites/apps/website/src/app/api/cart/get/route.ts` | Cart fetch (anonymous + auth) |
| `grohe-neo-websites/apps/website/src/app/api/cart/assign-addresses/route.ts` | Address assignment handler |
| `grohe-neo-websites/packages/features/cart/` | Cart UI + checkout flow |

## Known Issues & Gotchas

- **Anonymous cart ID cookie name is locale-specific:** `getAnonCartCookieName(locale)` — if
  locale changes between requests, the cookie lookup will fail and a new cart is created.
- **Cart promotion on login:** anonymous carts are merged in the auth callback route, not by the
  cart service itself. If promotion fails, the anonymous cart may be lost.
- **Result<T> pattern:** all service methods return `Result<T>`, not exceptions.
  `ResponseHandler.HandleResult()` converts to HTTP status codes (400/401/403/404/415/500).
- **Hybris session vs cart ID:** authenticated users use `HybrisConstants.LoggedInUserCartId` —
  do not pass the anonymous cart ID for authenticated calls.

## Common Ticket Patterns

- **Adding a new cart field:** update `CartDetailResponse` model, update `HybrisCartService`
  mapper, update frontend types in `@grohe/cart`.
- **New cart action (e.g. gift wrap):** add endpoint to `ShoppingCartController`, add service
  method in `ShoppingCartService`, add Refit method in `IHybrisCartApi`, add Next.js route.
- **Italy fiscal code:** fiscal code is already supported — pass in `SetAddressRequest.fiscalCode`.
- **Voucher flow:** `POST /voucher/add` and `DELETE /voucher/delete` in ShoppingCartController.
