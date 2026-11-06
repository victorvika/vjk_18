# BACKEND_SPEC — Original Backend (Observed) → Own Backend (Pudhu Design)

> ⚠️ Idhu original server-ai copy/clone panna spec **illa**. Enna *types* of API irundhuchu nu purinjikittu,
> namma own clean backend design panna reference. Original credentials/endpoints reuse panna koodadhu.

## 1. Original-la Therindhadhu (static analysis)

| Item | Observed |
|------|----------|
| Base URL | `http://olaridetaker.com` (cleartext ⚠️), app-la **server URL change panna option-um iruku** (`setServerUrl`) |
| Client | Retrofit/OkHttp (Moshi) + Ktor remnants; `PersistentCookieJar`, certificate pinner, security interceptor (token) |
| Auth | User ID + Password login (`loginForm`) → token + cookies; password device-la AES/GCM (Keystore) encrypt save |
| APIs | `login`, `dashboard` (status: plan, expiry, secondsRemaining, blocked), `heartbeat` (loop, remote block check), `createOrder`, `verifyOrder`, `paymentSuccess`, `logout` |
| Payment | UPI QR (personal handle, redacted) → server verify → **CreatedCredentials** (system generate panna User ID + password) → auto-login |
| Plans | 1 / 7 / 15 / 30 / 365 days; ₹150–₹2999 range; server `PlanCatalogItem` catalog-um varum |
| Anti-tamper | Plan time: server `secondsRemaining` + device monotonic clock sync (wall-clock maatina kandupidikum) |

## 2. Namma Own Backend (Recreate)

**Stack suggestion:** Firebase (Auth + Firestore + Cloud Functions) **illa** simple VPS: Kotlin Ktor / Node Fastify + PostgreSQL. Solo dev-ku Firebase fast.

```
POST /auth/login            {userId, password}        → {token, plan, expiresAt, secondsRemaining}
GET  /dashboard             (Bearer)                  → DashboardStatus
POST /heartbeat             {deviceFp}                → {blocked, secondsRemaining}
POST /orders                {planId}                  → {orderId, amount, upiUri, qrImageUrl}
POST /orders/verify         {orderId}                 → {status} → success-na credentials issue
GET  /plans                                           → PlanCatalog[]
POST /auth/logout
```

**Original-la irundhu kathuka vendiya nalla vishayam:** server-time + monotonic sync, heartbeat block flag,
order→verify→credentials flow.
**Fix panna vendiyadhu:** HTTPS only, no personal UPI handle (Razorpay/Stripe payment links),
debug-sign vendaam (release keystore + vault backup), device fingerprint = privacy policy-la disclose.

## 3. Data Models (Room + API common)

```kotlin
RideHistoryEntity(id, appName, fare, fareString, pickupKm, tripKm, pickupLocation, dropoffLocation, timestamp)
PlanCatalogItem(id, label, days, price, desc, tag)
LoginResponse(success, token, userId, plan, planExpires, secondsRemaining, isSubscribed, isBlocked)
```
