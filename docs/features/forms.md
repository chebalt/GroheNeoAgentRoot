# Forms

## What it does
Handles 5 types of form submissions from the website: contact, service request, request quote,
support/aftersales, and training registration. FormsApi validates reCAPTCHA (where required),
obtains an M2M OAuth2 token, and posts form data to Mulesoft for CRM integration. Forms are
called directly from the frontend — no Next.js API proxy route.

## Architecture

| Layer | Component | Role |
|---|---|---|
| .NET service | `GroheNeo.FormsApi` | Form validation, reCAPTCHA, Mulesoft submission |
| .NET service | `GroheNeo.RecaptchaApi` | reCAPTCHA v3 validation (shared with User Registration) |
| Feature packages | `@grohe/contact-form`, `request-quote-form`, `service-request-form`, `support-aftersales-form` | Form UI components |
| External | Mulesoft | CRM integration — receives form submissions |
| External | Google reCAPTCHA v3 | Form spam protection |
| External | Azure AD | M2M OAuth2 token issuer for Mulesoft auth |

## Data Flow

```
Browser (form page) → POSTs directly to FormsApi endpoint (no Next.js proxy)
    → FormsApi
        → reCAPTCHA validation (if required for this form type)
        → obtain M2M token via Azure AD client credentials
        → POST form data to Mulesoft API (JSON, camelCase, Bearer token)
        → log Mulesoft correlation ID
        → return 201 Created { statusCode, message }
```

## Key Business Logic

- **No Next.js API proxy:** forms call FormsApi directly from the browser. Endpoint URL from
  `serverEnv.FORMS_API_ENDPOINT` (exposed to client).
- **reCAPTCHA required for:** Contact Form, Service Request Form.
  **NOT required for:** Request Quote Form, Support/Aftersales Form, Training Registration.
- **reCAPTCHA bypass:** `X-Bypass-Captcha` header + matching `X-Bypass-Captcha-Key` env var.
  Returns 403 Forbidden if captcha fails without bypass.
- **M2M token:** fresh Azure AD client credentials token obtained per form submission. Token
  used as Bearer in Mulesoft call. No token caching (each form = new token).
- **Locale → country conversion:** `TechnicalModel.countryCode` mapped before Mulesoft call.
  Special case: `en` or `en-gb` → `UK` (not `GB`). Other locales: extract country part.
- **Mulesoft camelCase:** `JsonNamingPolicy.CamelCase` used for serialization. Field names in
  code are PascalCase; Mulesoft API expects camelCase.
- **Correlation ID logging:** Mulesoft returns a correlation ID in the response header — logged
  internally for tracing but NOT returned to client.
- **Error simplification:** detailed Mulesoft errors logged internally; simplified message
  returned to client.
- **All forms anonymous-capable:** JWT accepted but not required. All forms work for B2C users
  without login.
- **File uploads:** `ContactFormModel` includes `FileUploadModel[]` for attachments (sent to Mulesoft).

## Data Models

### `ContactFormModel` (representative)
```
{
  subject: string,
  messageContent: string,
  relatedProducts?: [{ productId?, productName? }],
  filesUpload: FileUploadModel[],    // attachments
  customerGroup?: string,
  companyName: string,
  salutation: string,
  firstName, lastName: string,
  address: AddressModel,
  phoneNumber: string,
  emailAddress: string,
  dataProtection: bool,              // required — GDPR consent
  captcha: string,                   // reCAPTCHA token
  technical: TechnicalModel          // { countryCode, timestamp, userAgent, origin }
}
```

### `FormResponse`
```
{ statusCode: int, message: string }
```

### Endpoints summary
| Form | Endpoint | reCAPTCHA |
|---|---|---|
| Contact | `POST /v1/contact-form` | Yes |
| Service Request | `POST /neo/forms/v1/service-request` | Yes |
| Request Quote | `POST /neo/forms/v1/request-quote-form` | No |
| Support/Aftersales | `POST /neo/forms/v1/aftersales-form` | No |
| Training Registration | `POST /neo/forms/v1/training-registration` | No |

## Integration Tests

None yet — FormsApi has no dedicated integration tests in `integration/`.

## Key Source Files

| File | What to look at |
|---|---|
| `grohe-neo-services/src/GroheNeo.FormsApi/Controllers/ContactFormController.cs` | Contact form endpoint |
| `grohe-neo-services/src/GroheNeo.FormsApi/Services/ContactFormService.cs` | reCAPTCHA, M2M token, Mulesoft call |
| `grohe-neo-services/src/GroheNeo.FormsApi/Services/FormServiceBase.cs` | Shared form service logic |
| `grohe-neo-services/src/GroheNeo.FormsApi/Controllers/ServiceRequestFormController.cs` | Service request endpoint |
| `grohe-neo-services/src/GroheNeo.FormsApi/Controllers/RequestQuoteFormController.cs` | Quote request endpoint |
| `grohe-neo-services/src/GroheNeo.FormsApi/Models/ContactFormModel.cs` | Full contact form model |
| `grohe-neo-services/src/GroheNeo.FormsApi/DependencyInjectionExtensions.cs` | All 5 service registrations |
| `grohe-neo-websites/packages/features/contact-form/` | Contact form UI |

## Known Issues & Gotchas

- **`en-gb` → `UK` not `GB`:** the locale-to-country mapping has this special case for Mulesoft.
  If a new locale contains `gb` or `en`, verify the mapping logic in `FormServiceBase`.
- **Fresh M2M token per request:** no token caching. If Mulesoft submission rate is high, this
  is a potential performance concern (Azure AD token endpoint latency).
- **Correlation ID is internal only:** don't rely on it being in the API response. It's only in
  logs. Use the Mulesoft admin console for tracing.
- **File upload size limits:** `FileUploadModel` sends file data to Mulesoft — verify Mulesoft
  and the reverse proxy have appropriate body size limits if users report upload failures.
- **No Next.js proxy:** if the FormsApi URL needs to change, update `FORMS_API_ENDPOINT` env var
  in Vercel settings. Clients call FormsApi directly.
- **GDPR consent required:** `dataProtection: bool` is `[Required]` on `ContactFormModel`.
  Forms without this field explicitly set to `true` will be rejected by model validation.

## Common Ticket Patterns

- **New form type:** create new controller, service, and model. Register service in
  `DependencyInjectionExtensions.cs`. Create feature package for UI.
- **New field on existing form:** add to the model with `[Required]` or nullable as appropriate.
  Update the Mulesoft mapping in the service.
- **reCAPTCHA threshold change:** update in `RecaptchaApi` service configuration.
- **Mulesoft endpoint change:** update `appsettings.json → Mulesoft:BaseUrl` per environment.
- **Azure AD credential rotation:** update Secret Manager with new `ClientId`/`ClientSecret`
  for the Azure AD app registration used by FormsApi.
