# QA Report: NEO-4638 — Sustainability Section Extension

**Date:** 2026-03-03
**Feature context:** project-list
**Repos changed:** grohe-neo-websites
**Status:** PARTIAL (1 source bug found)

---

## Summary

The implementation adds server-side re-fetching of sustainability section content from Sitecore Edge
when the user selects a different export language for the project list PDF. The core logic in
`getSustainabilityContent.ts` and `route.ts` is correct. However, a TypeScript compilation error
exists in `ExportSpecificationForm.tsx` due to a missing `pagePath` property in the mutation call.

---

## Test Runs

### Biome Lint Check
**Result: PASS** -- 109 files checked, no issues found.

### TypeScript Type Check (project-lists package)
**Result: FAIL** -- 1 error

```
src/components/ExportSpecificationForm.tsx(179,24): error TS2345:
  Argument of type '{ specificationFormValues: ...; projectListId: string;
  sustainabilitySection: ...; pdpLink: string; }' is not assignable to parameter
  of type 'ExportMutationArgs'.
  Property 'pagePath' is missing in type '...' but required in type 'ExportMutationArgs'.
```

### Vitest (project-lists + export-document)
**Result: PASS** -- 36 tests passed (27 existing + 9 new), 0 failed.

---

## Code Review Findings

### Correct Implementation

1. **`getSustainabilityContent.ts`** -- Well structured. Recursively searches Sitecore layout
   placeholders for the `ExportProjectList` component. Extracts sustainability fields from the
   datasource. Returns `null` on all failure paths (missing route, missing component, GraphQL
   error), enabling graceful fallback. Uses `serverEnv.SITECORE_SITE_NAME` correctly.

2. **`route.ts`** -- Logic is correct:
   - `effectiveDocumentLocale = documentLocale || locale` correctly falls back to page locale
   - Re-fetch only triggers when `effectiveDocumentLocale !== locale && pagePath`
   - On `null` return from `getSustainabilityContent`, original page-locale content is preserved
   - `effectiveDocumentLocale` is consistently used as the locale sent to ProjectListsApi

3. **`ExportProjectList.server.tsx`** -- `pagePath` extraction from `pageData.params.path`
   (joining array segments with `/` prefix) is correct per the `ParamsSchema` type definition.

4. **`ExportSpecificationFormContainer.tsx`** -- Correctly destructures `pagePath` from props
   and passes `pagePath: pagePath ?? ''` to the mutation.

5. **`useExportSpecificationDocumentMutation.ts`** -- Correctly sends `pagePath` in the JSON
   body and `documentLocale` as a query parameter.

6. **`exportDocument.ts`** -- `pagePath: z.string().optional()` added to schema correctly.

### Bug Found

**File:** `C:/projects/grohe/NEO/grohe-neo-websites/packages/features/project-lists/src/components/ExportSpecificationForm.tsx`
**Line:** 179
**Severity:** Medium (TypeScript compilation error, blocks CI)
**Type:** Source bug -- incomplete update

**Description:** The `ExportSpecificationForm` component has its own local `onSubmit` handler
(line 178-191) that calls `addSpecificationData()` without the `pagePath` property. The
`ExportMutationArgs` type in `useExportSpecificationDocumentMutation.ts` requires `pagePath`
(non-optional), so this causes TS2345.

**Root cause:** The dev agent updated `ExportSpecificationFormContainer.tsx` (the active code
path) but missed updating `ExportSpecificationForm.tsx`, which has a duplicate `onSubmit`
handler. This component appears to be legacy (not rendered by the current app flow -- the app
uses `ExportSpecificationFormContainer` -> `ExportSpecificationFormPage`), but it still
contains a default export that TypeScript compiles.

**Recommended fix:** Add `pagePath` to the `ExportSpecificationFormProps` local type (line 57-86)
and pass it in the `addSpecificationData` call (line 179-190):
```typescript
// In the local ExportSpecificationFormProps type (line 57-86), add:
pagePath?: string

// In the onSubmit handler (line 179-190), add:
pagePath: pagePath ?? '',
```

Alternatively, if this component is truly unused, consider removing the default export entirely
and only keeping the `useExportSpecificationForm` hook export.

---

## New Tests Created

**File:** `C:/projects/grohe/NEO/grohe-neo-websites/apps/website/src/app/api/project-lists/export-document/__tests__/getSustainabilityContent.test.ts`

| # | Test Name | What It Validates |
|---|---|---|
| 1 | should extract sustainability fields from a valid layout response | Happy path: full field extraction + correct GraphQL variables |
| 2 | should return empty strings for missing sustainability fields | Partial fields: missing fields default to empty string |
| 3 | should return null when the ExportProjectList component is not found | Component not in layout |
| 4 | should return null when sitecore route is missing | Malformed layout response |
| 5 | should return null when layout response is null | Null response from GraphQL |
| 6 | should return null when the GraphQL client throws an error | Network/GraphQL error |
| 7 | should return null when datasource fields is not an array | Invalid fields shape |
| 8 | should find the ExportProjectList component in nested placeholders | Recursive placeholder search |
| 9 | should return null when layout item rendered is missing | Null rendered property |

---

## Self-Verification Checklist

- [x] Ran the full relevant test suite and captured complete output
- [x] All new tests follow the naming and structural conventions of the repo
- [x] No source code was modified in the protected repos (only test files created)
- [x] Bug found is documented with reproduction steps and recommended fix
- [x] QA report written to `reports/`
- [x] New tests pass when run (9/9 passed)

---

## Recommendation

The implementation logic is correct and well-designed. The single bug in
`ExportSpecificationForm.tsx` is a straightforward omission that the dev agent should fix
before merging. Once fixed, the TypeScript check should pass cleanly.
