---
title: Troubleshooting and Error Codes
section: Technical
date: 2026-05-19
---

# Troubleshooting and Error Codes

This article is the general troubleshooting guide for Lumen. It explains how to approach a problem step by step, describes the error codes and HTTP errors that are not covered in a dedicated article, and lists exactly what information to collect before passing a case to another team. Payment errors, sign-in lockouts, report export limits, and webhook failures each have their own articles, which are referred to below.

## A general approach to troubleshooting

Most problems that customers report fall into a small number of groups. Working in the same order every time keeps answers consistent and avoids guesswork.

1. **Read the exact error.** Ask for the error code (for example E-1105) or the HTTP status (for example 500 or 503) and the text around it. A code is far more useful than a description such as "it is broken".
2. **Decide who is affected.** One user, several users of one workspace, or everyone? A problem that affects a single person on a single device is almost always local to the browser or the device. A problem that affects the whole workspace may be a service incident.
3. **Check when it started.** A problem that started after a browser update, a new extension, or a new app version points to the client side. A problem that started suddenly for many people points to the service side.
4. **Try the documented steps.** Use only steps that appear in the help articles. If the steps do not fix the problem, or the case is not covered, collect the details and escalate.
5. **Confirm the result.** Ask the customer to confirm that the problem is gone before closing the conversation.

### What not to ask for

Never ask a customer for a password, a one-time code, an API key, or a full card number. Screenshots must not show any of these either. If a customer posts one by mistake, ask them to remove it where possible and to change the password or key. When payment details must be identified, use only the payment reference and the last four digits of the card, as described in the billing articles.

## Information to collect

When a problem needs a second look, a good ticket saves a day of back-and-forth. Collect the following five items every time.

| Item | Why it matters | Example |
|---|---|---|
| Browser and version | Many page problems depend on the browser | Firefox 128.0 on Windows 11 |
| Time of the problem, in UTC | Allows engineers to find the matching log entries | 2026-05-18 14:32 UTC |
| Workspace name | Identifies the account and region | Northwind Traders |
| Screenshot | Shows the exact message and page state | Image of the full browser window |
| Error code | Points directly to the cause | E-1105 |

Customers usually do not know their time in UTC. Ask for their local time and time zone and convert it, or ask them to reproduce the problem and tell you the exact minute. For mobile problems, replace the browser with the app version, which is shown in the app under **Settings → About**, and the operating system version.

A short, useful note for a handoff looks like this:

```
Customer: workspace "Northwind Traders"
Problem: Report page shows E-1105 when opening "Weekly orders"
Browser: Chrome 126.0.6478 on macOS 14.5
Time: 2026-05-18 14:32 UTC
Steps tried: hard refresh, private window (still fails)
Attachment: screenshot_1.png
```

## E-1105 "Report render failed"

The error **E-1105 "Report render failed"** appears when the browser cannot draw a report. The report data itself is normally fine; the failure happens while the page builds the table or chart. The most common causes are an old cached copy of the page and browser extensions that block or change scripts.

Ask the customer to go through these steps in order:

1. Reload the page with a hard refresh: Ctrl+Shift+R on Windows and Linux, or Cmd+Shift+R on a Mac.
2. Clear the browser cache for the Lumen site, then reload.
3. Open the report in a private or incognito window, where extensions are normally disabled. If it works there, an extension is the cause.
4. Disable extensions one by one, starting with ad blockers, privacy tools, and script blockers, to find the one that interferes.
5. Try another supported browser.

If the error is still there after all five steps, collect the five items from the table above, including the report name, and escalate to the technical queue. Do not suggest that the customer delete or recreate the report, because this does not fix a rendering problem and could cause loss of work.

E-1105 is related to the blank-page problem on the Reports page, which is described in the reports and exports article, together with the export-specific error E-2210.

## Sign-in problems and E-3001

The error **E-3001** means that sign-in is temporarily locked. This article does not repeat the details. The conditions that cause the lock, how long it lasts, and what the first line may do are described in the account and login article. When a customer reports E-3001, read that article instead of trying other troubleshooting steps, since browser fixes will not help.

A sign-in problem without E-3001, for example a "wrong password" message, is a login help case and is also covered in the account and login article. It is not a technical fault.

## HTTP 500 and HTTP 503

HTTP errors are shown by the browser or by the Lumen page when the server could not complete a request. The two most common are 500 and 503, and they require different responses.

### HTTP 500 on any page

An HTTP **500** is a transient server error. It can appear on any page and usually disappears on its own. The recommended response:

1. Wait **10 minutes**.
2. Reload the page and repeat the action.
3. If the error is still there, try once more in a private window, then collect the five items and escalate.

A 500 on the payment page is a special case with its own rule about retrying, and it is described in the payment errors reference. Do not apply the general advice there.

### HTTP 503 for a whole workspace

An HTTP **503** that affects a whole workspace, meaning every user sees it, is a possible incident rather than a local problem. Do not ask the customer to clear the cache or switch browsers. Instead:

1. Check the status page for an active incident.
2. Ask one or two other users in the same workspace whether they see the same error.
3. If several or all users are affected, treat it as a possible major incident and escalate immediately with the workspace name, the time in UTC, and the number of affected users.

How incidents are classified, escalated, and communicated is described in the service status and incidents article. A 503 that affects only one person is treated like a 500.

## Quick reference of error codes

The table lists the codes handled in this article and where the full description lives. Codes that are not listed are described in their own articles, and an unknown code should be escalated with the five collected items.

| Code or status | Meaning | What to do | Details |
|---|---|---|---|
| E-1105 | Report render failed | Browser cache and extensions steps | This article |
| E-2210 | Export too large | Make the report smaller | Reports and exports |
| E-3001 | Sign-in locked | Follow the login guide | Account and login |
| E-4xxx | Payment errors | Do not retry repeatedly | Payment errors reference |
| E-5003 | Webhook delivery failed | Check URL and response codes | Integrations and API |
| HTTP 429 | Too many API requests | Wait for Retry-After | Integrations and API |
| HTTP 500 | Transient server error | Wait 10 minutes and retry | This article |
| HTTP 503 | Service unavailable | Check the status page | This article |

## Problems that are not on the list

Not every problem has a documented fix. If the issue does not match a code in the table, does not appear in the help articles, and cannot be solved with the general approach, do not invent a solution and do not promise a fix or a date. Tell the customer that the case is being passed to a team that can investigate, state that you have collected the details, and escalate with one short factual sentence describing the problem. The escalation policy describes the correct priority.

## Intermittent problems

Some problems come and go, which makes them harder to describe. A page that loads on one attempt and fails on the next, or an export that works in the morning and not in the afternoon, needs a few extra questions before anything else is tried.

1. **How often does it happen?** Every time, once a day, or only now and then.
2. **Does it depend on a place or a device?** Ask whether the same action works on another computer, another network, or on the mobile app.
3. **Does it depend on a certain report or order?** If only one report fails, the problem may be connected with that report's filters; if every report fails, the browser is the likelier cause.
4. **What changed recently?** A new extension, a browser update, a new office network, or a new app version.

Record the answers in the ticket. An engineer reading the ticket later can then see the pattern without asking the same questions again. Ask the customer to note the exact time the next failure happens, and to give it in the local time zone with the zone name, so it can be converted to UTC.

### Cache and cookies

When the cause is unclear and the problem affects one browser only, clearing cached files for the Lumen site is a safe step. Clearing cookies signs the user out, so tell the customer in advance and make sure they know their sign-in details. Never ask the customer to tell you their password in order to test a sign-in.

## Writing the reply

A good troubleshooting reply is short and gives the customer one clear next step. It follows the reply style guide: greeting, direct answer, next step, and the name of the help article used.

- State what is likely happening in one sentence, without blaming the customer.
- Give the steps as a numbered list, no more than five at a time.
- Say exactly what information you need if the steps do not work.
- Avoid promising when a problem will be fixed, and avoid describing internal tools.

For example, for E-1105: "Thank you for the details. This error is usually caused by an old cached copy of the page or a browser extension. Please press Cmd+Shift+R to refresh, then try opening the report in a private window. If it still fails, please send the browser name and version, the time in UTC, and a screenshot. Help article: Troubleshooting and Error Codes."

## Frequently asked questions

**A customer sends only a screenshot with no text. What now?**
Read the error code in the screenshot, then ask for the missing items: browser and version, time in UTC, and workspace name.

**The customer says the problem started after an app update.**
Check the release notes for known issues in that version before asking the customer to try anything else.

**The error went away by itself. Should the ticket be closed?**
Reply that the problem appears resolved, ask the customer to write again if it returns, and mention the time in UTC for future reference.

**May I ask the customer to share their screen?**
Support works through written messages. Ask for screenshots and a short list of the steps the customer took instead.
