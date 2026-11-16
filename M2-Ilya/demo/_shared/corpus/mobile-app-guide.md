---
title: Lumen Mobile App Guide
section: Product
date: 2026-06-09
---

# Lumen Mobile App Guide

The Lumen mobile app gives you your orders and reports on a phone or tablet. It is meant for checking figures and receiving alerts when you are away from your desk; heavier work such as building complex reports is more comfortable in the web version. This guide covers the supported systems, installation, signing in, biometric unlock, offline mode, and the most common problems.

## Supported devices and installation

The Lumen app runs on:

| Platform | Minimum version |
|---|---|
| iOS (iPhone and iPad) | iOS 16 or later |
| Android | Android 10 or later |

Devices with older system versions cannot install the current app. If your device is below the minimum, you can still use Lumen in a supported mobile browser, although some features of the app, such as push notifications and biometric unlock, are only available in the app itself.

**Install the app from official stores only.** Use the official store of your platform: the iOS store on iPhone and iPad, and the Android store on Android devices. The app is published by Lumen Labs. Do not install Lumen from a link in an email or a message, from a file shared on a website, or from an unofficial store. Apps from other sources can be modified and can steal your sign-in details. Lumen Labs never distributes the app as a file to download from a web page, and support staff will never ask you to install it from anywhere but the official store.

To install:

1. Open the store on your device.
2. Search for "Lumen" and check that the publisher is Lumen Labs.
3. Select **Install** or **Get**.
4. Open the app once the installation has finished.

Updates are delivered through the same store. Keep automatic updates switched on so that you receive fixes as soon as they are published. If a customer reports a problem that looks like a known issue, the first suggestion is to update the app; the release notes document lists known issues by version.

## Signing in on mobile

You sign in to the app with the same account as on the web: your email address and password. There is no separate mobile account.

1. Open the app and enter your email address and password.
2. If two-factor authentication is on, enter the six-digit code from your authenticator app, or use a recovery code.
3. Choose the workspace if you belong to more than one.

After the first sign-in, the app keeps you signed in so that you do not have to type credentials every time you open it. If you want a quicker and safer way to reopen the app, switch on biometric unlock (next section).

If you forget your password, use "Forgot password?" on the sign-in screen. The reset procedure, the lockout rules, and the handling of two-factor problems are all explained in the account and login guide. They work the same way in the app and in the browser, so they are not repeated here.

Signing out of the app is done from the app settings. Sign out before you hand in or sell a device, and before you give it to a colleague. If a device is lost, change your password from a computer; the account and login guide describes how.

## Biometric unlock

The app supports **biometric unlock**, which means that you open the app with your fingerprint or face, depending on what your device offers, instead of typing your password.

To switch it on:

1. Open the app and go to **Settings** in the app.
2. Select **Security**.
3. Turn on **Biometric unlock**.
4. Confirm with your fingerprint or face when the device asks.

Some things to know:

- Biometric unlock is a convenience on top of your sign-in. It does not replace your password; it only unlocks a session that is already stored on that device.
- Biometrics are checked by your phone's operating system. Lumen does not receive or store your fingerprint or face data.
- Your device must have biometrics set up in its own settings before the option works. If the option is greyed out, set up a fingerprint or face in the system settings of the device first.
- If the biometric check fails several times, the app asks for the device passcode or for your Lumen password.
- If you add or remove fingerprints or faces on the device, the app may ask you to confirm biometric unlock again.

On shared devices we recommend leaving biometric unlock off. Anyone whose biometrics are registered on that device could open the app.

## Offline mode

When your connection is poor or absent, the app still lets you look at recent data. Offline mode **caches the last 7 days of orders**, and it is **read-only**.

What works offline:

- Browsing and searching the cached orders of the last 7 days.
- Opening the details of those orders.

What does not work offline:

- Creating, editing, or deleting anything. Offline mode never changes data.
- Seeing orders older than 7 days.
- Building or exporting reports.
- Receiving push notifications, since these require a connection to reach the device.

The cache is refreshed whenever the app is online and is open. If you have not opened the app for more than 7 days, the cached orders can be older than the 7-day window; open the app with a connection first to refresh it, then go offline.

Orders that arrive while you are offline appear after the connection returns. The app shows a small banner, "Offline: showing saved data", at the top of the screen so that you can tell the figures are not live.

If you see old data in the app and you are online, pull down on the order list to refresh it. If the list still does not update, check that the device has a working connection and that the app is not restricted from using mobile data in the device settings.

## Tablets and screen sizes

The app adapts to tablets. On a tablet you see the order list and the order details side by side, and charts use the larger screen. On a phone these views are shown one after the other.

The app is intended for viewing reports and following orders. Some report builder controls are simplified on small screens. If you need the full builder, use a desktop browser; the minimum window width for it is described in the system requirements guide.

Mobile app features at a glance:

| Feature | Availability |
|---|---|
| View orders and reports | Yes |
| Push notifications | Yes, see the notifications guide |
| Biometric unlock | Yes |
| Offline mode | Yes, read-only |
| Full report builder | Use a desktop browser |

If a feature works in the browser but not in the app, update the app first and then contact support with the details listed in the section on what to include in a ticket.

### Notifications on mobile

The app is the channel for push notifications about your workspace. To receive them, you must allow notifications for Lumen when the app asks, and you must switch them on inside the app.

The details of what Lumen sends, how fast it should arrive, and how to fix delays are in the notifications and alerts guide. In short: if a notification does not arrive, check the permissions and the power-saving settings of the device before concluding that something is broken in Lumen. Those settings are the most common cause by a wide margin.

If you do not want to receive push notifications on a particular device, for example a shared tablet, you can switch them off in the app without changing the settings for your other devices.

## Troubleshooting the app

Work through the following in order. Each step takes a minute or two.

1. **Update the app** to the latest version from the official store.
2. **Restart the app**: close it fully and open it again.
3. **Check your connection.** Try loading another page or app on the same network. Switch between Wi-Fi and mobile data.
4. **Check the system version.** The app needs iOS 16 or Android 10 or later.
5. **Sign out and sign in again.** Make sure you have your password and authenticator at hand first.
6. **Reinstall the app** from the official store. Your data lives in the cloud, so a reinstall does not delete it.

Common symptoms:

| Symptom | Likely cause | Suggestion |
|---|---|---|
| The app closes right after opening a report | An outdated app version | Update the app, see release notes |
| "Offline" banner while online | Restricted background data or weak signal | Check connection and data permissions |
| Orders look old | The cache is showing | Reconnect and pull down to refresh |
| Biometric option greyed out | No biometrics on the device | Set them up in system settings |
| Cannot find the app in the store | Device below the minimum version | Use a mobile browser, or update the system |

If the app crashes on launch even after a reinstall, note the exact error text if there is one.

## What to include when contacting support

When you contact support about the app, include the following so that the first reply can be useful:

- The platform and system version, for example "Android 13" or "iOS 17".
- The app version, which you can find under the app settings, in the "About" section.
- The workspace name.
- The time in UTC when the problem occurred, as precisely as you can.
- A screenshot of what you see, including any error code.
- What you already tried from the list above.

Do not include your password, authenticator codes, or recovery codes in the ticket. Support staff never need them and will never ask for them.

An example of a log line that a customer might copy from an error screen:

```text
2026-06-02 08:14:31 WARN SyncClient: offline cache refresh skipped (no network)
```

This line is harmless: it only says that the app could not refresh its cache because the device was offline. Include such lines if you see them, but do not worry when they appear in ordinary use.

### Common questions

**Can I use the app on an older phone?** Only if it runs iOS 16 or later, or Android 10 or later. Otherwise, use a mobile browser.

**Can I edit orders offline?** No. Offline mode is read-only and shows the last 7 days of orders.

**Is it safe to install the app from a link a colleague sent?** Install only from official stores. Search for it in the store yourself instead of following a link from a message.

**Does biometric unlock send my fingerprint to Lumen?** No. Your device checks it and Lumen never receives it.
