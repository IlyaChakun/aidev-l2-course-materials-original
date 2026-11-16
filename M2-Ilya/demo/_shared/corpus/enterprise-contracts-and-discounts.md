---
title: Enterprise Contracts and Discounts
section: Billing
date: 2026-05-12
---

# Enterprise Contracts and Discounts

This article explains how contract-based pricing works at Lumen: what an order form is, who manages it, how a negotiated discount appears on invoices, and what first-line support can and cannot do when a customer asks about a discount. Published prices are listed in the Plans and Pricing article. Invoices in general are explained in the Billing, Invoices and Payments article.

## Overview

Most Lumen customers pay the published price of their plan. Some larger organisations agree a different commercial arrangement with Lumen Labs. That arrangement is called a **contract**, and it is documented in a **signed order form**.

The most important rule is simple: **discounts exist only through a signed order form that is managed by an Account Manager.** There are no discount codes, no public promotions that a support agent can apply, and no informal agreements that change the amount on an invoice. If a discount is not in a signed order form, it does not exist.

The people involved have different roles:

| Role | What they do |
|---|---|
| Sales | Talks to prospective customers, prepares proposals |
| Account Manager | Owns the customer relationship and the order form after signing |
| Billing team | Reviews and corrects invoices, handles amount questions |
| First-line support | Explains the process, collects data, escalates |

First-line agents are not part of the commercial process. They cannot start a negotiation, give an estimate, or say what a customer would pay under a contract. Their job is to direct the customer to the right person and to pass on the facts when something appears to be wrong with an invoice.

## What an order form is

An order form is a signed document between the customer organisation and Lumen Labs. It describes the services that the customer buys and the commercial terms that apply. In general, an order form includes:

- The names of the two parties.
- The workspace or workspaces that the order form covers.
- The plan and the number of seats that are part of the agreement.
- The pricing terms that differ from the published prices, if any.
- The dates when the agreement starts and ends.
- A contract reference that identifies the document.

The **contract reference** is the identifier that appears on the order form. Support staff use it to find the right contract quickly, so it is the first thing to ask for when a customer writes about a contract issue.

An order form is not created in the product. A workspace Owner cannot create or edit one in Settings, and an agent cannot edit one either. Changes to the terms need a new signed document or an amendment, both prepared by the Account Manager.

A signed order form is also the only source of truth about a negotiated discount. A statement in an email or chat message, even from someone at Lumen, does not replace it. If a customer says that "someone told me I would get a discount", the right answer is that discounts are applied only through a signed order form, and the customer should speak to the Account Manager.

## Volume tiers

Customers with many seats or heavy use sometimes ask for a volume discount. Lumen does have volume tiers, but they are **negotiated and not published**. There is no public list of thresholds and percentages, and the numbers differ between customers.

This has some practical consequences:

1. **Nobody in first line can say what a tier is.** Not the threshold, not the percentage, not whether a customer would qualify.
2. **There is no calculator.** An agent cannot estimate a price for a customer with 200 people or 2,000 people, and should not try to extrapolate from the published prices.
3. **Past agreements are not a reference.** An arrangement made with one customer does not give a right to the same terms for another.

When a prospective customer asks about volume pricing, the correct answer is that tiers are agreed individually and that an Account Manager can discuss them. The agent can direct them to the sales contact form on the Lumen website, or, if a ticket must be created, escalate it as a sales inquiry.

### Example of a correct reply

```
Hello, thank you for your interest. Volume pricing is agreed individually through a signed order form, which is handled by our Sales team and Account Managers. I have passed your request on so that they can contact you. For published plan prices, please see the Plans and Pricing article.
```

The reply does not mention percentages, does not promise a discount and does not say how long the process will take.

## What first-line agents can and cannot do

The boundaries are the same for every ticket that mentions a discount, a contract or special pricing.

| First-line agents CAN | First-line agents CANNOT |
|---|---|
| Explain that discounts exist only through a signed order form | Apply a discount to any invoice |
| Explain that the Account Manager manages the order form | Confirm that a discount exists or applies |
| Ask for the contract reference and invoice number | Calculate what a discount should be |
| Point to the published prices in the pricing article | Offer, hint at or promise a discount |
| Escalate the ticket with the right facts | Change the price of a plan |
| Describe where to see the Contract discount line on an invoice | Say whether a contract is valid or expired |

Two situations need extra care.

**The customer quotes a number.** A customer may write, "My contract gives me 20% off, but the invoice shows the full price." The agent must not say whether 20% is correct. The only task is to record the claim as the customer's own words, collect the references, and escalate.

**The customer asks for a discount without a contract.** The agent explains that discounts require a signed order form, and, when appropriate, gives the sales contact route. The agent does not offer a "one-off" gesture of any kind.

Support also does not discuss internal approval steps. The customer is told who can help, not how the internal process works.

## The Contract discount line on invoices

When a signed order form applies a discount to a workspace, the invoice for that workspace shows a separate **Contract discount** line. This line sits with the other invoice lines: the plan, the seats and the tax. The customer can see it in the invoice PDF under **Settings -> Billing -> Invoices**, which is available to the Owner only.

The existence of this line is how the customer, and support, can tell that the contract terms were applied. For that reason, its absence is an important signal.

A short checklist for looking at an invoice:

1. Does the invoice have a plan line and a seats line?
2. Is there a **Contract discount** line?
3. Does the tax block appear after the discount line?
4. Is the invoice number in the format `INV-######`?

Seeing a Contract discount line does not mean that the amount is correct. It only shows that a discount was applied. If the customer disputes the amount, the case goes to the Billing team.

An example of how the relevant part of an invoice may be described when a ticket is written up (the amounts are illustrative only):

```
INV-004218
Plan line ............... included
Seats line .............. included
Contract discount ....... present
Tax (VAT) ............... present
```

In a ticket, the agent only notes whether the line is present or absent. The agent does not copy amounts into explanations to the customer or comment on whether they look right.

## When the discount line is missing

If a customer says that their contract provides a discount and the invoice does not show a **Contract discount** line, the first line must **escalate to the Billing team**. The first line does not try to find the reason, and it does not tell the customer whether the discount will be added later.

Collect these items before escalating:

1. **The contract reference** from the order form.
2. **The invoice number** (`INV-######`) of the invoice without the line.
3. The workspace name.
4. The email address of the Owner as shown in the ticket.
5. The date of the invoice.

The escalation reason must be a single factual sentence, for example:

```
Customer states a signed order form applies to the workspace; invoice INV-004218 has no Contract discount line; contract reference as provided by the customer.
```

The Billing team compares the invoice with the order form and decides what to do. If the case involves a correction of money already charged, the Billing team handles that as well; no first-line agent should promise a correction. The Account Manager may be involved by the Billing team when the order form itself needs interpretation.

Support should tell the customer, in plain words, that the ticket has been passed to the Billing team and that they will review the invoice together with the contract. No date and no outcome should be given.

### Priority of such tickets

A missing discount line on a regular invoice is normally a normal-priority ticket. If the customer reports a repeated contact about the same issue, the rules in the Escalation and Routing Policy about raised priority apply.

## Renewals, changes and ending a contract

Contracts have a start and an end, and questions about them are common as the end date approaches.

**Renewal.** When a contract is coming to an end, the Account Manager contacts the customer to agree the next period. The first line cannot renew a contract, extend one or say what the terms will be.

**Changing seats or plan.** A customer under a contract who wants more seats, a different plan or additional workspaces should talk to the Account Manager first, because the order form may define the terms. Using the self-service Billing settings may produce a charge that does not follow the contract.

**Ending the arrangement.** The ability to cancel a plan in the Billing settings and the rules on refunds are described in the Refund and Cancellation Policy. Whether a signed order form contains different conditions for ending the agreement is decided by that document, and not by support. Any customer who asks about leaving a contract early is directed to the Account Manager and the ticket is escalated.

**Who the Account Manager is.** Customers under contract know their Account Manager by name. Support does not give out names or direct contact details of Lumen employees. If the customer has lost the contact, the ticket is escalated so that Sales can reconnect them.

## Frequently asked questions

**Can support give me a discount?** No. Discounts exist only through a signed order form managed by an Account Manager.

**Where can I see the discount on my invoice?** On the Contract discount line of the invoice, available as a PDF in Settings -> Billing -> Invoices for the Owner.

**Are volume discounts published?** No. Volume tiers are negotiated individually.

**Can support calculate what my price would be?** No. First-line agents cannot apply, confirm or calculate discounts.

**My invoice has no Contract discount line. What now?** Send the contract reference and the invoice number. The ticket goes to the Billing team.

**Who handles contracts?** Sales and the Account Manager.

**Is the Contract discount line the same as a refund?** No. A discount lowers the amount charged under an agreement; a refund returns money already paid, and refunds follow the Refund and Cancellation Policy.
