---
title: Getting Started with Lumen
section: Product
date: 2026-05-18
---

# Getting Started with Lumen

Lumen is a cloud web and mobile application that small businesses use to track orders and build reports. This guide walks a new customer through the first hour: creating a workspace, choosing a data region, bringing in orders, connecting a store, building a first report, and inviting colleagues. Each step is short, and you can stop after any of them and continue later; Lumen saves your progress in the workspace.

## What you need before you start

Gather a few things before you create the workspace. None of them is difficult, but having them ready makes the setup smoother.

- **A work email address** that you can open right now. Lumen sends a confirmation message to it, and this address becomes the sign-in name of your account.
- **A name for the workspace.** Most customers use the company name or the shop name. The name is shown at the top of the left menu and in notifications, and the Owner can change it later.
- **A decision about the data region.** You choose it once, during signup. The next section explains why this decision matters.
- **Your order data.** This can be a CSV file exported from your existing tool, or a store that you can connect directly. If you do not have order data yet, you can still create the workspace and look around, but reports will be empty.
- **A modern browser.** The supported browsers are listed in the system requirements guide.

It also helps to know who else should have access. You can invite colleagues after the first report is ready, so there is no need to decide this at the beginning. The person who creates the workspace becomes its Owner, and a workspace always has exactly one Owner. Roles and invitations are explained in the team and roles guide.

If you are evaluating Lumen, the plans and pricing document explains what a trial includes and how plans differ. This guide does not repeat those details.

## Step 1: Create your workspace

A workspace is the shared space where your orders, reports and team live. One company normally uses one workspace.

1. Open the Lumen sign-up page and enter your work email address and a password.
2. Open the confirmation email and select the link inside. If you cannot find it, check your Spam folder.
3. Enter the name of your workspace.
4. Choose your **data region** (see the next section).
5. Select **Create workspace**.

After this you arrive at the home screen of your new workspace. A short checklist on the home screen shows the remaining steps: import orders, connect a store, and build a first report. The checklist disappears once you have completed the steps, and you can hide it earlier if you wish.

If you already have a Lumen account because a colleague invited you, you do not create a workspace. You accept the invitation, and the workspace of your colleague opens. If you want to start a separate workspace, sign out of the invitation flow and register with the sign-up page; one account can belong to several workspaces.

Choose a password that you do not use anywhere else. Details on password handling, resets, and two-factor authentication are in the account and login guide. We recommend that the Owner switches on two-factor authentication right after creating the workspace.

## Step 2: Choose a data region

During signup Lumen asks where your workspace data should be stored. You can pick the **EU** or the **US** region.

| Region | Typical choice for |
|---|---|
| EU | Businesses that serve customers mainly in Europe, or that prefer to keep data in Europe |
| US | Businesses that serve customers mainly in North America, or that have no particular preference |

Two points are important.

1. The region is chosen at signup, and it **cannot be changed later**. If you pick the wrong region, the way forward is to create a new workspace in the correct region and import your orders there again. Nobody at Lumen Labs can move an existing workspace for you.
2. The choice affects where your data is stored, not who can use the product. People from any country can be invited to a workspace in either region.

If you are not sure which region to choose, think about the regulations that apply to your customers' data and about the location of your accountant or legal advisor, and ask them before you sign up. For the technical and legal details of how the regions work, see the security and compliance guide; support staff cannot give legal advice about which region you should choose.

If a customer asks for a region change after signup, the operator explains that it is not possible, mentions the option of a new workspace, and does not promise a migration.

## Step 3: Import your orders from CSV

The quickest way to see your own data in Lumen is to import a CSV file.

1. In the left menu, open **Orders**.
2. Select **Import** in the top-right corner.
3. Choose your CSV file, or drag it into the window.
4. Match the columns of your file to the Lumen fields on the mapping screen.
5. Review the preview of the first rows and select **Start import**.

The **maximum size of one CSV file is 5 MB**. If your file is larger, split it into several files, for example by month, and import them one after another. Splitting is safe: orders that appear in more than one file are matched by their order number and are not duplicated.

A file that imports well has a header row and one order per line. A minimal example:

```csv
order_id,order_date,customer_email,total,currency,status
10001,2026-04-01,anna@example.com,49.90,USD,paid
10002,2026-04-01,ben@example.com,120.00,USD,shipped
10003,2026-04-02,carla@example.com,18.50,USD,refunded
```

Tips for a clean import:

- Save the file as CSV with UTF-8 encoding. Spreadsheet programs sometimes offer several CSV variants; choose the UTF-8 one.
- Keep dates in the same format throughout the file, ideally `YYYY-MM-DD`.
- Do not merge cells or add summary rows at the bottom; each line must be an order.
- Use a dot or a comma consistently as the decimal separator, and tell Lumen which one on the mapping screen.

After the import finishes, Lumen shows how many orders were added and how many lines were skipped, with a reason for each skipped line. You can correct the file and import it again.

## Step 4: Connect your store (optional)

Instead of, or in addition to, CSV files, you can connect an online store so that new orders arrive automatically. The supported store connections are **Shopify** and **WooCommerce**.

1. Open **Settings -> Integrations**.
2. Choose **Shopify** or **WooCommerce**.
3. Follow the on-screen instructions to authorize Lumen to read your orders.
4. Choose how far back Lumen should read existing orders, and confirm.

Only the Owner and Admins can set up connections; Members and Viewers do not see the Integrations page. This is part of the role rules described in the team and roles guide.

After you connect a store, orders appear in Lumen shortly afterwards, and new orders follow as they are placed. Lumen only reads order information; it does not change anything in your store.

A few practical notes:

- A connected store and a CSV import can be used together. Orders that exist in both are matched by order number.
- If the first synchronization seems to take a long time for a store with many orders, give it some time before retrying; the data arrives in the background.
- If you cannot find your store platform on the list, import its orders through CSV files instead.
- For technical details about other integrations and about programmatic access, see the integrations and API guide.

If a connection fails, disconnect and reconnect it, and check that the person who authorizes it has sufficient rights in the store itself.

## Step 5: Build your first report

Once orders are in the workspace, you can build a report.

1. Open **Reports** in the left menu.
2. Select **New report**.
3. Choose a starting point: a template such as "Orders by day", or an empty report.
4. Pick the period, for example the last 30 days.
5. Add the measures you care about, such as number of orders and order total, and group them by day, week, or product.
6. Select **Save** and give the report a name.

On a good first report, aim for one question. "How many orders did we receive each week this quarter?" is a better start than a report that tries to show everything. You can always add more columns later and save a second report.

The full report builder needs a reasonably wide screen. On narrower windows some controls are collapsed, so if the builder looks cramped, enlarge the browser window or use a desktop computer. The system requirements guide gives the details.

When your report is ready, you can share it with colleagues, export it, or schedule it for email delivery. The limits and available formats depend on your plan and are described in the reports and exports guide, so they are not repeated here.

If the Reports page stays blank or something does not render, the troubleshooting guide lists the first things to try.

## Step 6: Invite colleagues and set up notifications

A workspace becomes more useful when the people who need the numbers can see them.

1. Open **Settings -> Team** and select **Invite**.
2. Enter the email address and choose a role.
3. Send the invitation, and ask the person to look in Spam if nothing arrives.

The invitation rules, the roles, and the matter of seats are all described in the team and roles guide.

Next, decide how you want to hear about your business. Lumen can alert you about events in your workspace by push notifications on the mobile app, by email digests, and by messages to **Slack**. To connect Slack, open **Settings -> Integrations** and follow the prompts. The notifications and alerts guide explains how to tune each channel and what to do when notifications are late.

Install the mobile app if you want to look at orders away from your desk. The mobile app guide describes the supported systems and the offline mode. Install it only from the official store for your device.

### First-week checklist

Use this checklist to confirm that the workspace is ready for daily use.

| Done | Task |
|---|---|
| [ ] | Workspace created and data region chosen |
| [ ] | Two-factor authentication switched on for the Owner |
| [ ] | Orders imported by CSV, or a store connected |
| [ ] | First report built and saved |
| [ ] | Colleagues invited with suitable roles |
| [ ] | Push notifications and email digests set up |
| [ ] | Mobile app installed on your phone |

### Common questions

**Can I change the data region later?** No. It is chosen at signup and cannot be changed. Create a new workspace in the right region if needed.

**My CSV import was rejected because of size.** The limit is 5 MB per file. Split the file and import the parts separately.

**Which stores can I connect?** Shopify and WooCommerce. Others can be imported through CSV.

**Where do I see my plan and invoices?** The Owner finds them in the billing settings. Billing questions are described in the billing guide.

**Where can I get help?** Use the help center articles first, then contact support by chat or email.
