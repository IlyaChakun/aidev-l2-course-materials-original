---
title: Support Hours and SLA
section: Policy
date: 2026-04-14
---

# Support Hours and SLA

This document describes how customers can reach Lumen Support, when the support team is available, and how quickly customers can expect a first response. It also explains how business hours are counted and what happens to tickets that arrive outside those hours.

## Support channels

Lumen Support is available through two channels only: **chat** and **email**. Both channels feed into the same ticket system, so a conversation that starts in one channel can continue in the other without the customer having to repeat information.

### Chat

Chat is available from inside the Lumen web app and the mobile apps. A customer who is signed in is identified automatically, which means the support team can see the workspace name, the plan and the app version without asking. Chat works best for short questions where the customer wants guidance while looking at the screen, for example "where do I find this setting?"

When no agent is available, the chat window offers to create a ticket. The message the customer has already typed is kept as the first message of that ticket, so nothing is lost.

### Email

Customers can write to the support address shown in the Help menu of the app. Every email creates a ticket and the customer receives an automatic confirmation containing the ticket number. Email is the better choice for longer problems, for cases where screenshots or log files must be attached, and for anything that needs to be discussed with colleagues.

### Channels that do not exist

Support is handled only through chat and email. Customers who ask for another channel should be told politely that chat and email are the available ways to reach the team, and that a ticket created through either one receives the same treatment. Staff must not promise that a new channel is being introduced, because no such plan has been announced.

## Business hours

The support team works **Monday to Friday, 08:00 to 18:00 UTC**. All targets in this document are measured against this window. The team does not work on weekends, and staff members are not expected to answer tickets outside the window.

The hours are the same for every plan; only the speed of the first response differs. A customer in another time zone should convert the hours to their local time. For example, 08:00 UTC is 09:00 in Berlin during winter and 04:00 in New York during summer time, and 18:00 UTC is 19:00 in Berlin and 14:00 in New York respectively. Because daylight saving time changes the local hours twice a year, the UTC definition is always the one that counts.

### Public holidays

Lumen Labs does not close for national public holidays in a single country. If the schedule of the team changes for a particular day, the change is announced in the Help menu of the app at least one week in advance. Operators should not tell a customer that the team is closed on a holiday unless such an announcement exists.

### What happens outside business hours

A ticket that arrives outside business hours is accepted and receives an automatic confirmation. The first-response clock starts when the next business day begins, not when the ticket arrived. A message sent on Friday at 19:00 UTC therefore starts counting at 08:00 UTC on Monday.

The only exception is a platform-wide outage; see the section on incidents below.

## First response targets

A first response is a reply written by a human or by the first-line operator that addresses the customer's question or tells the customer what happens next. The automatic confirmation does not count.

| Plan | First response target (business hours) |
|---|---|
| Starter | 48 hours |
| Team | 24 hours |
| Business | 4 hours |

The targets are counted in business hours, so only time inside the Monday to Friday window counts. A Starter ticket received on Friday at 16:00 UTC, for example, has used two hours of its target by the end of that day. The remaining hours continue on Monday morning.

### What a target is and is not

A first response target is the time within which the team replies for the first time. It is not the time within which the problem is solved. Some problems are solved in a single message; others need several exchanges, an investigation or the involvement of another team. Staff must not tell customers that their problem will be resolved within the response target.

### How the target is measured

The clock starts when the ticket is created and stops when the first reply is sent to the customer. The clock pauses while the ticket waits for information that only the customer can provide. When the customer answers, the clock does not restart the first response; it only matters for later replies in the same conversation, which are handled in order of arrival.

## Priority queue for Business

Workspaces on the Business plan have a **priority queue**. This means their tickets are placed ahead of tickets from other plans when the team picks up the next conversation. The priority queue does not change the support hours, and it does not let Business customers reach additional channels.

### How the queue is ordered

Within the queue, tickets are ordered by two rules, applied in this sequence:

1. Tickets with ticket priority urgent come first, whatever the plan.
2. Business tickets come before tickets from other plans that have the same priority.

Inside each group, the oldest ticket is handled first. An urgent ticket from a Starter workspace is therefore handled before a low-priority ticket from a Business workspace. The meaning of each priority level is defined in the escalation and routing policy.

### Telling customers about the queue

Staff may tell a Business customer that their plan includes priority handling and the response target that applies to the plan. Staff must not give a customer on another plan the impression that a faster target can be arranged by paying for a single ticket, because no such service exists. A customer who wants faster response times can be pointed to the plans overview.

## Incidents and 24/7 on-call

Outages are not subject to the Monday to Friday window. **SEV1 incidents are handled 24/7 by the on-call engineer**, including nights, weekends and holidays. The definition of SEV1, the way customers are informed and the status page are covered in the service status and incidents document.

For first-line operators this means one thing: when a ticket describes a possible SEV1 situation, it is escalated at once, even when the ticket arrives outside business hours. The ticket system routes such escalations to the on-call engineer directly. The ordinary first-response target is not used as a reason to wait until the next business day.

### What is not on-call

On-call coverage is for platform-wide incidents only. Questions about billing, privacy requests, how-to questions and single-user problems wait for the next business day and are answered according to the targets above. If a customer writes at the weekend that their report export is slow, the ticket is answered on Monday.

## Setting expectations in replies

Good replies about timing are specific and modest. The operator names the channel, the working window and the target for the customer's plan, and adds the ticket number so that the customer can refer to it later. The operator does not give a precise clock time for the reply.

Example of an acceptable closing sentence for a Team customer:

```text
Your ticket number is shown in the confirmation email. Our team replies
within the first response target of your plan during business hours,
Monday to Friday, 08:00 to 18:00 UTC.
```

### Frequently asked questions

**Which ways are there to contact support?** Chat and email only. Both lead to the same team.

**Does the response target include weekends?** No. Weekends are not counted in business hours.

**I wrote an hour ago and have no reply. Is something wrong?** Not necessarily. Compare the time since the ticket was created with the target for the plan, counting only business hours. If the target has already passed, the operator escalates the ticket to the Support Lead and informs the customer that the matter has been passed on.

**Does a reply to my reply restart the target?** No. The first response target applies only to the first reply on a ticket.

**Is the chat available outside business hours?** The chat window stays open so that customers can leave a message. A human reply follows within the targets above.

### Revision of targets

Targets are reviewed by the Support Lead. When a target changes, the change is published in the Help center and in this document before it applies to customers. Staff use the published value, never a value remembered from an earlier version.
