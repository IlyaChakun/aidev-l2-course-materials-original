---
title: Billing, Invoices and Payments
section: Billing
date: 2026-03-17
---

# Billing, Invoices and Payments

This article explains how billing works in Lumen: which payment methods are accepted, when and how you are charged, where to find and read invoices, what happens when a payment fails, and how taxes and VAT IDs are handled. It is written for workspace Owners and for support staff who answer billing questions. Prices and plan limits are listed in the Plans and Pricing article. Refunds and cancellation are covered in the Refund and Cancellation Policy, and payment error codes are covered in the Payment Errors Reference.

## How billing works

Lumen is billed per workspace. The plan you chose, together with any extra seats, produces one charge per billing period. The period is either one month or one year, depending on the billing period chosen when the plan was started.

Your **billing date is the day the plan started** each month or each year. A plan that started on the 12th of a month is charged on the 12th of every following month; an annual plan that started on 12 March is charged again on 12 March of the next year. Changing the plan or adding seats does not move the billing date.

Only the workspace **Owner** manages billing. Admins can manage the team and integrations, but they cannot open the Billing area, change the payment method or download invoices. If an Admin writes to support about a payment, the right answer is that the Owner of the workspace must handle it.

Each charge creates two records. The first is an invoice, which is the document that describes what was charged and why. The second is a payment reference, which identifies the actual payment attempt with your card. Both appear in the Billing area and are quoted by support when a payment has to be investigated.

| Record | Format | Example | What it identifies |
|---|---|---|---|
| Invoice number | `INV-######` | INV-004218 | The invoice document |
| Payment reference | `PAY-######` | PAY-077305 | One payment attempt |

## Accepted payment methods

Lumen accepts the following cards:

- Visa
- Mastercard
- American Express

**No cash and no checks are accepted.** Lumen does not accept bank transfers, payment links sent by email, or payments made outside the application. If a customer offers to pay by any of these methods, explain politely that only the three card types above can be used. Customers who have a signed contract with an Account Manager should speak to that person about any special arrangement, because the first line cannot agree to one.

### Adding or changing the card

The Owner can change the card in the Billing area of Settings. The usual steps are:

1. Sign in as the workspace Owner.
2. Open **Settings -> Billing**.
3. Choose the payment method section and select the option to add a new card.
4. Enter the card details and, if the bank asks for it, confirm the request in the banking app (3-D Secure).
5. Save the card and set it as the default payment method.

The new card is used from the next charge. Changing the card does not trigger an immediate charge and does not change the billing date.

Many banks ask for extra confirmation for online card payments. This confirmation happens in the bank's own window or app, not in Lumen. If it fails or times out, the payment is rejected; see the Payment Errors Reference for what to do. Support never asks a customer to send a full card number, the CVC code or a password. For a payment investigation, only the **last four digits** of the card are needed.

## Finding and downloading invoices

Invoices are available only to the workspace **Owner**. To open them:

1. Sign in as the Owner.
2. Go to **Settings -> Billing -> Invoices**.
3. Find the invoice by date or by number.
4. Select the invoice to download it as a **PDF**.

Invoice numbers use the format `INV-######`, for example `INV-004218`. Payment references use the format `PAY-######`. Invoices are generated after each successful charge and also when a charge is created but not yet paid.

If an Admin or Member asks for an invoice, they cannot download it themselves. The Owner must either download it and forward it, or, when the Owner is no longer at the company, follow the ownership transfer process described in the Team and Roles article.

### What an invoice shows

Each invoice lists the same blocks, in this order:

| Block | Content |
|---|---|
| Header | Invoice number, issue date, billing period |
| Workspace details | Workspace name, billing name and address |
| Plan line | The plan and the billing period |
| Seats line | Included seats and any extra seats |
| Contract discount line | Only if a signed order form applies a discount |
| Tax | VAT or sales tax, depending on country |
| Total | Amount charged, with the payment reference |

If a customer asks why the amount is different from last month, compare the plan line and the seats line first. A new seat, a plan upgrade or a tax change are the most common reasons. The tax block depends on the billing country, so the same plan can produce different totals for customers in different places.

## Failed payments and retries

A charge can fail for many reasons: the card has expired, the bank declined it, the limit was reached, or the 3-D Secure confirmation was not approved. When this happens, Lumen does not stop the workspace at once. It follows a fixed sequence.

| Time since the failed charge | What happens |
|---|---|
| Day 0 | The charge fails and the Owner receives an email |
| Day 1 | First automatic retry |
| Day 3 | Second automatic retry |
| Day 5 | Third automatic retry |
| Day 7 | If still unpaid, the workspace becomes read-only |

Automatic retries happen after **1, 3 and 5 days**. After **7 days** without a successful payment, the workspace becomes **read-only**. In read-only state people can still sign in and look at their data, but they cannot create or change orders and reports.

The data of a read-only workspace is **kept for 90 days**. If the Owner pays during this time, the workspace returns to normal and nothing is lost. For anything about what happens to data after that period, escalate to the relevant team instead of guessing.

### What the Owner should do

The quickest way to restore a workspace is to fix the cause before the next retry:

1. Open **Settings -> Billing** and check the card expiry date.
2. Add a new card if the old one is expired or was replaced.
3. Use the option to pay the open invoice, and approve the bank confirmation if requested.

Customers who attempt several payments in a row can create duplicate charges. Support should advise waiting a few minutes between attempts and following the guidance in the Payment Errors Reference.

## Double charges and authorization holds

"I was charged twice" is one of the most common billing questions. Most of the time there was only one real charge.

When a card payment is started, the bank may place a **temporary authorization hold** for the amount. The hold reserves the money while the payment is processed. If the first attempt did not complete, for example because the 3-D Secure window was closed, the hold stays on the account for a while even though no payment was taken. The customer then sees two lines in the banking app: a hold and the final charge. A hold **disappears from the card statement within 3-5 business days**, without any action on either side.

How to answer a customer who reports a double charge:

1. Ask the customer to check whether one of the lines is marked "pending" or "authorization" in the banking app.
2. Explain that a pending hold normally drops off within 3-5 business days.
3. If the customer confirms that two completed charges exist after that period, collect the data listed below and escalate to the **Billing team**.

Data to collect, in this order:

- The payment reference (`PAY-######`) of each payment
- The dates and amounts of both lines
- The last four digits of the card, and nothing more

A true duplicate charge is investigated and corrected **only by the Billing team**. The first line must not promise money back, confirm that a refund will be paid, or say how long the correction will take. A good reply says that the case has been passed to the Billing team and that they will review it. For the formal rules, see the Refund and Cancellation Policy.

## Taxes and VAT IDs

Lumen adds tax to invoices according to the billing country. Depending on the country, this is **VAT** or **sales tax**. The tax appears as a separate line on the invoice and is not part of the plan price shown in the Plans and Pricing article.

Businesses that are registered for VAT can add a **VAT ID** to their billing settings. This is done by the **Owner**:

1. Sign in as the Owner and open **Settings -> Billing**.
2. Find the billing details section.
3. Enter the VAT ID and the legal name and address of the company.
4. Save the changes.

New details appear on invoices created after the change. Invoices that were already issued are not rewritten, so a customer who forgot to add a VAT ID before a charge should be told that the details will apply from the next invoice. The first line cannot decide on tax exemptions or give tax advice. For a question about whether tax should apply to a specific country or company, escalate to the Billing team.

### Billing name and address

The name and address on invoices are the ones saved in the billing details. If a company changes its legal name or address, the Owner updates them in the same place. Document details are used exactly as entered, so a typo in the company name will also appear on the invoice.

## Contract discounts on invoices

Some workspaces have a negotiated arrangement with Lumen. When one applies, the invoice contains a line called **Contract discount**. This line is created from a signed order form and is described in the Enterprise Contracts and Discounts article.

For billing support, the key points are:

- The Contract discount line is visible on the invoice, between the seats line and the tax block.
- Its absence on an invoice that should have it is a billing problem, not something the first line can fix.
- The first line never calculates, confirms or applies discounts.

If a customer says that the discount is missing, collect the invoice number, the contract reference and the workspace name, then escalate to the Billing team.

## Quick reference for support staff

| Question | Answer |
|---|---|
| Which cards are accepted? | Visa, Mastercard, American Express |
| Can the customer pay by cash or check? | No |
| Who can see invoices? | The workspace Owner only |
| Where are invoices? | Settings -> Billing -> Invoices, as PDF |
| What is the invoice number format? | `INV-######` |
| What is the payment reference format? | `PAY-######` |
| When does a charge happen? | On the billing date, the day the plan started |
| When do retries happen? | After 1, 3 and 5 days |
| When does the workspace become read-only? | After 7 days unpaid |
| How long is data kept while read-only? | 90 days |
| Why do I see two charges? | Usually an authorization hold, gone in 3-5 business days |
| Who corrects a true duplicate charge? | The Billing team only |
| Who adds a VAT ID? | The Owner, in Billing settings |

Whenever a billing question is about an amount that a customer disputes, the correct next step is to escalate to the Billing team with the payment reference, the date, the amount and the last four digits of the card.
