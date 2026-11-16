---
title: Integrations and API
section: Technical
date: 2026-04-08
---

# Integrations and API

Lumen connects to the tools that small businesses already use, and it offers a REST API and webhooks for custom work. This article describes the four available integrations, how to create and protect API keys, the API rate limits, how webhooks are delivered and verified, and how to troubleshoot the most common problems.

## Available integrations

Lumen has exactly four integrations: **Shopify**, **WooCommerce**, **Zapier**, and **Slack**. No other integrations exist at this time. If a customer asks about a connection that is not on this list, the correct answer is that it is not available, and the customer may use Zapier or the API to build a connection of their own.

| Integration | What it does | Direction |
|---|---|---|
| Shopify | Brings orders from a Shopify store into Lumen | Store to Lumen |
| WooCommerce | Brings orders from a WooCommerce store into Lumen | Store to Lumen |
| Zapier | Connects Lumen events to other apps through Zapier workflows | Both |
| Slack | Sends Lumen notifications into a Slack channel | Lumen to Slack |

Integrations are managed in the web app under **Settings → Integrations**. Connecting or disconnecting an integration requires the Owner or Admin role. A Member or Viewer can see which integrations are active but cannot change them. Role details are in the team and roles guide.

### Shopify and WooCommerce

The two store connections work the same way from the user's point of view. After the store is connected, new orders are imported automatically and appear in reports within a few minutes. Orders created before the connection was made can be brought in with a CSV import; the onboarding guide explains that process.

A store connection can stop working when the store owner changes the store password, removes the Lumen app from the store, or revokes the access token. The fix is always to disconnect and connect again from **Settings → Integrations**. Reconnecting does not duplicate orders that have already been imported.

### Slack

The Slack integration posts notifications to a channel chosen during setup. It does not read Slack messages. If notifications stop appearing in Slack, check that the Lumen app is still a member of the channel, because removing the app from a channel silently stops delivery. Reconnecting the integration and selecting the channel again restores it. General notification behavior is covered in the notifications article.

### Zapier

The Zapier connection lets a customer start a workflow when something happens in Lumen, for example when a new order arrives, or create records in Lumen from another app. Zapier is configured on the Zapier side, with a Lumen API key used for authentication. Because it relies on the API, it is subject to the same rate limits described below.

## API keys

The Lumen API lets a workspace read and write its own data programmatically. API access depends on the plan of the workspace; the plans and pricing article lists which plans include it. A customer on a plan without API access will not see the **Developers** page.

API keys are created and managed by the Owner or an Admin at **Settings → Developers → API keys**.

### Creating a key

1. Open **Settings → Developers → API keys**.
2. Click **Create key**.
3. Enter a descriptive name, such as "Warehouse sync" or "Zapier production".
4. Choose whether the key is read-only or read and write.
5. Click **Create** and copy the key immediately.

The full key is shown **only once**, at creation. Afterwards the page shows only the first and last characters. If a key is lost, it cannot be recovered; create a new key and delete the old one.

### Keeping keys safe

- Treat a key like a password. Never paste it into a support ticket, a chat, a screenshot, or a public code repository.
- Use one key per application, so a single key can be revoked without breaking the others.
- Revoke keys that are no longer needed by selecting **Delete** next to the key. Deleting takes effect immediately, and requests that use the key start to fail with HTTP 401.
- If a key may have been exposed, delete it first, then create a replacement.

Support staff must never ask a customer for a full API key. If a key must be identified, ask for its name and the last four characters shown on the page. A suspected leak of a key is a security matter and is handled according to the security and compliance article.

Requests are authenticated with a bearer header:

```
curl https://api.lumen.example/v1/orders?limit=25 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Rate limits and HTTP 429

To keep the service responsive for everyone, the API limits how many requests a workspace can send each minute. The limit depends on the plan.

| Plan | Requests per minute |
|---|---|
| Team | 60 |
| Business | 300 |

The limit is counted per workspace, not per key. Three integrations that each send 30 requests a minute on a Team workspace together reach 90 requests a minute, which is over the limit.

When the limit is exceeded, the API returns HTTP **429 Too Many Requests**. The response includes a **`Retry-After`** header with the number of seconds to wait before sending another request.

```
HTTP/1.1 429 Too Many Requests
Retry-After: 12
Content-Type: application/json

{"error": "rate_limited", "message": "Too many requests"}
```

### Handling 429 correctly

1. Stop sending requests and wait for the number of seconds in `Retry-After`.
2. Resume at a slower pace, and avoid retrying in a tight loop, which only extends the delay.
3. Reduce the number of calls: request larger pages instead of many small ones, and cache data that rarely changes.
4. If the workload really needs more requests, a higher plan has a higher limit; the support agent should point the customer to the plans and pricing article instead of promising a change.

Customers often discover the limit when a Zapier workflow suddenly shows errors after a busy sales day. The Zapier task history will show 429 responses, and the fix is to spread the workflow over time or reduce the number of steps.

## Webhooks

Webhooks let Lumen send an HTTP POST request to a URL of the customer's choice when an event occurs, for example when an order is created or updated. They are configured at **Settings → Developers → Webhooks** by an Owner or Admin.

### Delivery and retries

A delivery is considered successful when the receiving server answers with a status code in the 2xx range within a few seconds. Any other answer, a timeout, or a connection error counts as a failure. Lumen then **retries the delivery 5 times** with **exponential backoff**, which means the wait between attempts grows longer each time. When all 5 retries have failed, the delivery is marked as failed and the webhook page shows the error **E-5003**.

Because retries can happen, the receiving system may see the same event more than once. Receivers should use the event ID in the payload to ignore duplicates.

### Verifying the signature

Every webhook request carries the header **`X-Lumen-Signature`**. The value is a hash computed from the request body and the webhook's signing secret. The receiver should calculate the same hash and compare it before trusting the payload. A request with a missing or wrong signature should be rejected.

```
POST /hooks/lumen HTTP/1.1
Content-Type: application/json
X-Lumen-Signature: sha256=3f2a9c0d41b7e5a8...

{"event": "order.created", "id": "evt_8841", "order_id": 10482}
```

### Troubleshooting E-5003

If the webhook page shows **E-5003**, work through this checklist:

1. Confirm the URL is correct, uses HTTPS, and is reachable from the public internet.
2. Check that the receiving server returns a 2xx code quickly; long processing should happen after the response is sent.
3. Check firewalls and security rules that may block requests from unknown addresses.
4. Verify that signature checking is not rejecting valid requests because of a wrong secret.
5. After fixing the cause, use **Send test event** on the webhook page and check that the result is green.

If the receiving server is healthy and E-5003 continues, collect the webhook URL host name, the event ID, and the time in UTC, and pass them on to support.

## Common API response codes

Besides the 429 response described above, developers meet a small set of standard status codes. Knowing them helps a support agent tell a customer-side mistake from a real fault.

| Status | Meaning | Typical cause | What to suggest |
|---|---|---|---|
| 200 / 201 | Success | Request accepted | Nothing to do |
| 400 | Bad request | Malformed JSON or an invalid field value | Check the request body against the API reference |
| 401 | Unauthorized | Missing, mistyped, or deleted API key | Check the `Authorization` header; create a new key if needed |
| 403 | Forbidden | A read-only key used for a write, or a plan without API access | Use a read and write key, or check the plan |
| 404 | Not found | Wrong ID or wrong path | Check the object ID and the URL |
| 429 | Too many requests | Rate limit exceeded | Wait for `Retry-After` |
| 500 | Server error | Transient fault | Wait and retry later; see the troubleshooting article |

A response body always contains an `error` field and a short `message`, which can be copied into a ticket. The body never contains the API key.

## Good practice for API clients

Customers who build their own scripts often run into limits because of how the client is written. These suggestions prevent most problems.

1. **Page through results.** Use the `limit` and `page` parameters instead of requesting everything in a single call. Smaller pages are faster and are less likely to time out.
2. **Request only what changed.** Filter by an updated-since date rather than downloading all orders each time. This reduces the number of calls and keeps the workspace well below its per-minute limit.
3. **Back off on errors.** On a 429 or a 5xx response, wait and retry with a growing delay, and stop after a reasonable number of attempts.
4. **Make webhook handlers fast.** Acknowledge the request first, then process it in the background, so deliveries are not counted as failures.
5. **Store the event ID.** Both webhooks and API objects carry IDs that make it easy to detect and ignore duplicates.
6. **Use separate keys for test and production.** A mistake in a test script then cannot consume the production workspace's request allowance under the same key name, and revoking it is simple.

```
curl -X GET "https://api.lumen.example/v1/orders?limit=100&page=2&updated_since=2026-04-01T00:00:00Z" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### What support can and cannot do

First-line support can explain where to find keys, what the rate limit means, how retries work, and how to read a status code. Writing or debugging a customer's own code is outside the help center. If a customer reports that the API returns errors even though the request looks right, collect the request path, the status code, the time in UTC, and the workspace name, never the key itself, and escalate to the technical queue.

## Frequently asked questions

**Where do I get an API key?**
At **Settings → Developers → API keys**, if you are an Owner or Admin and your plan includes API access.

**I lost my API key. Can you show it again?**
No. Keys are displayed only once. Create a new key and delete the old one.

**Which integrations are available?**
Shopify, WooCommerce, Zapier, and Slack.

**How many times does Lumen retry a failed webhook?**
Five times, with exponential backoff, and then E-5003 is shown.

**What does the Retry-After header mean?**
It tells the client how many seconds to wait before the next request after an HTTP 429 response.
