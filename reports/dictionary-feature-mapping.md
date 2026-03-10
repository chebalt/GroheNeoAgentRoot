# Sitecore Dictionary-to-Feature Mapping Report

> Generated: 2026-03-09
> Source: PROD Sitecore dictionary export (`data_input/JIRA/dict-prod-extracted/`)
> Verification: codebase search against `grohe-neo-websites` (T() key usage)

## How Dictionary Keys Work

Sitecore dictionary items live under `Dictionary/Components/` in the XM Cloud content tree. The GraphQL dictionary query returns flat key-value pairs where the key is a dot-separated path derived from the Sitecore item hierarchy (e.g., `cart.empty_cart`, `checkout.summary.billing_address`). The frontend accesses them via talkr's `useT()` hook:

```tsx
const { T } = useT()
T('cart.empty_cart')  // returns the translated string
```

---

## Table of Contents

1. [Product Detail Page (PDP)](#1-product-detail-page-pdp)
2. [Product Listing Page (PLP) and Product Catalogue](#2-product-listing-page-plp-and-product-catalogue)
3. [Shopping Cart](#3-shopping-cart)
4. [Checkout](#4-checkout)
5. [My Account](#5-my-account)
6. [Project Lists](#6-project-lists)
7. [Forms (Shared)](#7-forms-shared)
8. [Contact Form](#8-contact-form)
9. [Service Request Form](#9-service-request-form)
10. [Support/Aftersales Form](#10-supportaftersales-form)
11. [Request Quote Form](#11-request-quote-form)
12. [Training Courses](#12-training-courses)
13. [Store Locator](#13-store-locator)
14. [Search](#14-search)
15. [Header and Navigation](#15-header-and-navigation)
16. [Content Components (Shared)](#16-content-components-shared)
17. [Payment Methods (Settings)](#17-payment-methods-settings)
18. [User Registration](#18-user-registration)
19. [Pricing and Product Card (Cross-Feature)](#19-pricing-and-product-card-cross-feature)
20. [Shared UI / Generic](#20-shared-ui--generic)
21. [Unused or Backend-Only Dictionary Groups](#21-unused-or-backend-only-dictionary-groups)

---

## 1. Product Detail Page (PDP)

**Feature doc:** `docs/features/pdp.md`
**Description:** Displays full product detail including images, specs, variants (finish/size), pricing, downloads, and spare parts. The PDP dictionary group provides copy/labels for interactive elements.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| PDP | `pdp.copy_product_number` | `Components/PDP/Copy product number` | "Copy product number" button on PDP |
| PDP | `pdp.copy_ean` | `Components/PDP/Copy EAN` | "Copy EAN" button on PDP (trade code) |
| PDP | `pdp.copy_rsk` | `Components/PDP/Copy RSK` | "Copy RSK" button (Swedish trade code) |
| PDP | `pdp.copy_vvs` | `Components/PDP/Copy VVS` | "Copy VVS" button (Danish trade code) |
| PDP | `pdp.copy_nrf` | `Components/PDP/Copy NRF` | "Copy NRF" button (Norwegian trade code) |
| PDP | `pdp.decrease_quantity` | `Components/PDP/Decrease quantity` | Quantity selector "-" aria label |
| PDP | `pdp.increase_quantity` | `Components/PDP/Increase quantity` | Quantity selector "+" aria label |
| PDP | `pdp.product_quantity_label` | `Components/PDP/Product quantity label` | "Quantity" label next to quantity input |
| PDP | `pdp.select_product_finish` | `Components/PDP/Select product finish` | Finish dropdown/selector label |
| PDP | `pdp.select_product_size` | `Components/PDP/Select product size` | Size dropdown/selector label |
| PDP | `pdp.no_size_image_message` | `Components/PDP/No size image message` | Message when no size image is available |
| PDP | `pdp.spare_part_latest` | `Components/PDP/PDP Spare Part Latest` | Label for latest spare part version |
| PDP | `pdp.spare_part_version` | `Components/PDP/PDP Spare Part Version` | Label for spare part version number |
| PDP | `pdp.sku_data_missing` | `Components/PDP/SKU data not found` | Error message when SKU data cannot be loaded |
| PDP (Downloads) | _(CMS rendering fields)_ | `Components/PDP/Downloads BIM`, `Downloads CAD ...`, `Downloads DIM`, `Downloads EPD`, `Downloads TPI`, `Downloads Care Label`, `Downloads Flow Diagram` | Labels for PDP download section tabs (BIM, CAD 2D/3D DWG/DXF/STP, DIM, DIM Inch, EPD, TPI, Care Label, Flow Diagram). Used as rendering field values, not T() keys directly. |
| PDP | _(rendering field)_ | `Components/PDP/Gallery navigation accessibility text` | Screen reader text for the PDP image gallery navigation |
| PDP | _(rendering field)_ | `Components/PDP/Read more about product details` / `Read less about product details` | Expand/collapse toggle text for product description |

**Key files:** `packages/features/product/src/PDPProductMain/`, `packages/features/product/src/PDPAccordion/`, `packages/features/product/src/components/pdp/`, `packages/ui/shared/src/components/QuantityInput.tsx`

---

## 2. Product Listing Page (PLP) and Product Catalogue

**Feature docs:** `docs/features/plp.md`, `docs/features/product-catalogue.md`, `docs/features/product-filters.md`
**Description:** Paginated product listing grids with filtering, sorting, and "load more" functionality. Used for category browse pages and search results.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Product | `product.listing_grid_switcher` | `Components/Product/Product listing grid switcher` | Grid/list view toggle button label |
| Product | `product.load_more_button_ariaLabel` | `Components/Product/Load more button Label` | "Load more" button aria label on PLP |
| Product | _(rendering field)_ | `Components/Product/Product listing grid` | Grid layout configuration label |
| Product | _(rendering field)_ | `Components/Product/Product listing items count` | "{n} items" count text |
| Filters | _(CMS rendering fields)_ | `Components/Filters/Apply`, `Clear all`, `Desktop trigger label`, `Mobile trigger label`, `Show results`, `Sheet label`, `Min`, `Max`, `Remove` | Filter panel UI labels. These appear to be delivered as Sitecore rendering fields to the PLP/search components, not consumed via T() keys. |
| Browse All | _(CMS rendering field)_ | `Components/Browse All` | "Browse all" link label on category pages |
| No results | `no_results.heading` | `Components/No results/heading` | "No results" heading when PLP/search returns empty |
| No results | `no_results.description` | `Components/No results/description` | "No results" description text |

**Key files:** `packages/features/product-list/src/components/ProductListingGrid/`, `packages/features/search-results/src/`

---

## 3. Shopping Cart

**Feature doc:** `docs/features/shopping-cart.md`
**Description:** Cart page showing cart items, coupon input, price summary, and empty cart state.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Cart | `cart.apply_coupon_code` | `Components/Cart/Apply a coupon code` | Coupon code submit button label |
| Cart | `cart.cancel` | `Components/Cart/Cancel` | Cancel button in cart actions |
| Cart | `cart.code_character_limit` | `Components/Cart/Code character limit` | Validation error: coupon code max length |
| Cart | `cart.code_not_valid` | `Components/Cart/Code not valid` | Validation error: invalid coupon code |
| Cart | `cart.code_required` | `Components/Cart/Code required` | Validation error: coupon code required |
| Cart | `cart.coupon_code` | `Components/Cart/Coupon code` | Coupon code input label |
| Cart | `cart.coupon_successfully_applied` | `Components/Cart/Coupon successfully applied` | Success toast after coupon applied |
| Cart | `cart.discounts` | `Components/Cart/Discounts` | "Discounts" label in price summary |
| Cart | `cart.empty_cart` | `Components/Cart/Empty cart` | Empty cart state heading |
| Cart | `cart.id` | `Components/Cart/ID` | Cart ID label |
| Cart | `cart.modal_description` | `Components/Cart/Modal description` | Remove item confirmation modal text |
| Cart | `cart.product_number` | `Components/Cart/Product number` | Product number label on cart item tile |
| Cart | `cart.remove_cart` | `Components/Cart/Remove` | Remove all items button label |
| Cart | `cart.remove_cart_product` | _(derived)_ | Remove single product button label |
| Cart | `cart.remove_item` | `Components/Cart/Remove item` | Remove item action label |
| Cart | `cart.shipping` | `Components/Cart/Shipping` | "Shipping" label in price summary |
| Cart | `cart.subtotal` | `Components/Cart/Subtotal` | "Subtotal" label in price summary |
| Cart | `cart.total_order` | `Components/Cart/Total order` | "Total order" label in price summary |
| Cart | `cart.vat` | `Components/Cart/VAT` | "VAT" label in price summary |
| Cart | `ModalDescription.modal_empty_cart_description` | `Components/Cart/Modal empty cart description` | Empty cart modal confirmation text |

**Key files:** `packages/features/cart/src/components/shopping-cart/`, `packages/core/schemas/src/voucher.ts`

---

## 4. Checkout

**Feature doc:** `docs/features/checkout.md`
**Description:** Multi-step checkout flow including address entry, payment, order summary, and 3DS handling.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Checkout / Autocomplete | `checkout.autocomplete.find_address` | `Components/Checkout/Autocomplete/FindAddress` | Address autocomplete placeholder text |
| Checkout / Autocomplete | `checkout.autocomplete.not_found` | `Components/Checkout/Autocomplete/NotFound` | "Address not found" message |
| Checkout / Autocomplete | `checkout.autocomplete.searching_addresses` | `Components/Checkout/Autocomplete/SearchingAddresses` | "Searching..." loading text |
| Checkout / General | `checkout.general.confirm` | `Components/Checkout/General/Confirm` | "Confirm" button label |
| Checkout / General | `checkout.general.default` | `Components/Checkout/General/Default` | "Default" badge label for addresses |
| Checkout / General | `checkout.general.delete` | `Components/Checkout/General/Delete` | "Delete" button label |
| Checkout / General | `checkout.general.edit` | `Components/Checkout/General/Edit` | "Edit" button label |
| Checkout / General | `checkout.general.edit_billing_address_ariaLabel` | `Components/Checkout/General/Edit billing address label` | Aria label for edit billing address button |
| Checkout / General | `checkout.general.edit_shipping_address_ariaLabel` | `Components/Checkout/General/Edit shipping address label` | Aria label for edit shipping address button |
| Checkout / Modal | `checkout.modal.back` | `Components/Checkout/Modal/Back` | "Back" button in checkout modals |
| Checkout / Modal | `checkout.modal.both_addresses_warning` | `Components/Checkout/Modal/Both addresses warning` | Warning when editing both addresses |
| Checkout / Modal | `checkout.modal.cardInformationLabel` | `Components/Checkout/Modal/Card Information Label` | Label for card info section |
| Checkout / Modal | `checkout.modal.edit_billing_address.title` | `Components/Checkout/Modal/Edit Billing Address Title` | Edit billing address modal title |
| Checkout / Modal | `checkout.modal.edit_delivery_address.title` | `Components/Checkout/Modal/Edit Delivery Address Title` | Edit delivery address modal title |
| Checkout / Modal | `checkout.modal.setDefaultAddress.confirm` | `Components/Checkout/Modal/Set default address` | "Set as default" confirmation button |
| Checkout / Modal | `checkout.modal.verifyYourCardTitle` | `Components/Checkout/Modal/Verify Your Card Title` | 3DS card verification modal title |
| Checkout / Notifications | `checkout.notification.addressAddedSuccessfully` | `Components/Checkout/Notifications/Address added succesfully` | Address added success toast |
| Checkout / Notifications | `checkout.notification.addressDeletedSuccessfully` | `Components/Checkout/Notifications/Address Deleted Successfully` | Address deleted success toast |
| Checkout / Notifications | `checkout.notification.addressEditedSuccessfully` | `Components/Checkout/Notifications/Address Edited Successfully` | Address edited success toast |
| Checkout / Payment | `checkout.payment.selectCreditCard.confirm` | `Components/Checkout/Payment/Select credit card` | Credit card selection confirm button |
| Checkout / Payment | `checkout.payment.selectCreditCard.title` | _(derived)_ | Credit card selection modal title |
| Checkout / Summary | `checkout.summary.billing_address` | `Components/Checkout/Summary/Billing address` | "Billing address" section heading |
| Checkout / Summary | `checkout.summary.button.change_billing_address` | `Components/Checkout/Summary/Change billing address` | "Change billing address" button |
| Checkout / Summary | `checkout.summary.button.change_delivery_address` | `Components/Checkout/Summary/Change delivery address` | "Change delivery address" button |
| Checkout / Summary | `checkout.summary.delivery_address` | `Components/Checkout/Summary/Delivery Address` | "Delivery address" section heading |
| Checkout / Summary | `checkout.summary.price` | `Components/Checkout/Summary/Price` | "Price" column header in order summary |
| Checkout / Summary | `checkout.summary.quantity` | `Components/Checkout/Summary/Quantity` | "Quantity" column header in order summary |
| Checkout / Stepper | _(CMS rendering fields)_ | `Components/Checkout/Stepper/Step1..4` | Stepper labels (Delivery, Payment, Review, Confirm). Delivered as Sitecore rendering fields. |
| Checkout / error | `checkout.error.authorization.failed` | _(derived)_ | Payment authorization failure message |
| Order | `order.return_label` / `order.return_labels` | _(derived)_ | Return label button text (singular/plural) |

**Key files:** `packages/features/cart/src/components/checkout/`, `packages/features/cart/src/hooks/mutations/`

---

## 5. My Account

**Feature doc:** `docs/features/my-account.md`
**Description:** Account settings (profile, addresses, payment methods, order history). Includes address management shared with checkout.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| MyAccount / Addresses | `my_account.addresses.empty_state.title` | `Components/MyAccount/Addresses/No addresses added` | Empty state when user has no addresses |
| MyAccount / Addresses | _(CMS rendering fields)_ | `Components/MyAccount/Addresses/Title`, `Add a billing address`, `Add a delivery addess`, `Billing addresses`, `Delivery addresses` | Section headings and button labels for address management page |
| MyAccount / Button | _(CMS rendering fields)_ | `Components/MyAccount/Button/Add Billing Address Label`, `Add Delivery Address Label` | Button labels for adding addresses |
| MyAccount / Modal | _(CMS rendering fields)_ | `Components/MyAccount/Modal/DeleteAddressModal` | Delete address confirmation modal text |
| MyAccount / Notification | _(CMS rendering fields)_ | `Components/MyAccount/Notification/AddressDeletedSuccessfully` | Toast notification after address deletion |
| Status / Hybris | _(server-side mapping)_ | `Components/Status/Hybris/Cancelled`, `Completed`, `Created`, `Payment Authorized`, etc. | 26 order status display labels. These are used to translate Hybris status codes into human-readable labels for the Order History page. Not consumed via T() keys -- the `statusDisplay` field from Hybris/backend carries these. |

**Key files:** `packages/features/my-account/src/components/MyAccountSettings/Addresses/`, `packages/features/my-account/src/components/OrderListing/`

---

## 6. Project Lists

**Feature doc:** `docs/features/project-list.md`
**Description:** Authenticated users save products to named project lists (wishlists for professionals). Features CRUD, sections, bulk import, duplication, PDF export, and download of BIM/CAD files.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Project Lists | `project_lists.add_to_project_list` | `Components/Project Lists/Add To Project List` | "Add to project list" button (PDP + product cards) |
| Project Lists | `project_lists.create_new_project_list` | `Components/Project Lists/Create New Project List` | "Create new project list" button/modal title |
| Project Lists | `project_lists.project_list_name` | `Components/Project Lists/Project List Name` | Project list name input label |
| Project Lists | `project_lists.project_list_description` | `Components/Project Lists/Project List Description` | Project list description input label |
| Project Lists | `project_lists.add_new_section` | `Components/Project Lists/Add New Section` | "Add new section" button label |
| Project Lists | `project_lists.section_name` | `Components/Project Lists/Section Name` | Section name input label |
| Project Lists | `project_lists.rename_section` | `Components/Project Lists/Rename Section` | "Rename section" menu item |
| Project Lists | `project_lists.delete_from_list` | `Components/Project Lists/Delete from project list` | "Delete from project list" menu item |
| Project Lists | `project_lists.delete_list` | `Components/Project Lists/Delete project list` | "Delete project list" menu item |
| Project Lists | `project_lists.delete_section` | `Components/Project Lists/Delete section` | "Delete section" menu item |
| Project Lists | `project_lists.duplicate_list` | `Components/Project Lists/Duplicate project list` | "Duplicate project list" menu item |
| Project Lists | `project_lists.duplicate_product` | `Components/Project Lists/Duplicate product` | "Duplicate product" menu item |
| Project Lists | `project_lists.duplicate_section` | `Components/Project Lists/Duplicate section` | "Duplicate section" menu item |
| Project Lists | `project_lists.move_to_different_list` | `Components/Project Lists/Move to different list` | "Move to different list" menu item |
| Project Lists | `project_lists.move_to_section` | `Components/Project Lists/Move To Section` | "Move to section" menu item |
| Project Lists | `project_lists.edit_name_and_description` | `Components/Project Lists/Edit name and description` | "Edit" menu item for list name/description |
| Project Lists | `project_lists.search_and_add_products` | `Components/Project Lists/Search and Add Products` | Search-and-add modal title |
| Project Lists | `project_lists.search_product_by_sku` | `Components/Project Lists/Search Product By Sku` | SKU search input placeholder |
| Project Lists | `project_lists.bulk_import_products` | `Components/Project Lists/Bulk Import Products` | "Bulk import" button label |
| Project Lists | `project_lists.export_as_spec` | `Components/Project Lists/Export and specification document` | "Export as specification" button |
| Project Lists | `project_lists.export_document` | `Components/Project Lists/Export document PDF` | PDF export button label |
| Project Lists | `project_lists.download_files` | `Components/Project Lists/Download files` | "Download files" button (BIM/CAD) |
| Project Lists | `project_lists.cover_image` | `Components/Project Lists/Cover Image` | Cover image section label |
| Project Lists | `project_lists.add_your_logo` | `Components/Project Lists/Add Your Logo` | "Add your logo" button |
| Project Lists | `project_lists.add_your_contact_details` | `Components/Project Lists/Add Your Contact Details` | "Add contact details" button |
| Project Lists | `project_lists.copy_link` | `Components/Project Lists/Copy Link` | "Copy link" menu item |
| Project Lists | `project_lists.include_specifications` | `Components/Project Lists/Include specifications` | Checkbox label in export form |
| Project Lists | `project_lists.select_language_for_export` | `Components/Project Lists/Select language for export` | Language selector in export form |
| Project Lists | `project_lists.product_number` | `Components/Project Lists/Product Number` | Product number label in list |
| Project Lists | `project_lists.product_not_available` | `Components/Project Lists/Product Not Available` | Message for unavailable products |
| Project Lists | `project_lists.add_custom_label` | `Components/Project Lists/Add Custom Label` | "Add custom label" button |
| Project Lists | `project_lists.custom_label` | `Components/Project Lists/Custom Label` | Custom label input label |
| Project Lists | `project_lists.where_to_buy` | `Components/Project Lists/Where To Buy` | "Where to buy" link label |
| Project Lists | _(~40 more keys)_ | `Components/Project Lists/*` | Validation messages, success/error toasts, form labels, import modals, section management. Full list: 121 unique T() keys with `project_lists.*` prefix. |
| Project Lists (PDF) | _(server-side only)_ | `Components/Project Lists/Specification`, `Index`, `Colour`, `Contact Details`, `Rrp Excluding Vat`, `Rrp Including Vat`, `Default Section Header`, `Specification Document First Page Note`, etc. | These keys are fetched server-side by `ProjectListsApi.DictionaryItemsService` (via XM Cloud GraphQL) for use in the DotLiquid PDF specification document template. Not used via T() in the frontend. |

**Key files:** `packages/features/project-lists/src/`, `grohe-neo-services/src/GroheNeo.ProjectListsApi/Services/DictionaryItemsService.cs`

---

## 7. Forms (Shared)

**Feature doc:** `docs/features/forms.md`
**Description:** The `Form` dictionary group provides shared labels and validation messages used across all form types: registration, contact, service request, support, request quote, training, checkout addresses, and My Account settings.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Form | `form.firstName.label` | `Components/Form/FirstName` | "First name" field label |
| Form | `form.firstName.error` | _(sub-item)_ | Required validation error |
| Form | `form.firstName.errorInvalid` | _(sub-item)_ | Format validation error |
| Form | `form.lastName.label` / `.error` / `.errorInvalid` | `Components/Form/LastName` | Last name field |
| Form | `form.email.label` / `.error.required` / `.error.invalid` | `Components/Form/Email` | Email field |
| Form | `form.phoneNumber.label` / `.error.required` / `.error.invalid` / `.description` | `Components/Form/PhoneNumber` | Phone number field |
| Form | `form.companyName.label` / `.error` / `.errorInvalid` | `Components/Form/Company Name` | Company name field |
| Form | `form.salutation.label` / `.error` / `.placeholder` | `Components/Form/Salutation` | Salutation dropdown |
| Form | `form.city.label` / `.error` / `.errorInvalid` | `Components/Form/City` | City field |
| Form | `form.street.label` / `.error` / `.errorInvalid` | `Components/Form/Street` | Street field |
| Form | `form.streetAndNumber.label` / `.error` / `.errorInvalid` | `Components/Form/Street And Number` | Street and number field |
| Form | `form.streetNumber.label` / `.error` / `.errorInvalid` | `Components/Form/Street number` | Street number field |
| Form | `form.houseNumber.label` / `.error` / `.errorInvalid` | `Components/Form/House Number` | House number field |
| Form | `form.zipCode.label` / `.error` / `.errorInvalid` | `Components/Form/ZipCode` | ZIP/postal code field |
| Form | `form.password.label` / `.error.containsPersonalInfo` | `Components/Form/Password` | Password field |
| Form | `form.dataProtection.error` | `Components/Form/Data Protection` | GDPR consent required error |
| Form | `form.gdprConsent.error` | `Components/Form/GdprConsent` | GDPR consent checkbox error |
| Form | `form.vatid.label` / `.errorInvalid` / `.errorRequired` | `Components/Form/VAT ID` | VAT ID field |
| Form | `form.fiscalCode.labelRequired` / `.errorRequired` | `Components/Form/Fiscal Code` | Italy fiscal code field |
| Form | `form.country.label` / `.error` / `.tooltip.*` | `Components/Form/Country` | Country dropdown |
| Form | `form.invitationCode.label` / `.errorInvalid` | `Components/Form/Invitation Code` | B2B invitation code field |
| Form | `form.titleCode.label` / `.error` | `Components/Form/TitleCode` | Title/prefix dropdown |
| Form | `form.jobTitle.label` / `.errorInvalid` | `Components/Form/JobTitle` | Job title field |
| Form | `form.submitButton.label` | _(derived)_ | "Submit" button default label |
| Form | `form.label.indicator.optional` | `Components/Form/Label Indicator Optional` | "(optional)" indicator text |
| Form | `form.generic.field_min_characters` / `field_max_characters` | `Components/Form/Generic` | Generic "min/max characters" validation messages |
| Form | `form.errorInvalidHtml` | _(derived)_ | HTML injection validation error |
| Form | `form.fileUpload.*` | `Components/Form/File upload` | File upload labels (dropzone, button, size/type descriptions, delete, errors) |
| Form | `form.saveAddress.label` / `form.saveChanges.label` | `Components/Form/Save` | Save button labels |
| Form | _(~155 total keys)_ | `Components/Form/*` | The Form group is the largest dictionary group (155 unique T() keys). It includes all form-related sub-items: Address, Billing, Delivery, Department, Location Type, Project, and more. |

**Used across:**
- `packages/core/schemas/src/` (validation schemas for all form types)
- `packages/features/cart/src/components/checkout/forms/` (checkout address forms)
- `packages/features/my-account/src/` (profile editing, address CRUD, registration)
- `packages/features/contact-form/src/`
- `packages/features/service-request-form/src/`
- `packages/features/support-aftersales-form/src/`
- `packages/features/request-quote-form/src/`
- `packages/features/training-courses/src/`
- `packages/features/project-lists/src/` (export specification form)

---

## 8. Contact Form

**Feature doc:** `docs/features/forms.md`
**Description:** Contact form for general inquiries. Uses shared Form dictionary keys plus contact-specific items.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Contact Form Texts | `contact.form.add.another.product` | `Components/Contact Form Texts/Add another product` | "Add another product" button on contact form |
| Contact Form Texts | `contact.form.product.title` | `Components/Contact Form Texts/Product title` | Product section heading |
| Contact Form Texts | `contact.form.remove.product` | `Components/Contact Form Texts/Remove product` | "Remove product" button |

**Key files:** `packages/features/contact-form/src/components/ContactForm.tsx`

---

## 9. Service Request Form

**Feature doc:** `docs/features/forms.md`
**Description:** Form for submitting service requests (defect reports with product details, photos). Heavily uses Form dictionary group plus service-specific items.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Form | `form.groheArticleNumber.label` / `.placeholder` / `.error` | `Components/Form/Grohe Article Number` | GROHE article number field |
| Form | `form.purchaseInstallationDate.label` / `.error` / `.invalidError` | `Components/Form/Purchase Installation Date` | Purchase/installation date field |
| Form | `form.defectDescription.label` / `.placeholder` / `.error` | `Components/Form/Defect Description` | Defect description textarea |
| Form | `form.uploadProductPhoto.label` / `.error` | `Components/Form/Upload Product Photo` | Product photo upload field |
| Form | `form.uploadOtherFile.label` | `Components/Form/Upload Other File` | Additional file upload field |
| Form | `form.addMoreProducts.label` | `Components/Form/Add More Products` | "Add more products" button |
| Form | `form.removeProduct` | _(derived)_ | Remove product button |
| Form | `form.product` | _(derived)_ | "Product" heading in multi-product form |
| Form | `form.customerGroup.label` / `.placeholder` / `.error` | `Components/Form/Customer group` | Customer group dropdown |
| Form | `form.countryAndRegion.label` / `.alertHeading` / `.alertBody` | `Components/Form/Country And Region` | Country/region selector with alert |
| Form | `form.installation.contact.error.required` | _(derived)_ | Installation contact required error |

**Key files:** `packages/features/service-request-form/src/components/ServiceRequestForm.tsx`, `packages/core/schemas/src/serviceRequestForm.ts`

---

## 10. Support/Aftersales Form

**Feature doc:** `docs/features/forms.md`
**Description:** Form for support and aftersales inquiries with project-specific fields.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Form | `form.whatKindOfService.label` / `.placeholder` / `.error` | `Components/Form/What Kind Of Service` | Service type dropdown |
| Form | `form.serviceNeededDescription.label` / `.error` | `Components/Form/Service Needed Description` | Service description textarea |
| Form | `form.projectName.label` / `.error` | `Components/Form/Project Name` | Project name field |
| Form | `form.typeOfProject.label` / `.placeholder` / `.error` | `Components/Form/Type Of Project` | Project type dropdown |
| Form | `form.phoneNumbertoCallYouBack.label` / `.placeholder` / `.error` / `.errorInvalid` | `Components/Form/Phone Number To Call You Back` | Callback phone number field |

**Key files:** `packages/features/support-aftersales-form/src/components/SupportAftersalesForm.tsx`, `packages/core/schemas/src/supportAftersalesForm.ts`

---

## 11. Request Quote Form

**Feature doc:** `docs/features/forms.md`
**Description:** Form for requesting product quotes.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Form | `form.requestQuote.selectFromList` | _(derived)_ | "Select from list" dropdown option |
| Form | `form.areaOfInterest.label` / `.placeholder` / `.error` | `Components/Form/Area of interest` | Area of interest dropdown |
| Form | `form.projectDescription.label` / `.error` | `Components/Form/Project Description` | Project description textarea |
| Form | `form.message.label` / `.error` | `Components/Form/Message` | Message textarea |
| Form | `form.billingAddress.label` | `Components/Form/Billing Address` | Billing address section label |
| Form | `form.billingEmail.label` / `.error.invalid` | `Components/Form/Billing email` | Billing email field |
| Form | `form.addMoreParties.label` | `Components/Form/Add More Parties` | "Add more parties" button |
| Form | `form.removeParty` | _(derived)_ | Remove party button |
| Form | `form.party` | _(derived)_ | "Party" heading label |
| Form | `form.reference_number.label` / `.tooltip.*` | `Components/Form/Reference Number` | Reference number field with tooltip |
| Form | `form.deliverToCompany.label` / `.tooltip.*` | `Components/Form/Deliver To Company` | "Deliver to company" checkbox with tooltip |
| Form | `form.differentPlaceOfInstallation.label` | `Components/Form/Different Place Of Installation` | "Different place of installation" checkbox |
| Form | `form.product.number.label` / `.error.required` | `Components/Form/Product Number` | Product number field in quote form |
| Form | `form.date.of.purchase.*` | `Components/Form/Date of purchase` | Date of purchase field |
| Form | `form.enquiry.product.related.*` | `Components/Form/Is Enquiry Products Related` | "Is enquiry product related?" toggle |

**Key files:** `packages/features/request-quote-form/src/components/RequestQuoteForm.tsx`, `packages/core/schemas/src/requestQuoteForm.ts`

---

## 12. Training Courses

**Description:** Training course listing and registration page for professional users.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Training Course List | `training_course_list.enroll` | `Components/Training Course List/Enroll` | "Enroll" button on course cards |
| Training Course List | `training_course_list.retry` | `Components/Training Course List/Retry` | Retry button on error state |
| Training Course List | `training_course_list.audience_filter_label` | `Components/Training Course List/All Text For Filters` | Audience filter dropdown label |
| Training Course List | `training_course_list.format_filter_label` | _(derived)_ | Format filter dropdown label |
| Training Course List | _(CMS rendering fields)_ | `Components/Training Course List/Only Places Left`, `Training Course Full`, `List Error Message` | Course card status labels |
| Form | `form.numberOfParticipants.*` | `Components/Form/Number Of Participants` | Participants count field (training registration) |
| Form | `form.comments.label` | `Components/Form/Comments` | Comments textarea (training registration) |

**Key files:** `packages/features/training-courses/src/components/`

---

## 13. Store Locator

**Feature doc:** `docs/features/store-locator.md`
**Description:** Map-based store/showroom finder with filters for certifications and store types.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Locator | `locator.seeDetails` | `Components/Locator/See details` | "See details" link on store card |
| Locator | `locator.blocked_location_message` | `Components/Locator/Blocked location access  message` | Message when geolocation is blocked |
| Locator | `locator.dropdown_selectedLabel` | `Components/Locator/Dropdown selected label` | Selected count label in multi-select filter |
| Locator | _(CMS rendering fields)_ | `Components/Locator/Distance Km`, `Distance Mi`, `Map view`, `List view`, `Show on map`, `Remove filter`, `Visit`, `Accept cookies button`, `Accept cookies text` | Distance units, view toggle labels, map/list buttons. Some are passed as props from Sitecore renderings. |
| Measurements | `measurements.cm` | `Components/Measurements/cm` | "cm" unit label (used in store cards, shared) |
| Measurements | `measurements.inches` | `Components/Measurements/inches` | "inches" unit label |

**Key files:** `packages/features/locator/src/components/`

---

## 14. Search

**Feature doc:** `docs/features/search.md`
**Description:** Product and content search with autosuggest and result listings.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Feedback | `feedback.announcement.search_results_loaded` | _(derived)_ | Screen reader announcement after search results load |
| Feedback | `feedback.suggested_results_found` | _(derived)_ | Screen reader announcement for autosuggest results |
| Feedback | `feedback.announcement.quantity_updated` | _(derived)_ | Screen reader announcement after quantity change |
| No results | `no_results.heading` / `no_results.description` | `Components/No results` | Empty search results state |
| Content | `components.content.tags.all` | `Components/Content/Tag - all` | "All" tag button in content listing filters |
| More keywords | _(CMS rendering field)_ | `Components/More keywords button aria label` | Aria label for "more keywords" button in search |

**Key files:** `packages/features/search-results/src/components/`, `packages/features/header/src/hooks/useSearch.ts`, `packages/features/feedback/src/toast/components/Toast.tsx`

---

## 15. Header and Navigation

**Feature doc:** `docs/features/dynamic-navigation.md`
**Description:** Site header including product navigation menu, search, cart count, language selector, and hamburger menu.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Header | `components.header.back_previous_menu` | `Components/Header/Back to previous menu` | "Back" button in mobile nav |
| Header | `components.header.homepage` | `Components/Header/Homepage` | Logo/home link aria label |
| Header | `components.header.close_menu` | _(tKey)_ | Close menu button aria label |
| Header | `components.header.close_search` | `Components/Header/Close search` | Close search button aria label |
| Header | `components.header.open_menu` | `Components/Header/Open menu` | Open menu button aria label |
| Header | `components.header.open_search` | `Components/Header/Open search` | Open search button aria label |
| Header | `components.header.search` | `Components/Header/Search` | Search input placeholder/aria label |
| Header | `components.header.select_language` | `Components/Header/Select language` | Language selector button aria label |
| Header | `components.header.products_in_cart` | `Components/Header/Products in cart` | Cart count badge aria label |
| Header | `components.header.secondary_navigation` | `Components/Header/Secondary Navigation` | Secondary nav section aria label |
| Header | `components.header.top_navigation` | `Components/Header/Top Navigation` | Top nav section aria label |
| Country-Language Selector | `components.countrylanguageselector.search_label` | `Components/Country-Language Selector/search_label` | Search input label in country/language modal |
| Country-Language Selector | `components.countrylanguageselector.clear_search_query` | `Components/Country-Language Selector/clear_search_query` | "Clear" button aria label |
| Country-Language Selector | `components.countrylanguageselector.back_button` | _(tKey)_ | "Back" button aria label |
| Country-Language Selector | `components.countrylanguageselector.close_button` | _(tKey)_ | "Close" button aria label |
| Country-Language Selector | `components.countrylanguageselector.selector_title` | _(tKey)_ | Modal title |
| Navigation | _(CMS rendering field)_ | `Components/Navigation/Home` | "Home" breadcrumb label |
| Footer | _(CMS rendering fields)_ | `Components/Footer/Homepage`, `Lixil website` | Footer link labels. These are delivered as Sitecore rendering fields via the FooterResolver, not via T() keys. |

**Key files:** `packages/features/header/src/components/`

---

## 16. Content Components (Shared)

**Description:** Shared UI text used across multiple content components (RichText, modals, show more/less, carousels, videos, hotspots, downloads).

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Read more / Read less | `components.read_more` | `Components/Read more` | "Read more" button text (RichText truncation) |
| Read less | `components.read_less` | `Components/Read less` | "Read less" button text |
| Show more / Show more2 | `components.show_more` / `components.show_more2` | `Components/Show more` / `Show more2` | "Show more" toggle (two variants for different contexts) |
| Show less / Show less 2 | `components.show_less` / `components.show_less2` | `Components/Show less` / `Show less 2` | "Show less" toggle |
| More | `components.more` | `Components/More` | "More" link text (content cards) |
| Learn more about | `components.learnMoreAbout` | `Components/Learn more about` | "Learn more about" prefix text |
| Close notification | `close_notification` | `Components/Close notification` | "Close" button on notification banners |
| Modals | `modal.close` | `Components/Modals/Close modal windows` | "Close" button in all modal dialogs |
| Carousel | `carousel.active_slide_text` | `Components/Carousel/Active slide text` | Screen reader: current slide indicator |
| Carousel | `carousel.next_slide` | `Components/Carousel/Next slide` | "Next slide" button aria label |
| Carousel | `carousel.previous_slide` | `Components/Carousel/Previous slide` | "Previous slide" button aria label |
| Carousel | `carousel.navigation` | `Components/Carousel/Carousel navigation` | Carousel nav section aria label |
| Video | `video.play` / `video.pause` | `Components/Video/Play video` / `Pause video` | Video player button aria labels |
| Video | `video.promo_video_play` / `video.promo_video_play` | _(derived)_ | Promo video play/pause labels |
| Video | _(CMS rendering fields)_ | `Components/Video/Mute video`, `Stop video`, `Unmute video` | Video control labels (some via rendering fields) |
| Hotspots | `hotspot.modalTitle` | `Components/Hotspots/Modal Title` | Hotspot detail modal title |
| Hotspots | `hotspot.multiTriggerAriaLabel` | `Components/Hotspots/Multi Trigger Area Label` | Multiple hotspot trigger button aria label |
| Downloads | `downloads.download` | `Components/Downloads/Download` | "Download" button label |
| Downloads | `downloads.downloadButton_ariaLabel` | `Components/Downloads/Download button aria label` | Download button aria label |
| Downloads | `downloads.previewButton_ariaLabel` | `Components/Downloads/Preview button file label` | Preview button aria label |
| Downloads | `downloads.requestButton_ariaLabel` | `Components/Downloads/Request download button label` | Request button aria label |
| Downloads | `downloads.viewButton_ariaLabel` | `Components/Downloads/View button label` | View button aria label |
| Tooltips | `tooltip.close` / `tooltip.open` | `Components/Tooltips/Close tooltip` / `Open tooltip` | Tooltip trigger aria labels |
| Select | `select.placeholder` | `Components/Select/Placeholder` | Default select/dropdown placeholder text |
| General Error Alert | `components.general_error_alert.title` / `.description` | `Components/General Error Alert` | Generic error alert heading and description |
| Accordion2 | _(CMS rendering fields)_ | `Components/Accordion2/Go to all FAQs`, `Link title` | FAQ accordion link labels. Delivered as rendering fields. |
| Dynamic Carousel Articles | _(CMS rendering field)_ | `Components/Dynamic Carousel Articles` | Labels for article carousel component. No T() keys found -- likely delivered via rendering fields. |
| Content | _(CMS rendering field)_ | `Components/Content/Content items count` | "{n} items" count label |
| Invalid Datasource | _(CMS rendering field)_ | `Components/Invalid Datasource` | Error message when component datasource is misconfigured in Sitecore |
| Load more | _(CMS rendering field)_ | `Components/Load more` | "Load more" button label (generic) |
| Input | _(CMS rendering field)_ | `Components/Input/Password visibility` | Password visibility toggle label |
| Dropdown | _(CMS rendering field)_ | `Components/Dropdown/MultipleSelectedPlaceholder` | Multi-select dropdown placeholder |

**Key files:** `jss/atoms/src/RichText.tsx`, `jss/asset-picker/src/Video.tsx`, `packages/features/content/src/`, `packages/ui/shared/src/components/Modal.tsx`, `packages/ui/shared/src/components/GeneralErrorAlert.tsx`, `packages/ui/shared/src/components/Button.tsx`

---

## 17. Payment Methods (Settings)

**Feature doc:** `docs/features/checkout.md` (PaymentApi), `docs/features/my-account.md`
**Description:** Credit card management in My Account settings and checkout payment step.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Settings / Payment | `settings.payment.add_new_payment_card` | `Components/Settings/Payment/...` | "Add new card" button |
| Settings / Payment | `settings.payment.card_holder_name` / `_invalid` / `_required` | | Card holder name field + validation |
| Settings / Payment | `settings.payment.card_number` / `_required` / `invalid_card_number` | | Card number field + validation |
| Settings / Payment | `settings.payment.expiration_date` / `_required` / `invalid_expiration_date` | | Expiration date field + validation |
| Settings / Payment | `settings.payment.security_code` / `_required` | | CVV/security code field + validation |
| Settings / Payment | `settings.payment.save_credit_card` | | "Save credit card" button |
| Settings / Payment | `settings.payment.cancel` | | Cancel button |
| Settings / Payment | `settings.payment.delete_credit_card` / `_description` | | Delete card confirmation modal |
| Settings / Payment | `settings.payment.empty_payment_method` | | Empty state for no saved cards |
| Settings / Payment | `settings.payment.expiry` | | "Expiry" label on saved card |
| Settings / Payment | `settings.payment.cvv_info` | | CVV info tooltip text |
| Settings / Payment | `settings.payment.use_date_format` / `use_digits` | | Input format hint labels |
| Settings / Payment | `settings.payment.notification.*` | | Success/error toast messages for card operations |

**Key files:** `packages/features/payment-methods/src/components/modals/`, `packages/features/cart/src/components/checkout/payment/`, `packages/features/my-account/src/components/MyAccountSettings/Payments/`

---

## 18. User Registration

**Feature doc:** `docs/features/user-registration.md`
**Description:** Full and partial registration forms, including B2B invitation codes.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| User | _(CMS rendering fields)_ | `Components/User/Architects and Designer`, `Commercial Customer`, `DIY Store  Retailer`, `EndConsumer`, `Installer`, `Kitchen Studio`, `Others`, `Planner`, `Showroom`, `Wholesaler`, `User type Internal` | User type dropdown options for registration and profile forms. These values are likely delivered as Sitecore rendering fields or dropdown option lists, not via T() keys. |

**Note:** Registration uses shared `form.*` keys (see section 7) for all field labels and validation messages.

**Key files:** `packages/features/my-account/src/hooks/useFullRegistrationForm.ts`, `packages/features/my-account/src/hooks/usePartialRegistrationForm.ts`, `packages/features/my-account/src/schemas/`

---

## 19. Pricing and Product Card (Cross-Feature)

**Feature docs:** `docs/features/pricing.md`, `docs/features/pdp.md`, `docs/features/plp.md`, `docs/features/project-list.md`
**Description:** The `Product` dictionary group provides labels used on product cards (PDP, PLP, cart summary, project list cards). These are cross-feature -- a single dictionary group consumed by multiple features.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Product | `product.add_to_cart` | `Components/Product/Add to cart` | "Add to cart" button text |
| Product | `product.addToCartButton_ariaLabel` | `Components/Product/Add to cart button aria label` | Add-to-cart button aria label |
| Product | `product.add_to_cart_success_message` | `Components/Product/Add to cart success message` | Success toast after add to cart |
| Product | `product.add_to_cart_error_message` | `Components/Product/Add to cart error message` | Error toast when add to cart fails |
| Product | `product.discount_label` | `Components/Product/Discount label` | Discount badge text |
| Product | `product.incl_vat` | `Components/Product/Incl VAT` | "Incl. VAT" price label |
| Product | `product.original_price_label` | `Components/Product/Original price label` | Crossed-out original price label |
| Product | `product.price_label` | `Components/Product/Price label` | "Price" label |
| Product | `product.recommended_retail_price` | `Components/Product/Recommended Retail Price` | "Recommended Retail Price" label |
| Product | `product.rrp` | `Components/Product/RRP` | "RRP" abbreviation |
| Product | `product.tag.label_new` | `Components/Product/Tag - New` | "New" product badge |
| Product | `product.pinButton_ariaLabel` | `Components/Product/Pin button aria label` | Pin/unpin product button aria label |
| Product | `product.view_shopping_cart_link_label` | `Components/Product/View shopping cart link label` | "View cart" link after add to cart |
| Product | _(CMS rendering fields)_ | `Components/Product/ECO Participation Label`, `Dimension Drawing`, `Flow Diagram`, `NRF`, `RSK`, `VVS`, `Product Description`, `Specification Heading`, `Pin product`, `Unpin product`, `Product card optional label`, `Product card required label` | Additional product-related labels; some via T() keys, others via Sitecore rendering fields. |
| External Retailers | _(CMS rendering field)_ | `Components/External Retailers/Dialog title` | External retailers modal dialog title. Not used via T() keys. |
| API responses | `api.input_body_not_matching` | `Components/API responses/Input body not matching` | Error message when API request body validation fails. Used in: `useCreateOrderMutation.ts`, `EditUserEmailForm.tsx`, `MyAccountInfoFormB2B/B2C.tsx` |
| API responses | _(CMS rendering field)_ | `Components/API responses/Invalid reCaptcha` | reCAPTCHA validation failure message |

**Key files:** `packages/features/product/src/components/ProductCard.tsx`, `packages/features/product/src/PDPProductMain/PDPPurchase.client.tsx`, `packages/features/cart/src/components/checkout/summary/CartSummaryProductTile.tsx`, `packages/features/project-lists/src/components/ProjectCard.tsx`

---

## 20. Shared UI / Generic

**Description:** The `Generic` dictionary group provides button labels and file-related messages used in shared UI components across the entire application.

| Dictionary Group | Dictionary Key (T() prefix) | Sitecore Path | Usage Context |
|---|---|---|---|
| Generic | `generic.back` | `Components/Generic/Back` | "Back" button text |
| Generic | `generic.cancel` | `Components/Generic/Cancel` | "Cancel" button text |
| Generic | `generic.choose_file` | `Components/Generic/Choose Fle` | "Choose file" button text |
| Generic | `generic.copy_failed` / `generic.copy_successful` | _(derived)_ | Clipboard copy feedback messages |
| Generic | `generic.download_csv_template` | `Components/Generic/Download Csv Template` | CSV template download button |
| Generic | `generic.file_too_big` | `Components/Generic/File Too Big` | File size exceeded error |
| Generic | `generic.file_upload_instructions` / `generic.file_upload_label` | `Components/Generic/File Upload Instructions` | File upload helper text |
| Generic | `generic.incorrect_file_format_title` / `_message` | `Components/Generic/Incorrect File Format Title...` | Wrong file format error modal |
| Generic | `generic.invalid_file_type` | _(derived)_ | Invalid file type error |
| Generic | `generic.isLoading` | _(derived)_ | "Loading..." text |
| Generic | `generic.maximum_file_size` | `Components/Generic/Maximum File Size` | "Maximum file size" label |
| Generic | `generic.size_limit` / `large_size_limit` / `small_size_limit` | `Components/Generic/Size Limit`, etc. | File size limit labels |
| Generic | `generic.supported_file_types` | `Components/Generic/Supported File Types` | Supported file types label |
| Generic | `generic.upload_file` | `Components/Generic/Upload File` | "Upload file" button text |
| Generic | `generic.wrong_file_format` | _(derived)_ | Wrong file format error message |

**Used by:** `packages/ui/shared/src/components/Button.tsx` (loading state), `packages/features/project-lists/src/` (CSV import), `packages/features/product/src/PDPProductMain/PDPProductMain.client.tsx` (copy SKU)

---

## 21. Unused or Backend-Only Dictionary Groups

These dictionary groups exist in the PROD export but have **no direct T() key usage** in the Next.js frontend. They are either:
- Consumed server-side (ProjectListsApi PDF generation)
- Delivered as Sitecore rendering field values (not dictionary lookups)
- Legacy items no longer used
- Used by a mechanism other than talkr T() (e.g., Hybris status display mapping)

| Dictionary Group | Sitecore Path | Likely Usage |
|---|---|---|
| **Product Detail Document** | `Components/Product Detail Document/Article No`, `Date`, `EAN Code`, `Page`, `Product Description`, `Spare Parts`, `Technical Data` | **Likely unused / legacy.** Not referenced in ProjectListsApi `DictionaryItemsService.cs` (which explicitly lists only `project_lists.*` keys). Not referenced via T() in frontend. May have been used in an earlier PDF template or content structure. |
| **Status / Hybris** | `Components/Status/Hybris/Cancelled`, `Completed`, etc. (26 order statuses) | **Backend mapping.** Hybris returns `statusDisplay` with the translated status string. These dictionary items may be used by a Sitecore rendering resolver or content resolver to map Hybris status codes to display names, but the mapping happens server-side. The frontend receives `statusDisplay` directly. |
| **Filters** | `Components/Filters/Apply`, `Clear all`, `Desktop trigger label`, `Mobile trigger label`, `Show results`, `Sheet label`, `Min`, `Max`, `Remove` | **Sitecore rendering fields.** Filter UI labels are delivered as Sitecore rendering fields in the SERP Filters component datasource, not via dictionary T() keys. These configure the `@grohe/search-results` filter drawer/sidebar UI. |
| **Navigation** | `Components/Navigation/Home` | **Sitecore rendering field.** The "Home" breadcrumb label is delivered via the `BreadcrumbsResolver.cs` Sitecore rendering resolver, not via dictionary. |
| **Footer** | `Components/Footer/Homepage`, `Lixil website` | **Sitecore rendering fields.** Footer content is delivered via `FooterResolver.cs`, not via dictionary T() keys. |
| **External Retailers** | `Components/External Retailers/Dialog title` | **Sitecore rendering field.** External retailers modal dialog title. |
| **Dynamic Carousel Articles** | `Components/Dynamic Carousel Articles/No result first line`, `No result second line`, `No results found` | **Sitecore rendering fields.** Article carousel empty state messages. Delivered via XM Cloud rendering fields, not T() keys. |
| **Browse All** | `Components/Browse All` | **Sitecore rendering field.** "Browse all" link label on category pages. |
| **Input** | `Components/Input/Password visibility` | **Sitecore rendering field.** Password visibility toggle label. |
| **Dropdown** | `Components/Dropdown/MultipleSelectedPlaceholder` | **Sitecore rendering field.** Multi-select dropdown placeholder. |
| **Invalid Datasource** | `Components/Invalid Datasource` | **Sitecore rendering field.** Error message displayed when a component's datasource is misconfigured in Sitecore Content Editor. |
| **More keywords button aria label** | `Components/More keywords button aria label` | **Sitecore rendering field.** Aria label for "show more keywords" button. |
| **Load more** | `Components/Load more` | **Sitecore rendering field.** Generic "load more" button label. |

---

## Summary Statistics

| Category | Dictionary Groups | T() Keys in Frontend | Notes |
|---|---|---|---|
| PDP | 1 (PDP) | 9 | Plus ~15 rendering field items for downloads labels |
| PLP / Catalogue / Filters | 3 (Product, Filters, Browse All) | 3 | Filters group is rendering-field-only |
| Shopping Cart | 1 (Cart) | 19 | |
| Checkout | 1 (Checkout, 7 sub-groups) | 28 | |
| My Account | 1 (MyAccount, 4 sub-groups) | 1 | Most labels come from rendering fields |
| Project Lists | 1 (Project Lists) | 121 | Largest single group by far |
| Forms (shared) | 1 (Form, ~60 sub-items) | 155 | Shared across all form features |
| Contact Form | 1 (Contact Form Texts) | 3 | |
| Training Courses | 1 (Training Course List) | 4 | |
| Store Locator | 2 (Locator, Measurements) | 5 | |
| Search / Content | 3 (No results, Content, Feedback) | 8 | |
| Header / Nav | 3 (Header, Country-Language Selector, Navigation) | 17 | Navigation/Footer are rendering-field-only |
| Content (shared) | 12 (Read more/less, Show more/less, Carousel, Video, Hotspots, Downloads, Tooltips, Select, Modals, etc.) | 21 | |
| Settings / Payment | 1 (Settings/Payment) | 26 | |
| Generic (shared UI) | 1 (Generic) | 20 | |
| API Responses | 1 (API responses) | 1 | |
| User Registration | 1 (User) | 0 | Values delivered as rendering fields |
| Status (Hybris) | 1 (Status/Hybris) | 0 | Backend/server-side mapping |
| **TOTAL** | **48 groups** | **~449 unique T() keys** | Excludes storybook-only keys |
