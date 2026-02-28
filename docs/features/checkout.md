# Checkout

## What it does
Orchestrates the checkout flow — creating orders, handling Adyen payment (including 3D Secure
redirects), viewing order history, and downloading invoices/shipping labels. OrderApi manages
order lifecycle; PaymentApi manages stored credit cards and available payment methods. Both
talk to Hybris; order payments go through Adyen.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.OrderApi` | Order creation, order history, invoice/label download |
| .NET service | `GroheNeo.PaymentApi` | Payment methods, stored credit card CRUD |
| Next.js routes | `/api/order/` (5 routes) | BFF proxy — order creation handles 3DS logic |
| Feature package | `@grohe/cart` | Checkout flow UI (same package as shopping cart) |
| External | Hybris (SAP Commerce) | Order placement, order history, invoice data |
| External | Adyen | Payment processing, 3DS challenge |
| External | Firestore | HeyLight invoice/shipping label tracking |

## Data Flow

```
Browser (checkout page)
    → POST /api/order/createOrder               (payment + order)
        → OrderApi
            → Hybris: create order
            → Adyen: process payment
            → if resultCode == "redirect": return 3DS action to client
            → client POSTs to Adyen 3DS URL, then redirects back
    → GET /api/order/orders                     (order history)
    → GET /api/order/orderDetails?id=...        (single order)
    → GET /api/order/invoices?orderId=...       (invoice PDF download)
```

## Key Business Logic

- **Order creation:** validates `CreateOrderRequest`, gets Hybris auth token, creates order via
  `HybrisOrderService`, processes Adyen payment response.
- **Adyen result codes handled in Next.js route:**
  - `Redirect` → returns 3DS action object to client (client-side redirect + form POST)
  - `Authorised` / `Pending` / `Received` → success (redirect to confirmation)
  - `Refused` → 422 Unprocessable Entity
  - `Cancelled` → 400 Bad Request
- **3DS flow:** client receives `action.url` + `action.data` (MD, PaReq), posts form to Adyen 3DS
  URL, then Adyen redirects back to the return URL with result.
- **Page size limit on order history:** hard limit of 25 to prevent N+1 Hybris calls.
- **Payment methods:** fetched from Hybris per locale — different markets have different payment
  options (card, bank transfer, etc.).
- **JWT required for order operations** (history, detail, invoices). Order creation accepts
  optional JWT (anonymous checkout supported via Hybris).
- **Firestore in OrderApi:** used for HeyLight invoice/shipping label tracking (not product data).
- **Locale → BaseSiteId:** `AuthorizationService` resolves Hybris context from locale.

## Data Models

### `CreateOrderRequest`
```
{
  locale: string,                   // required
  paymentMethodType: string,        // "card", "external"
  paymentMethodId: string?,         // stored card ID
  brand: string?,                   // "VISA", "MC", etc.
  encryptedSecurityCode: string?,   // Adyen-encrypted CVV
  isExternalPaymentMethod: bool?,
  referenceNumber: string?          // external payment reference
}
```

### `CreateOrderResponse`
```
{
  order: {
    code: string,   // order code
    guid: string,
    status: string
  },
  adyen: {
    resultCode: string,   // "Authorised"|"Pending"|"Received"|"Refused"|"Cancelled"|"Redirect"
    action: {             // present only for redirect
      type: string,       // "redirect"
      method: string,     // "POST"
      url: string,
      data: { MD, PaReq }
    }
  }
}
```

### `GetOrderHistoryRequest`
```
{
  locale: string,
  pageSize: int?,      // max 25
  currentPage: int?,
  sort: string?,       // "byDate"
  statuses: string?    // "CANCELLED,CHECKED,VALID"
}
```

## Integration Tests

None yet — OrderApi/PaymentApi have no dedicated integration tests in `integration/`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.OrderApi/Controllers/OrdersController.cs` | Order endpoints |
| `grohe-neo-services/src/GroheNeo.OrderApi/Services/CreateOrderService.cs` | Order creation + Adyen handling |
| `grohe-neo-services/src/GroheNeo.OrderApi/Services/OrdersService.cs` | Order history/detail retrieval |
| `grohe-neo-services/src/GroheNeo.OrderApi/Services/Hybris/HybrisOrderService.cs` | Hybris HTTP client |
| `grohe-neo-services/src/GroheNeo.PaymentApi/Controllers/PaymentController.cs` | Payment method endpoints |
| `grohe-neo-services/src/GroheNeo.OrderApi/DependencyInjectionExtensions.cs` | DI + Firestore config |
| `grohe-neo-websites/apps/website/src/app/api/order/createOrder/route.ts` | 3DS handling logic (223 lines) |
| `grohe-neo-services/src/GroheNeo.OrderApi/Models/Api/CreateOrderResponse.cs` | Adyen response models |

## Known Issues & Gotchas

- **3DS handling is in the Next.js route, not the .NET service:** `createOrder/route.ts` parses
  `adyen.resultCode` and decides whether to return 3DS data or redirect to confirmation.
  The .NET service just returns the raw Adyen response.
- **`encryptedSecurityCode` must be redacted in logs:** Next.js route logs the request with
  `encryptedSecurityCode` replaced. If you add logging elsewhere, redact this field.
- **Order history N+1:** `GetOrderHistory` fetches each order detail separately — page size 25
  cap is a safety valve. Don't raise the cap without validating Hybris performance.
- **Firestore in OrderApi is for HeyLight only:** different from product Firestore.
  Don't confuse with PLProductContent etc.
- **Payment methods differ by market:** test with the correct locale, not just any locale.

## Common Ticket Patterns

- **New payment method type:** add to `paymentMethodType` handling in `CreateOrderService`,
  update `CreateOrderRequest` model, update Next.js checkout UI.
- **New Adyen result code:** add handler in `createOrder/route.ts` and in `CreateOrderService`.
- **Order status filter:** add to `statuses` query param in `GetOrderHistoryRequest`.
- **Invoice/label download:** `GET /v1/invoices/{orderId}/{documentId}` and
  `GET /v1/shippingLabels/{shippingLabelId}` — both proxy to Hybris/HeyLight.
