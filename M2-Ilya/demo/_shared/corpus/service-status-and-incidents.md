---
title: Service Status and Incidents
section: Policy
date: 2026-03-09
---

# Service Status and Incidents

This document explains how Lumen Labs communicates about outages and degraded service, how incidents are classified by severity, and what the uptime commitments are for each plan. It is written for support staff who answer customers during an incident and for customers who want to understand what the status page is telling them.

## The Lumen status page

The public status page lives at `https://status.lumen.example`. It is the single official source of truth about the health of the Lumen web app, the mobile apps, the public API and webhook delivery. Anyone can open it without signing in, and it works even when the Lumen app itself is unavailable, because it is hosted separately from the production platform.

The page shows three things:

- **Current status** for each component (Web app, Mobile apps, API, Webhooks, Report exports, Email notifications), shown as Operational, Degraded performance, Partial outage or Major outage.
- **Active incidents**, each with a title, a severity label, a start time in UTC and a chronological list of updates.
- **Past incidents**, kept as a searchable history so that customers can see what happened and when it was resolved.

Customers can subscribe to the status page by email, so that they receive every new incident and every update without having to reload the page. Workspace Owners and Admins are encouraged to subscribe with a shared mailbox rather than a personal address, so that the information is not lost when someone changes roles.

All times on the status page are in UTC. When a customer asks "was it down at 9 am yesterday?", the first step is to convert their local time to UTC and compare it with the incident history, rather than answering from memory.

### What the status page does not show

The status page describes problems that affect many customers or a whole component. It does not show problems that affect a single workspace for reasons that are specific to that workspace, such as a blocked invitation, a rejected card or a browser extension that breaks the report view. Those cases are handled through normal troubleshooting, so a green status page does not mean that the customer is wrong. Staff should never tell a customer "there is no problem" only because the page is green; the correct wording is that no platform-wide incident is currently listed and that the team will continue to investigate the individual case.

## Severity levels

Every incident is given one of three severity levels. The level decides who is paged, how quickly customers are updated and how support tickets about the incident are handled.

| Severity | Definition | Typical examples |
|---|---|---|
| **SEV1** | The entire workspace or all users are blocked | HTTP 503 for everyone, sign-in impossible for everyone |
| **SEV2** | A major feature is down for many users | Report exports failing for many workspaces, webhooks not delivered |
| **SEV3** | Limited impact | A cosmetic defect, a slow page for a small group, one integration delayed |

The decisive question is how many people are blocked and how completely. One customer who cannot sign in is a normal account problem. Every customer who cannot sign in is a SEV1 incident.

### Choosing between SEV2 and SEV3

When it is unclear whether an incident is SEV2 or SEV3, engineers consider whether a customer can still finish their daily work with a reasonable workaround. If the main function is unusable and no workaround exists, the incident is SEV2. If the function works but slowly, intermittently, or only for a small group, it is SEV3. The severity can be raised or lowered as more information arrives, and each change is recorded in the incident timeline.

Support staff do not set the severity themselves. They report what customers are experiencing, and the on-call engineer or incident manager assigns the level.

## How SEV1 incidents are handled

A SEV1 incident is always escalated immediately to the on-call engineer, and the related tickets get priority urgent. There is no waiting period and no attempt to troubleshoot first. If a first-line operator sees several tickets in a short time that describe the same total outage, the operator escalates the first one and links the others to it.

During a SEV1 incident, customers are updated on the status page every 30 minutes. An update is published even when there is nothing new to report; in that case it says that the team is still working on the problem and gives the time of the next update. This steady rhythm is intentional, because silence is the thing customers find most frustrating during an outage.

### Roles during an incident

| Role | Responsibility |
|---|---|
| On-call engineer | Diagnoses the problem and applies the fix or workaround |
| Incident manager | Coordinates people, decides severity changes, owns the timeline |
| Communications owner | Writes and publishes the status page updates |
| Support Lead | Keeps the support queue consistent and informs the first line |

First-line operators do not need to know the technical cause. They need to know the status, the time of the next update and the wording that is approved for customers.

## What support staff say during an incident

The approved wording is short and factual. The customer is pointed to the status page, told that the team is working on it, and told that updates appear there. Support staff must not guess the cause, promise a resolution time, or speculate about data loss.

A suitable reply looks like this:

```text
Hello, thank you for letting us know. We are currently seeing an incident
that affects access to Lumen, and our engineers are working on it. You can
follow every update at https://status.lumen.example. We will not repeat the
details here so that you always see the latest information. 
```

Things that must not be said:

- "It will be fixed in an hour." No resolution time may be promised unless it is on the status page.
- "Your data is safe" or "your data is lost." Statements about data are made only by the incident manager.
- "You will receive compensation." Service credits are not decided by the first line (see the next section).

### Tickets created during an incident

Tickets that arrive during an incident keep their normal handling, but the operator adds a short internal note with the incident title from the status page. After the incident is closed, the Support Lead decides whether customers who wrote in receive a follow-up message. The first line does not send follow-ups on its own initiative.

## Uptime commitments and service credits

Lumen Labs commits to the following monthly availability levels, depending on the plan.

| Plan | Uptime commitment |
|---|---|
| Business | 99.9% |
| Team | 99.5% |
| Starter | Best effort, no commitment |

Starter workspaces use the same platform and benefit from the same engineering work, but there is no contractual availability level for them.

### Service credits

If a workspace on a plan with an uptime commitment believes the commitment was missed, the case goes to the Billing team. The Billing team alone decides whether a service credit applies and how it is applied to the account. First-line staff must not confirm that a credit is owed, must not estimate its size, and must not say that the commitment was or was not missed. The correct reply acknowledges the question, explains that the Billing team reviews such requests, and says that the ticket has been passed on. The operator collects the workspace name, the date and time range in UTC in which the customer saw the problem, and the incident title if the customer mentions one.

### What counts toward uptime

Planned maintenance that has been announced on the status page in advance is not treated as downtime. Problems caused by the customer's own network, browser, or third-party services such as a store connection that is down on the store's side are also not part of the platform's availability. When a customer's experience may fall into one of these groups, the operator does not decide this; the Billing team reviews the evidence together with the engineering incident record.

## After the incident: resolution and review

When an incident is resolved, the status page shows a final update marked Resolved with the time of resolution in UTC. For SEV1 and SEV2 incidents, engineering also writes a short post-incident summary on the status page that describes what happened, the period affected, and what is being changed to prevent a repeat.

### Internal review

The review looks at detection, response, communication and prevention. The Support Lead attends and brings the support view: how many tickets arrived, whether customers received consistent wording, and whether any ticket was handled outside the approved wording. Findings that concern the first line are turned into updates to this document or to the reply style guide.

### Common questions

**Is there a way to be notified before maintenance?** Planned maintenance appears on the status page ahead of time, and subscribers receive the announcement by email.

**The status page is green, but I get an error.** This usually means the problem is specific to the workspace, the browser or the network. Follow the normal troubleshooting steps and collect the browser and version, the time in UTC, the workspace name, a screenshot and the error code.

**Can the first line decide that something is an incident?** No. Operators report symptoms and escalate. Only the on-call engineer or the incident manager declares an incident and assigns its severity.

**Where can a customer see past incidents?** On the status page, in the incident history, which shows the start time, the severity label and every update.
