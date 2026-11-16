---
title: Plans and Pricing
section: Billing
date: 2026-02-09
---

# Plans and Pricing

This article describes the three Lumen plans (Starter, Team and Business), what each one costs, and which limits and features come with it. It is the reference for anyone who needs to compare plans, estimate a monthly bill, or decide when it makes sense to upgrade. All prices are per workspace, not per user, and are listed in US dollars.

Lumen is sold per workspace. A workspace holds your orders, reports, integrations and team members. Each workspace has exactly one plan at a time, and the plan decides how many people can work in it, how many orders it can track every month, and which advanced features are switched on.

## Plan overview

Lumen offers three plans. Starter is meant for a single owner-operator or a very small shop that wants basic order tracking and a handful of reports. Team is the plan most growing businesses use: it adds API access, more seats, a much higher order volume and a longer audit history. Business is for larger organisations that need single sign-on, unlimited tracked orders and the longest audit history.

The monthly price is a flat fee for the workspace. It already includes a fixed number of seats, so a small team does not pay anything extra for the people it already has. If you need more people than your plan includes, you can add seats on Team and Business, or move up to a bigger plan.

Every plan includes the web application and the mobile apps. Plans differ only in limits and in a short list of features, which are all shown in the comparison table below. Nothing else about the day-to-day experience changes when you switch plans: your data, reports and settings stay exactly as they are.

If you are not sure which plan fits, the usual starting point is the Team trial (see "Free 14-day trial" below). It lets you build real reports with real data before you decide anything.

## Plan comparison table

The table below is the complete list of plan limits. If a figure is not in this table, it is not a plan limit.

| | Starter | Team | Business |
|---|---|---|---|
| Price per workspace per month | $19 | $59 | $149 |
| Included seats | 3 | 15 | 50 |
| Tracked orders per month | 1,000 | 20,000 | unlimited |
| Saved reports | 5 | 50 | unlimited |
| API access | no | yes | yes |
| SSO (SAML) | no | no | yes |
| Audit log history | no | 90 days | 1 year |

A few notes on how to read the table:

- **Price per workspace per month** is the base price for the plan when billed monthly. Taxes are added on the invoice according to your country.
- **Included seats** are the people who can be active in the workspace at the same time without any additional charge.
- **Tracked orders per month** counts the orders Lumen records for your workspace in a calendar month, whether they arrive through a store connection, a CSV import or the API.
- **Saved reports** is the number of report definitions you can keep. Running or exporting a report does not use up a saved report.
- **Audit log history** is how far back you can look in the in-product audit log. Starter does not include an audit log.

## Seats and extra seats

A seat is one person with access to the workspace. Each plan includes a number of seats in its monthly price: 3 on Starter, 15 on Team and 50 on Business.

When a workspace needs more people than its plan includes, extra seats can be added on Team and Business for **$5 per seat per month**. Extra seats are not available on Starter. A Starter workspace that outgrows its three seats should upgrade to Team, which includes 15 seats and costs less than a long list of extra seats would.

Extra seats are added by the workspace Owner in the Billing area of Settings. The added amount appears as its own seat line on the next invoice, together with the plan line.

### Worked examples

The examples below show how a monthly total is built. They use monthly billing and exclude tax.

| Situation | Calculation | Monthly total |
|---|---|---|
| Team workspace with 15 people | $59 plan, no extra seats | $59 |
| Team workspace with 20 people | $59 + 5 extra seats x $5 | $84 |
| Business workspace with 50 people | $149 plan, no extra seats | $149 |
| Business workspace with 58 people | $149 + 8 extra seats x $5 | $189 |
| Starter workspace with 4 people | Not possible: upgrade to Team | $59 |

When a team grows, it is worth comparing the cost of extra seats with the next plan.

For how seats are freed, who may invite people and what happens when all seats are used, see the Team and Roles article.

## Tracked orders and saved reports

Two limits shape how much you can do with a workspace every month: the number of tracked orders and the number of saved reports.

**Tracked orders per month.** Starter tracks up to 1,000 orders per month, Team up to 20,000, and Business is unlimited. The counter covers a calendar month and starts again at the beginning of the next one. Orders from every source count the same way, so a Shopify store, a WooCommerce store and a CSV import all draw from the same monthly allowance.

If your workspace reaches its order limit, the Owner and Admins see a notice in the app. When this happens regularly, the sensible step is an upgrade, since the limit is based on the plan and not on how long the workspace has existed.

**Saved reports.** Starter can keep 5 saved reports, Team 50, and Business has no limit. A saved report is a report layout you named and stored so that you can open it again with one click. Opening, filtering and exporting a saved report does not change the count. Only the number of stored layouts matters. If you reach the limit, you can delete a report you no longer use or move to a larger plan.

Other limits, such as export size, import file size or API speed, belong to the feature they apply to and are explained in the Reports and Exports, Onboarding and Integrations and API articles.

## API access, SSO and audit log

Three features depend on your plan.

**API access.** The Lumen API is included on Team and Business, and is not included on Starter. A Starter workspace that needs to connect its own tools through the API must upgrade to Team first. The API article explains how keys and limits work.

**SSO (SAML).** Single sign-on through SAML is available only on Business. Team and Starter workspaces sign in with email and password, with optional two-factor authentication. SSO cannot be bought as a separate add-on for lower plans.

**Audit log history.** The audit log records important actions in the workspace, such as role changes and settings changes. Starter does not include an audit log. Team keeps 90 days of history, and Business keeps 1 year. Entries older than the plan allows are no longer shown in the product.

| Feature | Starter | Team | Business |
|---|---|---|---|
| API access | no | yes | yes |
| SSO (SAML) | no | no | yes |
| Audit log history | no | 90 days | 1 year |

When a customer asks "why can't I see the API keys page" or "why is the SSO option missing", check the plan of the workspace first. Security-related background is in the Security and Compliance article.

## Annual billing

Every plan can be paid monthly or annually. With annual billing you **pay for 10 months and get 12**, which is about 17% off the monthly price.

| Plan | 12 months billed monthly | Annual price (10 months) |
|---|---|---|
| Starter | $228 | $190 |
| Team | $708 | $590 |
| Business | $1,788 | $1,490 |

The annual price is charged once, at the start of the term, and the workspace is then covered for 12 months. The billing date is the day the plan starts. How invoices, payment methods and retries work is described in the Billing, Invoices and Payments article.

Annual billing is a good fit for businesses that know they will use Lumen throughout the year. Monthly billing is more flexible, because a monthly plan can be changed at any time (see the next section). Refund rules differ between the two billing periods; see the Refund and Cancellation Policy.

## Changing plans

You can change a monthly plan at any time. The Owner does this in the Billing area of Settings. The two directions work differently:

- **Upgrades are prorated and take effect immediately.** The new features and limits are available straight away. You pay only the difference for the remaining part of the current billing period, so you do not pay twice for the same days.
- **Downgrades take effect at the next renewal.** You keep the features and limits of the higher plan until the current period ends, and the lower plan starts on the next billing date.

### Before you downgrade

A smaller plan has smaller limits, so check these points first:

1. Count the people in the workspace. If there are more than the new plan includes, the number of seats must fit the new plan.
2. Count the saved reports. A plan with a lower limit may hold fewer reports than you have.
3. Check whether you rely on the API or SSO. Both are lost when the new plan does not include them.
4. Compare your monthly order volume with the order limit of the lower plan.

Customers sometimes ask whether they can get money back after downgrading. Plan changes do not create refunds; the Refund and Cancellation Policy is the source for any refund question.

## Free 14-day trial

Every new account can try Team for free for 14 days, and **no card is required** to start. During the trial the workspace has the features and limits of the Team plan described above: 15 seats, up to 20,000 tracked orders per month, 50 saved reports, API access and a 90-day audit log.

A typical trial looks like this:

1. Create a workspace and choose the Team trial during signup.
2. Import a sample of orders or connect a store.
3. Build a few reports and invite colleagues to see how they work in practice.
4. Before the 14 days end, choose the plan that fits and add a payment method, or let the trial finish.

Because no card is collected at the start, nothing is charged automatically when the trial ends. To keep using the workspace, the Owner chooses a plan and adds a payment method. Customers who are unsure should compare the numbers they actually used during the trial with the plan table above.

The trial is offered for Team. If you want to evaluate SSO or the longer audit log of Business, contact Sales through your Account Manager or the sales form on the Lumen website.

## Frequently asked questions

**Are prices per user?** No. Prices are per workspace per month. Each plan includes a number of seats, and extra seats are available on Team and Business for $5 per seat per month.

**Can a Starter workspace add seats?** No. Upgrade to Team instead.

**Is there an unlimited plan?** Business is unlimited for tracked orders and saved reports. Its seats are limited to 50 included seats, and extra seats can be added.

**Do I need a card for the trial?** No. The free trial of Team lasts 14 days and requires no card.

**Can I get a custom price?** Published prices are the ones in this article. Custom terms are available only through a signed contract; see the Enterprise Contracts and Discounts article. Support agents on the first line cannot quote or promise any discount.
