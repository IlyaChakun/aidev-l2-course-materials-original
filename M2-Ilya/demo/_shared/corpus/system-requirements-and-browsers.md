---
title: System Requirements and Supported Browsers
section: Technical
date: 2026-06-23
---

# System Requirements and Supported Browsers

This article lists what a device and a browser need in order to run Lumen properly. It covers supported browsers, the minimum screen width, the browser settings that must be turned on, the network access Lumen needs, and the typical symptoms of an unsupported setup. Use it when a customer reports that pages look broken, that features are missing, or that the report builder does not behave as described in the help center.

## Supported browsers

Lumen supports the **latest two versions** of each of the following desktop browsers:

| Browser | Supported versions |
|---|---|
| Google Chrome | Latest two versions |
| Microsoft Edge | Latest two versions |
| Mozilla Firefox | Latest two versions |
| Apple Safari | Latest two versions |

"Latest two versions" means the current stable release and the one before it. Browsers update themselves every few weeks, so the supported range moves forward over time. A browser that was fine three months ago may now be too old.

**Internet Explorer is not supported**, and neither is any browser older than the latest two versions of the four above. Browsers based on the same engine as Chrome or Edge often work, but they are not tested, and support staff should describe them as "not officially supported" rather than promise that they work.

### What "supported" means

When a browser is supported, Lumen is tested on it for every release, and problems found on it are treated as defects that Lumen Labs will investigate. On an unsupported browser the pages may load, but a problem there will not be treated as a defect. The customer will be asked to switch to a supported browser first.

### How to check the version

Customers who do not know which browser version they use can find it in the browser's own **About** page:

1. **Chrome**: open the menu, choose **Help**, then **About Google Chrome**.
2. **Edge**: open the menu, choose **Help and feedback**, then **About Microsoft Edge**.
3. **Firefox**: open the menu, choose **Help**, then **About Firefox**.
4. **Safari**: open the **Safari** menu and choose **About Safari**.

Opening the About page also makes most browsers check for updates, so the same step often fixes the problem. Ask the customer to restart the browser after an update and to report the version number if the problem remains.

## Screen size

The full **report builder** needs a minimum screen width of **1024 px**. Below that width Lumen switches to a compact layout in which viewing a report works, but the builder controls (column picker, grouping, and filters side panel) are hidden or collapsed.

Common reasons a customer on a large monitor sees the compact layout:

- The browser window is not maximized, or it is snapped to half of the screen.
- The browser zoom level is high. A zoom of 150% on a 1440 px wide display gives an effective width of 960 px, which is below the minimum.
- The operating system display scaling is set high, which has the same effect as zoom.

The fix is to maximize the window and reset zoom to 100% with Ctrl+0 (Windows and Linux) or Cmd+0 (Mac). The browser's developer tools docked on one side of the window also reduce the available width and should be closed.

The mobile app has its own requirements, which are in the mobile app guide, and the full report builder is intended for desktop screens.

## Required browser settings

Two browser settings must be enabled for Lumen to work at all.

### JavaScript

Lumen is a single-page web application. Without **JavaScript** the page stays blank or shows only the page title. JavaScript is on by default in all supported browsers, but some privacy extensions or corporate policies turn it off for specific sites.

### Cookies

**Cookies** must be enabled for the Lumen site. They keep the user signed in and carry the workspace context between pages. If cookies are blocked, the typical symptoms are being sent back to the sign-in page right after signing in, or a message that the session has expired immediately after loading.

To allow cookies for Lumen only, add the Lumen site address to the browser's list of sites that are always allowed to use cookies, instead of turning off cookie protection completely. Blocking only third-party cookies is fine, since Lumen uses its own cookies.

### Other settings worth checking

- **Pop-ups and downloads**: allow downloads from the Lumen site so exports are saved. Some browsers ask for confirmation the first time an export starts.
- **Clock and time zone**: a device clock that is far off can cause sign-in session errors. Turn on automatic time.
- **Private mode**: Lumen works in private windows, but sessions end when the window is closed.

## Network access

Lumen needs a normal internet connection and does not need any software to be installed. Offices with a firewall or a web filter should allow access to the domains below. The domains are shown in the form used in this documentation.

```
app.lumen.example       web application
api.lumen.example       REST API and webhooks
```

If a customer's company network blocks these addresses, typical symptoms are a spinner that never stops, partially loaded pages, or reports that stay empty while the rest of the page loads. Ask the customer to try on a different network, such as a mobile hotspot. If Lumen works there, the company network is the cause and the network administrator should allow the domains.

Lumen does not require a fast connection, but it does need a stable one. Very slow or unstable connections can cause large report pages to load partially or time out.

## Typical symptoms of an unsupported setup

The table lists symptoms that often indicate an unsupported or misconfigured environment, together with the first thing to check.

| Symptom | Likely cause | First check |
|---|---|---|
| Completely white page | Unsupported browser or blocked JavaScript | Browser version and JavaScript setting |
| Sign-in page appears again after signing in | Cookies blocked | Cookie settings for the site |
| Report builder controls are missing | Window narrower than 1024 px | Maximize window, reset zoom |
| Export button does nothing | Extension blocking downloads | Disable extensions, test private window |
| Charts do not draw | Outdated browser or script blocker | Update browser, disable blockers |
| Page layout is shifted or overlapping | Old cached styles | Hard refresh |

A hard refresh means pressing Ctrl+Shift+R on Windows and Linux or Cmd+Shift+R on a Mac. For more detailed steps on pages that are blank or buttons that do not respond, see the reports and exports article, and for error codes shown on the page, see the troubleshooting article.

## Recommended setup for best results

The following habits prevent most browser problems:

1. Keep the browser updated and let it update itself.
2. Use one supported browser as the default for Lumen.
3. Keep extensions to the ones that are actually needed, and add Lumen to the allow list of ad and script blockers.
4. Use a window at least 1024 px wide, and reset zoom to 100% when building reports.
5. Sign in to Lumen from the browser's normal window if working with exports, so downloads are not blocked.

## Company-managed computers

Many customers use Lumen on computers that are managed by their employer. In these environments some settings are locked, and the customer cannot change them without help from an administrator. Typical situations are:

- **Old browser versions pinned by policy.** Some companies delay browser updates for months. If a computer runs a browser older than the latest two versions, Lumen is unsupported there, and the customer needs to ask the administrator to update it or use another device.
- **Extensions installed by the company.** Security and web-filtering extensions can block scripts or downloads. The customer cannot disable them, so ask them to test on a personal device or network to confirm the cause.
- **Cookie and script policies.** A policy may block cookies for all sites except a list. The administrator needs to add the Lumen address to that list.
- **Proxy servers.** A proxy that rewrites or caches web content can break pages. The administrator should exclude the Lumen domains from it.

When a customer says that Lumen works at home but not at the office, the difference is almost always one of the four items above. Do not ask the customer to bypass company rules. Give them a short message they can forward to their administrator, naming the supported browsers, the need for JavaScript and cookies, and the domains in the network section of this article.

## Display and accessibility

Lumen follows the display settings of the browser. Users who rely on larger text can raise the browser zoom, but it should be kept in mind that zoom reduces the effective width of the window, as described in the section on screen size. For a comfortable view of the report builder with larger text, a bigger monitor or a lower display scaling is the better choice.

Keyboard navigation is available on all pages: Tab moves between controls, Enter activates buttons, and Esc closes dialogs. Screen readers can read page titles, buttons, and table headings. If a customer finds a control that cannot be reached with the keyboard, collect the page name, the browser and version, and the screen reader name, and escalate as a defect.

## Checklist before reporting a problem

Before a ticket is passed on, confirm that the following has been checked. This avoids sending cases that are only caused by the environment.

| Check | Done when |
|---|---|
| Browser is supported | It is one of the latest two versions of Chrome, Edge, Firefox, or Safari |
| JavaScript and cookies on | Pages load and the user stays signed in |
| Window width | At least 1024 px at 100% zoom |
| Network | Works on another network, or the domains are allowed |
| Extensions | Problem remains in a private window |
| Hard refresh | Done with Ctrl+Shift+R or Cmd+Shift+R |

If every check passes and the problem persists, collect the browser name and version, the time in UTC, the workspace name, a screenshot, and any error code, as described in the troubleshooting article.

## Frequently asked questions

**Can I use Lumen in Internet Explorer?**
No. Internet Explorer is not supported. Use the latest two versions of Chrome, Edge, Firefox, or Safari.

**Is there a minimum screen size?**
The full report builder needs a width of at least 1024 px.

**Do I need to install anything?**
No. Lumen runs in the browser. JavaScript and cookies must be enabled.

**My browser is one version older than the latest two. Will Lumen still work?**
It might, but it is not supported. Update the browser before reporting a problem.

**Do I need to enable anything for Safari on a Mac?**
No special setting is needed beyond JavaScript and cookies. Check that cross-site tracking prevention is not blocking the Lumen site from keeping a session.
