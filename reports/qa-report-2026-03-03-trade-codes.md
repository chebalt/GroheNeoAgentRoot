# QA Report: EDSD-3075 + EDSD-3076 -- VVS/RSK/NRF Trade Codes on PDP

**Date:** 2026-03-03
**Feature:** PDP (Product Detail Page)
**Feature doc:** `docs/features/pdp.md`
**Verdict:** PASS

---

## Summary

Three new optional Scandinavian trade code fields (`vvs_denmark`, `rsk_sweden`, `nrf_norway`) have been implemented end-to-end across all four repositories. The implementation is correct, complete, and follows established patterns in each repo.

---

## Repos and Files Reviewed

### grohe-neo-data-loader
| File | Status |
|---|---|
| `models/product.py` (lines 252-255) | PASS -- 3 new `Optional[str]` fields with correct names and descriptions |
| `output_models/pl_product_content.py` (lines 146-148) | PASS -- PascalCase `VvsDenmark`, `RskSweden`, `NrfNorway` with `= None` default |
| `transformer.py` (lines 1430-1432) | PASS -- correctly wired `product.vvs_denmark` -> `VvsDenmark` etc. |

### grohe-neo-services
| File | Status |
|---|---|
| `GroheNeoProductDataCommon/.../PLProductContent.cs` (lines 101-103) | PASS -- `[FirestoreProperty] public string?` for all three |
| `GroheNeo.ProductsApi/.../ProductDetailResponse.cs` (lines 110-120) | PASS -- camelCase `[JsonPropertyName]`, `[JsonIgnore(WhenWritingNull)]` |
| `GroheNeo.ProductsApi/.../ProductDataService.cs` (lines 640-642) | PASS -- direct mapping from Firestore model to response |

### grohe-neo-websites
| File | Status |
|---|---|
| `packages/core/schemas/src/product.ts` (lines 197-199) | PASS -- `z.string().nullish()` for all three |
| `packages/features/product/src/PDPProductMain/PDPProductMain.client.tsx` (lines 128-164) | PASS -- `PDPTradeCodesJss` component with null guard, dictionary lookups, matching EAN styling |
| `packages/features/product/src/jss/Product.client.ts` | PASS -- re-exports `PDPTradeCodesJss` |
| `packages/features/product/src/jss/Product.dynamic.ts` (line 32) | PASS -- `PDPTradeCodesJssDynamic` dynamic import |
| `packages/features/product/src/jss/PDPProductMain.server.tsx` (line 353) | PASS -- renders `PDPTradeCodesJssDynamic` inside `pdp-info-row` div, after EAN row |

### grohe-neo-sitecore-xm-cloud (6 YAML dictionary items)
| File | Key | Phrase | Status |
|---|---|---|---|
| `Dictionary/Components/Product/VVS.yml` | `product.vvs` | `VVS` | PASS |
| `Dictionary/Components/Product/RSK.yml` | `product.rsk` | `RSK` | PASS |
| `Dictionary/Components/Product/NRF.yml` | `product.nrf` | `NRF` | PASS |
| `Dictionary/Components/PDP/Copy VVS.yml` | `pdp.copy_vvs` | `Copy VVS number` | PASS |
| `Dictionary/Components/PDP/Copy RSK.yml` | `pdp.copy_rsk` | `Copy RSK number` | PASS |
| `Dictionary/Components/PDP/Copy NRF.yml` | `pdp.copy_nrf` | `Copy NRF number` | PASS |

All YAML files follow the exact same structure (Parent ID, Template ID, SharedFields, Languages) as existing siblings in their respective directories.

### integration
| File | Status |
|---|---|
| `fixtures/csv/1_product_data.csv` | PASS -- columns `vvs_denmark` (56), `rsk_sweden` (57), `nrf_norway` (58) present |

---

## Test Run Results

### Biome lint check
```
Checked 1991 files in 937ms. No fixes applied.
```
**Result:** PASS (0 errors)

### TypeScript type check
- `@grohe/product` package: PASS (tsc --noEmit clean)
- `@grohe/schemas` package: PASS (tsc --noEmit clean)
- Full `pnpm type:check`: known Windows failure on `@grohe/icons` setup (svgo glob issue, pre-existing)

### Vitest test suite
**Before new tests:** 61 test files, 458 tests -- all passing
**After new tests:** 62 test files, 467 tests -- all passing
**New tests added:** 9 (see below)

---

## New Tests Created

**File:** `C:/projects/grohe/NEO/grohe-neo-websites/packages/features/product/src/__tests__/PDPTradeCodes.test.tsx`

| # | Test Name | Verifies |
|---|---|---|
| 1 | renders nothing when all trade codes are null | Null guard -- no DOM output |
| 2 | renders nothing when all trade codes are undefined | Undefined guard -- no DOM output |
| 3 | renders nothing when all trade codes are empty strings | Empty string guard -- no DOM output |
| 4 | renders VVS trade code with label and copy button when provided | VVS rendering + dictionary label + copy button aria label |
| 5 | renders RSK trade code with label and copy button when provided | RSK rendering + dictionary label + copy button aria label |
| 6 | renders NRF trade code with label and copy button when provided | NRF rendering + dictionary label + copy button aria label |
| 7 | renders all three trade codes when all are provided | All three rendered simultaneously, 3 copy buttons |
| 8 | renders only non-null trade codes in a mixed scenario | Selective rendering (VVS + NRF shown, RSK hidden) |
| 9 | applies correct styling classes to trade code rows | CSS classes match EAN row styling |

---

## Bugs Found

None.

---

## Observations and Notes

1. **Pre-existing issue:** `pl_product_content.py` has a duplicate `Warranty` field declaration (lines 56 and 143). This is not related to this PR.

2. **No .NET unit test project** exists for `GroheNeo.ProductsApi.Tests`. The mapper changes in `ProductDataService.cs` are simple pass-through assignments (`VvsDenmark = product.VvsDenmark`) and are low-risk. When a test project is created, tests for the trade code mapping should be added.

3. **Dictionary items** have English-only phrases (`VVS`, `RSK`, `NRF`). Since these are international trade code abbreviations, they are likely the same across locales -- but market-specific translations should be verified with the business team.

4. **Integration CSV** has empty values for the three columns. This is expected since the test fixture uses UK market data, and these are Scandinavian-market-specific fields.

---

## Self-Verification Checklist

- [x] Ran the full relevant test suite and captured complete output
- [x] All new tests follow the naming and structural conventions of the repo
- [x] No source code was modified in the four protected repos (only test files)
- [x] Any bugs found are documented (none found)
- [x] The QA report is written to `reports/`
- [x] New tests actually pass when run (9/9 passing)
