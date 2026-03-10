# QA Report: Firestore Config Resilience Fix

**Date:** 2026-03-02
**Verdict:** PARTIAL
**Feature:** FirebaseConfigurationService resilience (cache TTL + exception fallback)
**Changed file:** `grohe-neo-services/src/GroheNeoProductDataCommon/Services/Configuration/FirebaseConfigurationService.cs`

---

## Summary

The resilience fix to `FirebaseConfigurationService` is **functionally correct** in its own scope: it catches Firestore exceptions, logs them, returns stale config, and uses a short (1-minute) retry TTL on failure. The 8 new unit tests all pass.

However, a **downstream source bug** was discovered in `HttpTenantContext` and `FirestoreDbResolver` (`GroheNeo.ProductsApi/FireStoreDbResolver.cs`): these classes use direct dictionary indexing (`config[key]`) on the config dictionary returned by `FirebaseConfigurationService`, which throws `KeyNotFoundException` when the config is empty (first-call failure with no last-known config). This partially defeats the purpose of the resilience fix.

---

## Unit Tests: PASS (8/8)

**New test project:** `grohe-neo-services/src/GroheNeoProductDataCommon.Tests/GroheNeoProductDataCommon.Tests.csproj`
**Test file:** `grohe-neo-services/src/GroheNeoProductDataCommon.Tests/Services/Configuration/FirebaseConfigurationServiceTests.cs`
**Added to solution:** `GroheNeoServices.sln`

| # | Test Name | Status |
|---|---|---|
| 1 | `LoadConfigurationAsync_ReturnsConfig_WhenFirestoreSucceeds` | PASS |
| 2 | `LoadConfigurationAsync_ReturnsLastKnownConfig_WhenFirestoreThrows` | PASS |
| 3 | `LoadConfigurationAsync_ReturnsEmptyDict_WhenFirestoreThrowsAndNoLastKnown` | PASS |
| 4 | `LoadConfigurationAsync_UpdatesLastKnownConfig_AfterSuccessfulFetch` | PASS |
| 5 | `LoadConfigurationAsync_UsesCachedResult_OnSecondCall` | PASS |
| 6 | `LoadConfigurationAsync_SetsShortCacheTtl_WhenFirestoreThrows` | PASS |
| 7 | `Constructor_SetsCacheDurationTo60Minutes` | PASS |
| 8 | `Constructor_SetsCacheRetryOnFailureTo1Minute` | PASS |

Tests use the Firestore emulator (localhost:8080) for happy-path scenarios and reflection-injected
throwing `Lazy<FirestoreDb>` for exception-path scenarios. Real `MemoryCache` is used throughout.

Tests pass in both Debug and Release configurations.

---

## Integration Tests: PASS (5/5, after fix)

**Test file:** `integration/tests/pdp/test_products_api.py`

| # | Test Name | Status |
|---|---|---|
| 1 | `test_products_api_returns_product_for_known_sku` | PASS |
| 2 | `test_product_response_contains_sku_field` | PASS |
| 3 | `test_products_api_returns_404_for_unknown_sku` | PASS |
| 4 | `test_category_endpoint_returns_data_for_locale` | PASS (after test fix) |
| 5 | `test_variants_endpoint_returns_variants_for_known_sku` | PASS |

**Test bug fixed:** `test_category_endpoint_returns_data_for_locale` assumed the `/neo/product/v1/category`
endpoint returns `{"categories": [...]}` but it actually returns a plain JSON array `[...]`. Fixed the
test to handle both shapes (`isinstance(body, list)` check).

**Infrastructure note:** The unit tests' `ClearConfigurationCollection()` helper wiped the emulator's
`configuration` collection, which caused the ProductsApi container to fail with empty config. This was
resolved by re-seeding (`seed_config.py`) and restarting the container. The 1-minute failure cache TTL
from the resilience fix means the service self-healed after the config was re-seeded.

---

## Build Result: PASS

```
dotnet build GroheNeo.ProductsApi/GroheNeo.ProductsApi.csproj --verbosity normal
  0 Error(s)
  686 Warning(s) (all pre-existing -- XML comment, nullable, ASP0000)
```

No new warnings or errors from the changed file.

---

## Full Solution Test Run

| Test Project | Passed | Failed | Notes |
|---|---|---|---|
| GroheNeoSharedTests | 9 | 0 | |
| GroheNeoJwtTokenServiceTests | 21 | 0 | |
| GroheNeo.Feature.SitecoreSearch.Tests | 9 | 0 | |
| GroheNeo.PricingApiTests | 1 | 0 | |
| GroheNeo.SearchApi.Tests | 11 | 0 | |
| GroheNeo.ProductsDynamicNavigationApiTests | 6 | 0 | |
| GroheNeo.PaymentApi.Tests | 36 | 0 | |
| **GroheNeoProductDataCommon.Tests** | **8** | **0** | **NEW -- this PR** |
| GroheNeo.ShoppingCartApiTests | 56 | 0 | |
| GroheNeo.IndexingApi.Tests | 21 | 0 | |
| GroheNeo.ProductsApiTests | 1 | 0 | |
| GroheNeo.UserApi.Tests | 74 | 7 | Pre-existing: IdpServiceTests |
| GroheNeo.ProjectListsApiTests | 67 | 1 | Pre-existing: GetUserProjectList auth test |
| **Totals** | **320** | **8** | 8 failures are pre-existing |

---

## Bug Found: Downstream KeyNotFoundException in HttpTenantContext

**Severity:** Medium
**File:** `grohe-neo-services/src/GroheNeo.ProductsApi/FireStoreDbResolver.cs`
**Lines:** 31 (HttpTenantContext) and 73 (FirestoreDbResolver)

### Description

The resilience fix in `FirebaseConfigurationService` returns an empty `Dictionary<string, string>`
when Firestore fails on the first call (no last-known config available). This prevents the service
from throwing, but the downstream consumers do direct dictionary access:

```csharp
// Line 31 -- HttpTenantContext
DatabaseId = configurationDictionary[configKey];  // throws KeyNotFoundException

// Line 73 -- FirestoreDbResolver
_projectId = configurationDictionary["project_id"] ?? throw ...;  // throws KeyNotFoundException
```

### Reproduction

1. Start ProductsApi without seeding the `configuration` collection (or clear it)
2. Send any request with `?locale=de-DE`
3. Result: HTTP 500 with `KeyNotFoundException: The given key 'database_de_de' was not present`

### Impact

When the resilience fix returns an empty config (first-call failure scenario), every request
still crashes with a 500. The resilience fix works correctly for the case where there IS a
last-known config (subsequent failures return stale data), but does not protect the first-call
cold-start scenario.

### Recommended Fix (for dev agent)

Replace direct dictionary access with `TryGetValue` or add validation before access:

```csharp
// HttpTenantContext -- line 31
if (!configurationDictionary.TryGetValue(configKey, out var dbId) || string.IsNullOrEmpty(dbId))
{
    throw new InvalidOperationException(
        $"Firestore configuration missing key '{configKey}'. "
        + "The configuration service may not have loaded yet.");
}
DatabaseId = dbId;

// FirestoreDbResolver -- line 73
if (!configurationDictionary.TryGetValue("project_id", out var projectId) || string.IsNullOrEmpty(projectId))
{
    throw new ArgumentException("project_id is missing from Firestore configuration.");
}
_projectId = projectId;
```

This converts an opaque `KeyNotFoundException` into a clear, actionable error message.

---

## Files Created/Modified

| File | Action | Scope |
|---|---|---|
| `grohe-neo-services/src/GroheNeoProductDataCommon.Tests/GroheNeoProductDataCommon.Tests.csproj` | Created | Test project |
| `grohe-neo-services/src/GroheNeoProductDataCommon.Tests/Services/Configuration/FirebaseConfigurationServiceTests.cs` | Created | 8 unit tests |
| `grohe-neo-services/src/GroheNeoServices.sln` | Modified | Added test project to solution |
| `integration/tests/pdp/test_products_api.py` | Modified | Fixed category endpoint response shape assertion |

---

## Self-Verification Checklist

- [x] Ran full relevant test suite and captured complete output
- [x] All new tests follow naming and structural conventions (`[Method]_[Scenario]_[Expected]`, Arrange/Act/Assert, `[ExcludeFromCodeCoverage]`)
- [x] No source code modified in protected repos (only test files)
- [x] Bug found is documented with reproduction steps and diagnosis
- [x] QA report written to `reports/`
- [x] New tests pass when run (both Debug and Release)
