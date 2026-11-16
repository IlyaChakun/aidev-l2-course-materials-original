---
title: Notifications and Alerts
section: Product
date: 2026-07-21
---

# Notifications and Alerts

Lumen can tell you about what happens in your workspace in three ways: push notifications on the mobile app, email digests, and messages in Slack. This guide explains how each channel works, how fast notifications should arrive, how to set them up, and what to do when they are late or missing. Most delay complaints turn out to be caused by phone settings rather than by Lumen, and the steps below are written to find that out quickly.

## Notification channels

| Channel | Where it appears | Best for |
|---|---|---|
| Push notification | Mobile app, on the lock screen and in the notification list | Time-sensitive events when you are away from your desk |
| Email digest | Your inbox | A summary you can read at your own pace |
| Slack | A Slack channel you choose | Keeping a team informed in one place |

You can use any combination. Each person controls their own notification settings; changing yours does not change anyone else's. The settings are per person and per device for push, and per person for email.

Typical events that can trigger a notification include the arrival of a new order in a connected store, a scheduled report being ready, a failed delivery in an integration, and changes to your workspace made by an Admin. Not every event is available on every channel, and the list in the settings screen shows exactly what you can choose.

Notifications are informational. They are not a guaranteed alarm system, and they should not be the only way you find out about something critical for your business. For outages and service problems, check the status page described in the service status document.

The sections below describe each channel in turn and then the troubleshooting procedure for push delays, which is the most common reason customers contact support.

## Push notifications

Push notifications are delivered to the Lumen mobile app on your phone or tablet. To receive them you need the app installed on a supported system, an account signed in on the device, push notifications allowed by the device, and push switched on inside the app.

**Normal push delivery is under 60 seconds.** From the moment the event happens in your workspace, the notification should appear on your device in less than a minute. A delay of a few seconds to half a minute is normal and depends on the network.

To switch push on:

1. Open the Lumen app.
2. Go to **Settings -> Notifications**.
3. Turn on **Push notifications**.
4. Choose which kinds of events you want to hear about.
5. When the device asks for permission, allow notifications.

If you denied the permission earlier, the in-app switch cannot override that. You need to open the notification settings of the operating system, find Lumen in the list of apps, and allow notifications there.

Push notifications need a connection to reach your device. When the device is offline, notifications wait and may be delivered when it reconnects, depending on how long it was offline. The offline mode of the app does not itself receive notifications; see the mobile app guide for what offline mode does.

You can switch push off on one device while keeping it on for another, which is useful for shared tablets. Signing out of the app on a device also stops push to that device.

## Why notifications arrive late

When a customer says "my notification arrives 15 or 20 minutes late", it is nearly always the same cause. **Delays of 15-20 minutes are almost always caused by phone battery optimization on Android, or by Focus modes and Background App Refresh settings on iOS.**

The operating system saves battery by putting apps to sleep and bundling their network activity. If Lumen is treated as an app to be put to sleep, the system holds the notification and releases it in a batch a quarter of an hour or more later. The notification was sent on time; the phone delivered it late.

Typical signs of this cause:

- The delay is consistent, in the range of about 15-20 minutes, rather than random.
- Notifications arrive late when the phone has been idle or locked, but arrive promptly when the app is open.
- Several apps on the same phone show similar delays.
- The problem started after a phone update, a new battery-saving setting, or a new Focus mode.

Signs that point elsewhere:

- No notification arrives at all, even after hours. Check the permission, the in-app switch, and whether the device is signed in.
- The delay is just a few minutes at random. Slow networks or a brief service issue can cause this.
- Delays affect everyone in the workspace at the same time. Check the status page and see the section on when to escalate.

One more known cause exists, which has been fixed in a software update: older Android app versions caused delayed notifications. The release notes document describes it and the fixed version, so if a customer on Android has not updated for a long time, updating the app is a first step.

## Fixing push delays on Android

On Android, the manufacturer's battery management is usually the problem. Menu names differ between brands, so the wording below describes the idea.

1. Open the Lumen app and go to **Settings -> Notifications**. Make sure push is switched on.
2. Open the system settings of the phone and go to **Apps**, then **Lumen**.
3. Open the **Battery** section and choose **Unrestricted** or "Don't optimize". This is what is meant by **disabling battery optimization for Lumen**.
4. In the same app settings, make sure notifications are allowed and that the channel for Lumen alerts is not set to silent.
5. If your phone has an extra "app launch" or "auto-start" manager, allow Lumen there.
6. Check that Do Not Disturb is not active during the hours you expect the notifications.
7. Restart the phone and ask for a test event, for example by waiting for the next order.

Some phones also have an adaptive battery mode that learns which apps you rarely open and restricts them. If you open Lumen seldom, the phone may decide that it is unimportant. Setting the battery option to unrestricted for Lumen overrides that decision.

After making the changes, test the result over a day. If notifications now arrive within a minute, the cause was the battery management. If they are still delayed, collect the details described in the section on what to send to support.

## Fixing push delays on iOS

On iPhone and iPad, delays come from Focus modes and from Background App Refresh.

1. Open the Lumen app and go to **Settings -> Notifications**. Make sure push is switched on.
2. Open the system **Settings** of the device, find **Lumen**, and make sure **Notifications** are allowed. Choose an alert style that you will actually notice.
3. In the same place, allow **Background App Refresh** for Lumen. This is the setting that lets the app prepare its data and keeps notifications timely.
4. Check your **Focus modes**, such as Do Not Disturb, Work, or Sleep. A Focus mode can silence or defer notifications from apps that are not on its allowed list. Add Lumen to the allowed apps of the Focus you use, or switch the Focus off while testing.
5. Check **Low Power Mode**. When it is on, the system reduces background activity and notifications may be late. Turn it off while testing.
6. Restart the device.

Notifications that were deferred by a Focus mode are not lost; they are shown in the notification list when the Focus ends. That is why customers sometimes report "notifications come all at once in the morning".

| Setting | Where | Recommended for timely push |
|---|---|---|
| Notifications | System settings, Lumen | Allowed |
| Background App Refresh | System settings, Lumen | On |
| Focus modes | System settings, Focus | Lumen in allowed apps |
| Low Power Mode | Battery | Off during testing |

## Email digests

Email digests collect notifications into messages sent to the address of your account. You choose how often they arrive:

- **Instant**: one email per event, as it happens.
- **Hourly**: one email per hour, if anything happened in that hour.
- **Daily**: one email per day with a summary of everything.

To change the frequency, open **Settings -> Notifications** in the web app, find the email section, and choose Instant, Hourly, or Daily. You can also switch email off for a type of event.

Digests are only sent when there is something to report. If nothing happened in the period, you do not receive an empty email.

If digests do not arrive:

1. Look in Spam or Junk, and in tabs your mail provider uses for automated mail.
2. Confirm that the digest is switched on and that the frequency is what you expect. A daily digest does not arrive every hour.
3. Check that the email address of your account is correct. If you changed the address recently, the digest goes to the new one; the account and login guide describes how the change works.
4. Ask your IT team whether automated messages from Lumen are filtered.

Email arrival time is less predictable than push, because mail servers can delay messages. A delay of a few minutes on an Instant digest is not a problem. A delay of an hour or more affecting several users in one company is usually a mail filter.

## Slack notifications

Lumen can send notifications into a Slack channel, which is useful when a whole team follows orders. The connection is set up by an Owner or an Admin, because it is an integration of the workspace.

1. Open **Settings -> Integrations** and choose Slack.
2. Authorize Lumen in your Slack workspace and select the channel that should receive messages.
3. Choose the event types that should be posted.
4. Send a test message to confirm that it works.

Slack messages are separate from push and email, and changing your personal settings does not stop the team channel. To stop them, an Owner or Admin has to change the Slack connection.

If messages do not appear in the channel, check that the channel still exists, that Lumen has permission to post there, and that the connection has not been removed. If the connection was removed, reconnect it. For the full list of integrations and their behavior, see the integrations and API guide.

## What to send to support

If you have followed the steps above and notifications are still late or missing, contact support through chat or email and include:

- The device model and the system version, for example "Android 13" or "iOS 17".
- The Lumen app version, found in the app settings.
- Which channel is affected: push, email, or Slack.
- Examples with the time of the event and the time you received the notification, in UTC if possible.
- The workspace name.
- Which of the fixes you already tried.

Support staff treat a single user's delay as a normal priority matter and guide the customer through the steps in this guide. If many users in the same workspace report that all notifications stopped or are very late at the same time, support checks the status page and treats this as a possible incident rather than a phone setting.

Never send passwords or codes from your authenticator app to support.

### Common questions

**How fast should push notifications arrive?** Under 60 seconds.

**Why do I get notifications 15 or 20 minutes late?** Almost always because of battery optimization on Android, or Focus modes or Background App Refresh on iOS.

**Can I get a summary instead of many emails?** Yes. Choose Hourly or Daily in **Settings -> Notifications**.

**I changed my settings but my colleague still gets alerts.** Settings are personal. Each person manages their own.

**Do offline phones receive notifications?** Not until they reconnect.
