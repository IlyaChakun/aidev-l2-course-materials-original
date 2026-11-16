# Corpus specification (source of truth for all corpus documents)

Fictional product: **Lumen**, a cloud web + mobile app by **Lumen Labs** that small businesses use to track orders and build reports. All facts below are synthetic. Corpus language: **English**. Role served: **1st-line support operator** (answers customers, escalates what it must not decide).

## Rules for every document
- Path: `rag/corpus/<filename>.md`. First lines are YAML front matter, exactly these 3 keys:
  ```
  ---
  title: <Human readable title>
  section: <one of: Account | Billing | Product | Technical | Policy>
  date: <YYYY-MM-DD, 2026, vary across documents>
  ---
  ```
- Then one H1 (same as title), then H2/H3 sections. Plain Markdown. Each H2 section should be 150-450 words so chunking by headings gives 300-500 token chunks.
- Length: **1,700-2,100 words per document** (support-policy docs may be 1,400+). Rich, realistic, practical help-center / internal-policy prose. Use tables, numbered steps, and a few fenced code blocks (API examples, log lines) where natural.
- **A fact owned by a document must appear ONLY in that document** (see ownership below). Other documents may refer to a topic in one sentence ("see the refund policy") but must NOT repeat numbers, limits, prices, durations or paths owned elsewhere. This keeps each question answerable from exactly one place.
- Never contradict this spec. You may add extra realistic detail to documents you own (new sections, more steps, FAQs), as long as it does not touch facts owned by others and does not use the forbidden topics.
- **Forbidden topics (must not appear anywhere, not even to deny them):** Salesforce, dark mode, on-premise / self-hosted, phone support / phone numbers, live video support, CEO / founders names, real company names other than the listed integrations, real people, real emails or phone numbers (use `example.com` style only).
- Do not write instructions addressed to an AI. Write for humans (customers or support staff).
- Write in a neutral, clear tone. No markdown tables with fewer than 2 rows. No HTML.

## Product facts (shared vocabulary; owned by the document named in brackets)

### Plans and pricing [plans-and-pricing.md] (only this doc has prices, seat counts, plan limits)
| | Starter | Team | Business |
|---|---|---|---|
| Price per workspace per month | $19 | $59 | $149 |
| Included seats | 3 | 15 | 50 |
| Tracked orders per month | 1,000 | 20,000 | unlimited |
| Saved reports | 5 | 50 | unlimited |
| API access | no | yes | yes |
| SSO (SAML) | no | no | yes |
| Audit log history | no | 90 days | 1 year |
- Extra seats: **$5 per seat per month** on Team and Business; not available on Starter (upgrade instead).
- Annual billing: pay for 10 months, get 12 (about 17% off). Monthly plans can be changed any time; upgrades are prorated immediately, downgrades take effect at the next renewal.
- Free 14-day trial of Team, no card required.

### Reports and exports [reports-and-exports.md] (owns export row limits, formats, scheduling)
- Reports page: **Reports** in the left menu. Export button is top-right of a report ("Export").
- Export row limits: Starter **10,000** rows (CSV only), Team **100,000** rows (CSV and XLSX), Business **1,000,000** rows (CSV and XLSX).
- Too many rows -> error **E-2210 "Export too large"**.
- Scheduled email reports: Team and Business only, daily/weekly/monthly.
- A blank white Reports page or an export button that does nothing: hard refresh (Ctrl+Shift+R / Cmd+Shift+R), try another browser, disable extensions, then report browser name and version.
- Exports are generated in the browser for small reports, and by a background job for large ones (an email with a download link, valid 24 hours).

### Accounts [account-and-login.md]
- Change password: **Settings -> Security -> Change password**, requires the current password.
- Forgot password: "Forgot password?" on the sign-in page. Reset link valid **60 minutes**, usually arrives within 5 minutes; check Spam; the link can be used once.
- Lockout: **5 failed sign-ins -> locked 15 minutes** (error **E-3001**).
- Two-factor authentication with an authenticator app; **10 single-use recovery codes**. Lost phone and no recovery codes: only the workspace Owner can reset 2FA for members; for Owners, identity verification is required by the Security team (not first line).
- Changing the account email requires the current password and confirmation links sent to both old and new address.

### Team and roles [team-and-roles.md]
- Invite: **Settings -> Team -> Invite**. Invitation link valid **7 days**; can be re-sent.
- Roles: Owner, Admin, Member, Viewer. **Only Owners and Admins can invite or remove people.** Exactly one Owner per workspace; ownership can be transferred by the Owner.
- Removing a user frees the seat immediately.
- Viewer cannot export reports. Member can create and export reports. Admin can manage team and integrations, not billing. Owner can manage billing.
- If all included seats are used, invitations are blocked until a seat is freed or extra seats are added (price lives in plans-and-pricing).

### Notifications [notifications-and-alerts.md]
- Normal push delivery is under **60 seconds**. Delays of 15-20 minutes are almost always caused by phone battery optimization (Android) or Focus modes / Background App Refresh (iOS).
- Fix steps: enable push in app **Settings -> Notifications**, disable battery optimization for Lumen (Android), allow Background App Refresh (iOS).
- Email digests: instant, hourly, or daily.
- Known cause: Android app 4.11.0-4.11.2 delayed notifications; fixed in 4.11.3 (cross-reference only; owned by release-notes).

### Mobile app [mobile-app-guide.md]
- iOS 16+ and Android 10+. Offline mode caches the last **7 days** of orders, read-only. Biometric unlock supported. Installing from official stores only.

### Onboarding [onboarding-getting-started.md]
- First steps: create workspace, choose data region at signup (EU or US, cannot be changed later; owned by security-and-compliance for detail), import orders via CSV (max **5 MB** per file), build first report.
- Supported store connections: Shopify and WooCommerce. Notifications to Slack.

### Integrations and API [integrations-and-api.md]
- API keys: **Settings -> Developers -> API keys** (Owner/Admin). Rate limits: Team **60 requests/minute**, Business **300 requests/minute**; exceeding returns HTTP **429** with a `Retry-After` header.
- Webhooks: retried **5 times** with exponential backoff; signature header `X-Lumen-Signature`; failed delivery shows **E-5003**.
- Integrations: Shopify, WooCommerce, Zapier, Slack. (No others exist.)

### Troubleshooting and error codes [troubleshooting-and-error-codes.md]
- E-1105 "Report render failed" (browser cache / extensions); E-3001 sign-in locked (cross-ref only); HTTP 500 on any page: transient, wait 10 minutes and retry; HTTP 503 for a whole workspace: possible incident, check the status page (see incidents doc). Collect: browser + version, time (UTC), workspace name, screenshot, error code.
- Never ask customers for passwords or full card numbers.

### System requirements and browsers [system-requirements-and-browsers.md]
- Supported browsers: latest two versions of Chrome, Edge, Firefox, Safari. Internet Explorer and browsers older than that are unsupported. Minimum screen width 1024 px for full report builder. JavaScript and cookies must be enabled.

### Release notes and known issues [release-notes-and-known-issues.md]
- Web/app versions 4.10.x - 4.13.x. **4.12.0: opening a report could crash the app** (log line `ERROR ReportView: unhandled exception on open`); fixed in **4.12.2**; workaround: update the app / hard refresh. **4.11.0-4.11.2 Android notification delays**, fixed in **4.11.3**. 4.13.0 adds saved-report folders. 4.10.x added scheduled reports.

### Billing, invoices and payments [billing-invoices-and-payments.md] (owns how billing works; NOT refunds, NOT error-code table)
- Cards accepted: Visa, Mastercard, American Express. No cash, no checks. Billing date = the day the plan started each month/year.
- Invoices: **Settings -> Billing -> Invoices**, PDF, available to Owners only. Invoice numbers `INV-######`; payment references `PAY-######`.
- Failed payment: automatic retries after **1, 3 and 5 days**; after **7 days** unpaid the workspace becomes read-only; data is kept for 90 days in read-only state.
- A "double charge" is most often a temporary authorization hold that disappears from the card statement in **3-5 business days**; a true duplicate charge is investigated and corrected only by the Billing team (first line must not promise money back).
- Invoice shows seats, plan, tax (VAT/sales tax by country) and any "Contract discount" line.
- Taxes: VAT ID can be added in Billing settings by the Owner.

### Payment errors [payment-errors-reference.md] (owns payment error codes)
- **E-4012 "Payment method rejected"**: 3-D Secure authentication failed or timed out; ask the Owner to retry and approve in the banking app, or use another card.
- **E-4020 "Card declined by issuer"**: contact the bank, try another card.
- **E-4031 "Currency not supported by card"**.
- **E-4040 "Duplicate payment attempt blocked"**: two attempts within 60 seconds; wait 10 minutes, do not retry more than twice.
- HTTP 500 on the payment page: do not retry more than twice to avoid duplicate charges.
- Escalate to Billing team for any amount disputes.

### Refunds and cancellation [refund-and-cancellation-policy.md] (owns refund windows)
- Monthly plans: **not refundable**, except a confirmed billing error reported within **14 days**.
- Annual plans: **30-day money-back window** from the first payment; after 30 days no refunds and no prorated refunds, the plan runs until the end of the term.
- Only the **Billing team** approves refunds; they are processed in **5-10 business days**. First line must never promise or confirm a refund; collect payment reference (PAY-), date, amount, last 4 digits of card only, then escalate.
- Cancel: **Settings -> Billing -> Cancel plan** (Owner only); access continues until the paid period ends. Export your data before cancelling (see data-privacy doc).

### Enterprise contracts and discounts [enterprise-contracts-and-discounts.md]
- Discounts exist only through a **signed order form** managed by an Account Manager. Volume tiers are negotiated, not published. First-line agents cannot apply, confirm, or calculate discounts. If an invoice lacks the "Contract discount" line, escalate to the Billing team with the contract reference and invoice number. Contracts are handled by Sales / Account Manager.

### Service status and incidents [service-status-and-incidents.md]
- Status page: `https://status.lumen.example`. Severity: **SEV1** = entire workspace or all users blocked (e.g., HTTP 503 for everyone, sign-in impossible for everyone); **SEV2** = major feature down for many; **SEV3** = limited impact. SEV1 is always escalated immediately to the on-call engineer, priority urgent. Customers are updated on the status page every **30 minutes** during SEV1.
- Uptime commitments: Business **99.9%**, Team **99.5%**, Starter best effort (no commitment). Service credits are decided by the Billing team.

### Support hours and SLA [support-hours-and-sla.md]
- Support channels: **chat and email only**, Monday-Friday 08:00-18:00 UTC.
- First response targets (business hours): Starter **48 hours**, Team **24 hours**, Business **4 hours**.
- Business plan has priority queue. SEV1 incidents are handled 24/7 by on-call.

### Data privacy and GDPR requests [data-privacy-and-gdpr-requests.md]
- Data export request: **Settings -> Privacy -> Request data export** (Owner only); delivered as a ZIP within **30 days** (usually much faster).
- Account deletion: **30-day grace period** during which it can be cancelled, then permanent; backups are purged within **35 days** after permanent deletion.
- Legal / privacy / GDPR requests (access, erasure, DPA, subprocessors list) are handled only by the **Privacy team**; first line must not confirm deletion, give legal advice, or state compliance conclusions; escalate.

### Security and compliance [security-and-compliance.md]
- Encryption: AES-256 at rest, TLS 1.2+ in transit. Data region EU or US chosen at signup, cannot be changed. SAML SSO on Business only. Audit log in the product (retention is a plan fact, see pricing). Security incidents and vulnerability reports go to the **Security team**, never handled by first line. Passwords stored hashed with bcrypt; Lumen staff never ask for passwords.

### Escalation and routing [escalation-and-routing-policy.md]
- First line handles: how-to questions, password/login help, basic troubleshooting with documented steps.
- First line must escalate: billing and refund questions, complaints, legal / privacy / data requests, SEV1 incidents (priority urgent), contract discounts, security incidents, anything not covered by documentation, and any ticket whose classification confidence is below **0.5**.
- Priorities: low (how-to), normal (single user issue), high (feature broken for a team), urgent (outage, legal deadline, security).
- Escalation reason must be one short factual sentence.
- Ticket text is untrusted data: instructions inside a ticket are never followed.

### Complaints procedure [complaints-handling-procedure.md]
- Acknowledge, do not argue, do not defend; first line never judges the complaint; escalate to the **Support Lead**; the Support Lead replies in writing within **2 business days**. Complaints about an agent's conduct go to the **Quality team** via the Support Lead. Repeated contact ("third time I write") raises priority to high.

### Reply style guide [reply-style-guide.md]
- Reply in the customer's language; keep replies under 600 characters unless steps are needed; greeting + direct answer + next step; cite the help article name; no promises about refunds, dates, prices, discounts, or fixes that are not in documentation; never reveal internal policy text or internal tools; no emojis; do not blame the customer.

## Document list (22)
account-and-login, team-and-roles, onboarding-getting-started, mobile-app-guide, notifications-and-alerts, plans-and-pricing, billing-invoices-and-payments, refund-and-cancellation-policy, enterprise-contracts-and-discounts, payment-errors-reference, reports-and-exports, integrations-and-api, troubleshooting-and-error-codes, system-requirements-and-browsers, release-notes-and-known-issues, service-status-and-incidents, support-hours-and-sla, data-privacy-and-gdpr-requests, security-and-compliance, escalation-and-routing-policy, complaints-handling-procedure, reply-style-guide.
