---
title: Release Notes and Known Issues
section: Technical
date: 2026-09-30
---

# Release Notes and Known Issues

This article summarizes the Lumen web and mobile app releases in the 4.10.x to 4.13.x range and lists the known issues that customers have encountered, with the version in which each was fixed. Support staff should use it to check whether a reported problem matches a known defect, and to tell customers which version to update to. The web app and the mobile apps share version numbers, so "version 4.12.2" means the same release on every platform.

## How versions work

Lumen uses a three-part version number in the form **major.minor.patch**, for example 4.12.2.

- A change in the **minor** number (4.11 to 4.12) usually brings new features and larger changes.
- A change in the **patch** number (4.12.1 to 4.12.2) contains bug fixes only.
- Web releases roll out to every workspace at the same time and do not need any action, apart from a page reload. Mobile releases arrive through the app store and may reach different users on different days, depending on their store settings.

### How to find your version

1. **In the web app**: click your profile picture in the lower left corner and choose **About Lumen**. The version is shown at the top.
2. **In the mobile app**: open **Settings → About**. The version and build number are displayed there.

When a customer reports a problem, always ask for the version number. Whether a problem is known and already fixed depends on it.

### How to update

On the web, a hard refresh loads the newest version: Ctrl+Shift+R on Windows and Linux, or Cmd+Shift+R on a Mac. On mobile, open the official app store, search for Lumen, and choose **Update**. Apps should be installed from the official stores only. If the store does not show an update yet, the release may not have reached that region, and the customer can try again later the same day.

## Version summary

| Version range | Main change | Known issue |
|---|---|---|
| 4.10.x | Scheduled email reports added | None recorded |
| 4.11.0 – 4.11.2 | Interface and performance improvements | Android notification delays |
| 4.11.3 | Fix for Android notification delays | None recorded |
| 4.12.0 | Faster report loading | Opening a report could crash the app |
| 4.12.1 | Small interface fixes | Crash on opening a report still present |
| 4.12.2 | Fix for the report crash | None recorded |
| 4.13.0 | Saved-report folders | None recorded |

## Release 4.10.x: scheduled reports

The 4.10.x series introduced **scheduled reports**. A saved report can be sent by email to chosen recipients on a daily, weekly, or monthly basis, so that regular figures reach the people who need them without anyone having to open the app. The feature is controlled by plan, and the details of how to create and change schedules are in the reports and exports article.

Along with scheduling, 4.10.x brought several smaller improvements:

- A **Schedule** button next to the **Export** button of a saved report.
- Clearer messages when an export is queued as a background job.
- Improvements to the loading time of the Reports page for workspaces with many reports.

No known defects are recorded against 4.10.x. If a customer on this version reports a problem with scheduled emails, treat it as a normal troubleshooting case and use the documented steps first, then escalate with the usual details.

## Release 4.11.x: Android notification delays

Version **4.11.0** brought interface refreshes and general performance work. Unfortunately it also introduced a problem in the Android app: after a change in the way the app registers for push messages, notifications on some Android phones were delayed.

### Known issue: Android notification delays, 4.11.0 to 4.11.2

- **Affected versions:** Android app 4.11.0, 4.11.1, and 4.11.2.
- **Symptom:** push notifications arrive long after the event, in some cases after the customer has already seen the change in the app.
- **Fixed in:** **4.11.3**.
- **Action:** ask the customer to update the Android app to 4.11.3 or later from the official store.

If the customer is already on 4.11.3 or newer and still sees delays, the release problem is not the cause. In that case the usual reasons are phone settings that limit background activity, and the steps to follow are in the notifications and alerts article. Note that iOS devices were not affected by this defect.

### What the fix changed

Version 4.11.3 restored the previous way of registering the device for push messages. No action was needed from users apart from the update. Notifications that were delayed during the affected period are not re-sent, because they were eventually delivered.

## Release 4.12.x: report crash

Version **4.12.0** improved how quickly large reports open. It also contained a defect that could make the app crash when a report was opened.

### Known issue: opening a report could crash the app, 4.12.0

- **Affected version:** 4.12.0.
- **Symptom:** the app closes, or the web page goes blank, at the moment a report is opened. The problem was most visible with reports that use grouping.
- **Log line:** support staff may see the following entry in diagnostic logs attached to a ticket.

```
ERROR ReportView: unhandled exception on open
```

- **Fixed in:** **4.12.2**. Version 4.12.1 was a smaller interface release and still contained the problem.
- **Workaround:** update the app to the latest version. On the web, do a hard refresh (Ctrl+Shift+R or Cmd+Shift+R) so the newest version loads. After the update the report opens normally.

The crash does not damage or delete reports, and no data is lost. If the customer opens the same report on a fixed version, it appears as it was before.

### Related symptoms that are not this issue

A blank Reports page on a version other than 4.12.0 is not this defect. It is usually caused by the browser, and the steps are in the troubleshooting article. Similarly, the error E-1105 is a different problem from the crash described here.

### Support guidance

1. Ask for the version number.
2. If the version is 4.12.0, tell the customer it is a known issue that is fixed in 4.12.2, and ask them to update.
3. If the version is 4.12.1 or 4.12.2 or newer and the crash continues, collect the details listed in the troubleshooting article and escalate.
4. Do not promise a date for any future fix. Describe only what is documented here.

## Release 4.13.x: saved-report folders

Version **4.13.0** adds **saved-report folders**. Folders let a workspace group its saved reports, for example by team, by store, or by month, instead of keeping a single flat list on the Reports page.

### Using folders

1. Open **Reports** in the left menu.
2. Click **New folder** and enter a name.
3. Drag saved reports into the folder, or open a report and choose **Move to folder**.
4. Click the folder name to see only its reports.

Folders are a way of organizing; they do not change who can see a report, and they do not change the way exports or schedules work. Deleting a folder moves its reports back to the main list and never deletes the reports.

Folders can contain only reports, not other folders. There are no known issues recorded against 4.13.x at the time of writing.

## Using this article with a ticket

Customers rarely say "I am on version 4.12.0". They describe what they see, and support has to connect the description to a version. The table below maps common descriptions to the entries in this article.

| What the customer says | Check | Likely entry |
|---|---|---|
| "The app closes when I open a report" | Version number | 4.12.0 crash |
| "Push messages come very late on my Android phone" | App version | 4.11.0 – 4.11.2 delays |
| "I cannot find a way to send a report by email on a schedule" | Plan and version | 4.10.x scheduled reports |
| "I want to group my reports" | Version | 4.13.0 folders |
| "The Reports page is white" | Browser, not version | Troubleshooting article |

If the description does not match any entry, do not assume it is a new known issue. Handle it with the normal troubleshooting steps and escalate when they do not help.

### What to include when a defect is suspected

When a customer is on a fixed version and the problem still occurs, a new defect may have been found. The escalation should contain the app or web version, the platform and operating system version, the time in UTC, the workspace name, a screenshot, and, if available, the log line shown in the diagnostic information. A short factual sentence describing the symptom is enough; there is no need for a theory about the cause.

## How changes are announced

Feature releases are described in this article and in the in-app **What's new** panel that appears after an update. Patch releases that only fix defects usually appear only in the version summary. Lumen does not announce dates of future releases, and support staff must not guess when a feature or a fix will arrive. If a customer asks about a feature that is not in these notes, the answer is that it is not currently documented, and the question can be passed on as a feature request.

Known issues are removed from the "active" list when the fixed version has been available for some time, but they stay in this article so the history remains searchable.

## Frequently asked questions

**A customer's app crashes when opening a report. What should I check first?**
The version number. If it is 4.12.0, the crash is a known issue fixed in 4.12.2.

**Notifications on Android are very late. Is that the known issue?**
It is when the app version is between 4.11.0 and 4.11.2. The fix is in 4.11.3. On newer versions, look at the phone's settings, as described in the notifications article.

**When were scheduled reports added?**
In the 4.10.x releases.

**Where are saved-report folders?**
They arrived in 4.13.0 and appear on the Reports page.

**Do customers need to do anything for web updates?**
Only reload the page. A hard refresh makes sure the latest version is used.

**Will older versions keep working?**
Older mobile versions may continue to run, but problems on them will be handled by asking the customer to update first.
