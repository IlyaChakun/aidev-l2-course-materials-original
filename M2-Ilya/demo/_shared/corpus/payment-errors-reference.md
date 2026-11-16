---
title: Payment Errors Reference
section: Billing
date: 2026-06-23
---

# Payment Errors Reference

This reference lists the error codes that Lumen shows when a card payment does not go through, explains what each one means, and describes what the customer, the workspace Owner and support staff should do. Payments are made by the workspace Owner in the Billing area. For how billing works in general, including retries and read-only mode, see the Billing, Invoices and Payments article. For refund questions, see the Refund and Cancellation Policy.

## How to use this reference

When a payment fails, the Owner sees a message with a code that starts with `E-40`. The code tells support which step of the payment failed. Always ask the customer for the exact code and, if possible, a screenshot of the message. Ask for the time of the attempt in UTC and the workspace name.

The codes in this article are the payment codes:

| Code | Message | Short meaning |
|---|---|---|
| E-4012 | Payment method rejected | 3-D Secure authentication failed or timed out |
| E-4020 | Card declined by issuer | The bank declined the payment |
| E-4031 | Currency not supported by card | The card cannot be charged in the billing currency |
| E-4040 | Duplicate payment attempt blocked | Two attempts within 60 seconds |

Other errors, for example sign-in or report errors, are explained in the Troubleshooting and Error Codes article. A general HTTP error on the payment page is covered in the section "HTTP 500 on the payment page" below.

Two rules apply to every payment error:

1. **Never ask for a full card number, CVC, or password.** The only card detail support may ask for is the last four digits.
2. **Do not promise a refund or a correction.** If a customer disputes an amount, collect the data and escalate to the Billing team.

Payment errors can only be fixed by the Owner, since only the Owner can use the Billing area. An Admin or Member who sees an error should ask the Owner to retry.

## E-4012 Payment method rejected

**Message:** "Payment method rejected"

**Meaning:** The payment needed 3-D Secure authentication, and the authentication failed or timed out. 3-D Secure is the extra confirmation many banks require for online card payments. It usually appears as a notification in the banking app, a text message with a code, or a pop-up window from the bank.

**Common causes:**

- The Owner did not approve the request in the banking app in time.
- The pop-up window of the bank was blocked by the browser or closed too early.
- The code from the bank was typed incorrectly.
- The banking app was not installed on the phone that received the request, or notifications for it were turned off.
- The bank's own session expired because the Owner waited too long.

**What to do:**

1. Ask the Owner to **retry the payment and approve the request in the banking app** as soon as it appears.
2. If the pop-up is blocked, allow pop-ups for the Lumen site in the browser and retry.
3. If the problem repeats, ask the Owner to **use another card**.
4. If the customer says the bank charged the card although the error appeared, treat it as a possible duplicate and follow the double-charge guidance in the billing article.

The customer should not retry many times in a row. If the second attempt also fails with this code, using another card is the faster path. Support does not need any card data to solve this error. The Owner makes the retry in the browser, and the bank confirms it in its own app.

## E-4020 Card declined by issuer

**Message:** "Card declined by issuer"

**Meaning:** The bank that issued the card (the issuer) declined the payment. Lumen cannot see the reason, because banks do not share it with merchants. The decision is made by the bank.

**Common causes:**

- Not enough available funds or a credit limit that was reached.
- The card has expired or was replaced and the old number is no longer valid.
- The bank blocks online payments or payments to foreign merchants on that card.
- The bank's fraud checks flagged the payment as unusual.
- The card is blocked or reported lost.

**What to do:**

1. Ask the Owner to **contact the bank** and ask why the payment was declined. The bank is the only party that can say.
2. After speaking with the bank, the Owner can retry the payment, but should not repeat it quickly several times.
3. Alternatively, ask the Owner to **try another card**. Accepted cards are Visa, Mastercard and American Express.

Support must not guess the reason, and must not suggest that the problem is with Lumen when the bank has declined the payment. At the same time, do not accuse the customer: say that the bank declined the request and that the bank can explain.

If a failed payment is part of a regular charge and not a manual one, remember that Lumen retries automatically. The retry sequence and the read-only date are described in the billing article, and the Owner should be told that fixing the card before the next retry is the quickest way to avoid interruption.

## E-4031 Currency not supported by card

**Message:** "Currency not supported by card"

**Meaning:** The card cannot be used to pay in the currency of the charge. Some cards, especially certain prepaid, virtual or local cards, can only pay in one currency or in a limited list of currencies.

**Common causes:**

- A prepaid or virtual card that is restricted to one currency.
- A card issued for use in one country with foreign-currency payments turned off.
- A bank setting that blocks international transactions.

**What to do:**

1. Ask the Owner to **try a different card**, preferably a standard credit or debit card from a major issuer.
2. If the Owner wants to keep using the same card, they can ask the bank whether payments in other currencies can be enabled.
3. After the setting is changed or the card is replaced, the Owner retries the payment in the Billing area.

Support should not recommend a specific bank, a specific card product or a way to avoid currency conversion fees. Any fee charged by the bank for a currency conversion is a matter between the customer and the bank.

A customer may ask "can you change the currency of my invoice?" The first line cannot change currencies or tax settings. If the customer insists, escalate the ticket to the Billing team with the workspace name and the code.

## E-4040 Duplicate payment attempt blocked

**Message:** "Duplicate payment attempt blocked"

**Meaning:** Lumen received **two payment attempts within 60 seconds** for the same workspace and stopped the second one. The block exists to protect the customer from being charged twice when a button is pressed repeatedly or the page is reloaded during processing.

**What to do:**

1. Ask the Owner to **wait 10 minutes** before trying again.
2. Before retrying, open **Settings -> Billing -> Invoices** and check whether the first attempt succeeded. A new invoice or a changed status can show this.
3. Retry once if the invoice is still open. **Do not retry more than twice** in total.

The key point is that the first attempt may already have succeeded. The blocked second attempt is not a failure to be repeated at once; it can actually mean that the money is already on its way. A customer who repeats the attempt quickly may be charged twice.

| Customer report | Likely situation | Action |
|---|---|---|
| "I clicked Pay twice and saw E-4040" | The second click was blocked | Wait 10 minutes, check invoices |
| "I see E-4040 but never clicked twice" | The page reloaded during processing | Wait 10 minutes, check invoices |
| "I see two amounts in my banking app" | Possibly a hold and a charge | See the billing article for holds |
| "Two completed charges after waiting" | Possible duplicate charge | Collect the data and escalate to the Billing team |

If the customer reports two completed charges, never promise money back. Collect the payment reference (`PAY-######`), the date, the amount and the last four digits of the card only, and escalate.

## HTTP 500 on the payment page

An HTTP 500 error on the payment page means that something went wrong on the Lumen side while the page was being processed. It is usually temporary. It differs from the codes above because it does not say what happened to the payment itself.

**Do not retry more than twice.** A payment that returned an error page may still have been accepted in the background. Repeating the attempt again and again is the most common way a true duplicate charge happens.

Recommended steps for the Owner:

1. After the error, do not press Pay again immediately.
2. Open **Settings -> Billing -> Invoices** in a new tab and check whether the invoice shows a payment.
3. If there is no payment, retry once.
4. If the error appears again, stop after the second attempt and contact support.

When writing to support, the Owner should include the time of the attempt in UTC, the workspace name, the browser and version, and a screenshot of the page. A typical log excerpt that a support agent may see in a ticket looks like this:

```
2026-06-23 09:14:07 UTC  POST /billing/pay  status=500
2026-06-23 09:14:41 UTC  POST /billing/pay  status=200  ref=PAY-081244
```

In this example the second attempt succeeded. If the first attempt was also recorded as a payment, the Billing team must check for duplicates. A general HTTP 500 on other pages is covered in the Troubleshooting and Error Codes article.

## Amount disputes and escalation

Any dispute about an amount goes to the **Billing team**. Examples include:

- "The invoice is higher than the price I was told."
- "I was charged after I cancelled."
- "I was charged twice and the second line is not pending any more."
- "The amount on my card statement is different from the invoice."

The first line does not decide whether the customer is right, does not calculate any difference, and does not mention refunds or corrections as a certain result.

Collect these items:

1. The error code, if any, and the time (UTC).
2. The payment reference (`PAY-######`) and the invoice number (`INV-######`) if known.
3. The date and amount of each charge in question.
4. The last four digits of the card, and no other card details.

Write the escalation reason as one short sentence, for example:

```
Customer disputes a charge of the amount shown on PAY-081244 dated 2026-06-23; card ending 4417; two charges visible.
```

## Quick decision table

| Code or symptom | First action | If it fails again |
|---|---|---|
| E-4012 | Retry and approve in the banking app | Use another card |
| E-4020 | Contact the bank | Try another card |
| E-4031 | Try another card | Ask the bank about currency settings |
| E-4040 | Wait 10 minutes, check invoices | Do not retry more than twice; escalate if unclear |
| HTTP 500 on payment page | Check invoices before retrying | Do not retry more than twice; escalate |
| Amount dispute | Collect data | Escalate to the Billing team |
