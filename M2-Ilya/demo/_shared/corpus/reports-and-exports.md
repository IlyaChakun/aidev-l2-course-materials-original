---
title: Reports and Exports
section: Product
date: 2026-03-12
---

# Reports and Exports

This article explains how reports work in Lumen, how to export report data, which limits apply to exports, how scheduled email reports behave, and what to do when the Reports page does not load or an export does not start. It is written for customers and for support staff who answer questions about reporting.

## Where to find reports

Open **Reports** in the left menu of the Lumen web app. The Reports page lists every report in your workspace, shows who created it and when it was last opened, and lets you start a new report with the **New report** button in the upper right corner. The mobile app can display reports, but the full report builder is designed for a desktop browser; the browser and screen requirements are described in the system requirements article.

Each report is made of three parts:

- **Source**: the data the report reads, for example tracked orders, order items, or customers.
- **Filters and grouping**: the date range, status, store, and any other conditions, plus the way rows are grouped or summed.
- **Columns and layout**: which fields are shown, in what order, and whether the report is displayed as a table, a bar chart, or a line chart.

Opening a report always shows the data as it is at that moment. Lumen does not keep old snapshots of a report, so the same report opened a week later will include the orders that arrived in between, as long as they match the filters.

The **Export** button is at the top right of an open report, next to the date range selector. If you do not see it, the most common reasons are that the page has not finished loading, that the browser window is very narrow, or that your role does not allow exporting. Who may export is part of workspace roles; see the team and roles guide for details.

## Building a report

A typical report takes a few minutes to build. The steps below produce a table of orders grouped by week.

1. Select **Reports** in the left menu and then **New report**.
2. Choose the source, for example **Orders**.
3. Pick a date range. Presets such as "Last 30 days" and "This quarter" are available, and a custom range can be entered by hand.
4. Add filters. You can combine several filters; all of them must match for a row to be included.
5. Choose the columns. Drag columns to change their order and click a column heading to sort.
6. Under **Group by**, select a field such as **Week** or **Store**. Numeric columns are summed within each group.
7. Click **Save** and give the report a clear name.

Naming reports consistently helps later, because the search box on the Reports page matches report names. Teams that run many reports often use a prefix such as "Finance –" or "Ops –". Since version 4.13.0 reports can also be organized into folders; the release notes describe that change.

### Charts and tables

Every report can be switched between table and chart view with the toggle above the data. The chart view is for reading, not for exporting: an export always contains the underlying table rows, never an image of the chart. To share a chart, take a screenshot or use a scheduled email report, described later in this article.

## Export formats and row limits

Click **Export** at the top right of the report and select a format. The formats available, and the maximum number of rows in a single export, depend on the plan of the workspace.

| Plan | Maximum rows per export | Formats |
|---|---|---|
| Starter | 10,000 | CSV only |
| Team | 100,000 | CSV and XLSX |
| Business | 1,000,000 | CSV and XLSX |

The row limit applies to the rows of the report after filters and grouping are applied, not to the rows of the raw source data. A report grouped by week may therefore export only a few dozen rows even if it summarizes millions of orders. If you only need a total, grouping is usually the best way to stay within the limit.

### CSV and XLSX differences

CSV files are plain text with comma-separated values and a header row. They open in any spreadsheet tool, and they are the better choice for very large exports or for importing into another system. XLSX files keep number and date formatting, column widths, and a frozen header row, which makes them more comfortable for people who read the data directly. XLSX is not available on the Starter plan.

Dates in exports use the ISO format `YYYY-MM-DD`, and date-time values use UTC with a trailing `Z`. Money columns are exported as plain numbers without currency symbols, and the currency is given in a separate column when the report includes one.

```
order_id,created_at,store,status,total,currency
10482,2026-03-02T09:14:00Z,main-shop,paid,84.50,USD
10483,2026-03-02T09:21:00Z,main-shop,shipped,19.00,USD
```

## How exports are generated

Lumen creates exports in one of two ways, and the choice is made automatically.

**Small reports are generated in your browser.** When you click **Export**, the file is built on your computer and downloaded immediately, usually within a few seconds. Nothing is emailed. Because this path depends on the browser, ad blockers, privacy extensions, and strict download settings can interfere with it.

**Large reports are generated by a background job.** When a report contains too many rows to build comfortably in the browser, Lumen shows a message saying that the export has been queued. A background job builds the file on Lumen servers and sends an email to the address of the person who started the export. The email contains a download link, and the link is valid for 24 hours. After that the link expires and the export must be started again.

There is no setting that lets you choose between the two methods, and the exact switch-over point is not shown. What you can control is the size of the report: a narrower date range or an extra filter often turns a queued export into an instant one.

### If the email does not arrive

Background exports usually arrive within a few minutes, and large ones can take longer. If nothing arrives:

1. Wait a few more minutes and check the Spam or Promotions folder.
2. Confirm that the email address on your Lumen profile is correct.
3. Check that the export was started by you; the email goes only to the person who started it.
4. If the 24 hours have passed, start the export again.

If the email still does not arrive, note the report name, the time in UTC, and the workspace name, and contact support.

## Error E-2210 "Export too large"

When a report has more rows than your plan allows, Lumen refuses to create the file and shows the error **E-2210 "Export too large"**. Nothing is wrong with the report or with your account. The message simply means the number of rows is above the limit shown in the table in the section on export formats.

To fix it, make the report smaller:

1. Shorten the date range, for example export one month at a time instead of a full year.
2. Add a filter, such as a single store or a single status.
3. Use **Group by** to summarize rows instead of listing every order.
4. Split the work: run the same report for several date ranges and combine the files in a spreadsheet tool.

A higher row limit is available on a higher plan. Plan details and prices are in the plans and pricing article, and support staff should not quote them from memory.

The count of rows is shown at the bottom of the report as "Showing N rows". Compare that number with the limit before exporting. If the number is just slightly above the limit, tightening the date range by a few days is usually enough.

## Scheduled email reports

A scheduled report sends a saved report to chosen recipients by email on a regular basis, so nobody has to open Lumen and click **Export** each time. Scheduling is available on the **Team** and **Business** plans only. On Starter the scheduling option is not offered.

Available frequencies are **daily**, **weekly**, and **monthly**.

### Creating a schedule

1. Open the saved report from the **Reports** page.
2. Click **Schedule** next to the **Export** button.
3. Choose the frequency: daily, weekly, or monthly.
4. For weekly reports choose the weekday, and for monthly reports choose the day of the month.
5. Choose the time of day and the time zone.
6. Add recipients. Recipients can be workspace members or any other email address.
7. Select the file format and click **Save schedule**.

Scheduled reports follow the same row limits and formats as manual exports for the plan of the workspace. If the report grows beyond the limit, the scheduled email reports the failure instead of attaching a file, and the schedule continues to run on the next date. Narrow the report to fix it.

### Changing or stopping a schedule

Open the report, click **Schedule**, and either edit the settings or choose **Delete schedule**. Deleting a report also removes its schedules. If a workspace moves to the Starter plan, existing schedules stop sending, and they can be reactivated by upgrading again.

Version 4.10.x introduced scheduled reports; the release notes list the versions in more detail.

## The Reports page is blank or Export does nothing

Two related problems are reported often: the Reports page appears completely white, or the **Export** button can be clicked but nothing happens. In almost every case the cause is the browser, not the workspace data. Work through these steps in order.

1. **Hard refresh the page.** Press Ctrl+Shift+R on Windows and Linux, or Cmd+Shift+R on a Mac. This forces the browser to download the current version of the page instead of using a stale cached copy.
2. **Try another browser.** Open the same report in a different supported browser, or in a private window. If it works there, the first browser has a problem with cache, extensions, or settings.
3. **Disable browser extensions.** Ad blockers, privacy tools, script blockers, and download managers are the usual culprits. Turn them off for the Lumen site or test in a private window with extensions disabled.
4. **Report the browser name and version.** If none of the steps help, send support the browser name and exact version, the time in UTC, and the workspace name. A screenshot of the white page, or of the browser console if the customer is comfortable opening it, speeds up the investigation.

Customers sometimes see the related error E-1105 "Report render failed". It is covered in the troubleshooting article, together with how to collect details.

Make sure the browser is one of the supported ones; unsupported or very old browsers can show a white page by design. The list is in the system requirements article.

## Frequently asked questions

**Why does my export have fewer rows than I expected?**
Exports contain the rows of the report as filtered and grouped, not the raw data. Check the date range and the filters at the top of the report.

**Can I export a report to PDF?**
No. Export formats are CSV, and XLSX on plans that include it. For a printable view, use the browser's print function on the report page.

**The export link in my email no longer works.**
Download links from background exports are valid for 24 hours. Start the export again.

**Can a scheduled report go to someone who is not a Lumen user?**
Yes. Recipients can be any email address, so share only with people who are allowed to see the data.

**Is my export affected by time zones?**
Date-time values in files are written in UTC. The date range selector on the page uses the time zone set in your profile.

**Does exporting change my data?**
No. Exports are read-only copies and never modify orders or reports.
