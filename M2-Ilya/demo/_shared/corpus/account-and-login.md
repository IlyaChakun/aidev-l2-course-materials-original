---
title: Account and Login Guide
section: Account
date: 2026-03-12
---

# Account and Login Guide

This guide explains how to sign in to Lumen, how to manage your password, how two-factor authentication works, and what to do when you are locked out. It is written for customers and for support staff who help them. Every step below can be completed by the account holder without contacting Lumen Labs, with the exceptions that are clearly marked.

## How sign-in works

Every Lumen user has a personal account that is identified by an email address. One account can belong to a workspace, and the role you hold in that workspace decides what you can see and change. Roles are described in the team and roles guide; this guide is only about the account itself, meaning your email address, your password, and your second sign-in factor.

To sign in, open the Lumen sign-in page in your browser or open the mobile app, enter your email address and your password, and select **Sign in**. If two-factor authentication is switched on for your account, Lumen then asks for a six-digit code from your authenticator app. After you enter the code, you land on the workspace you used most recently.

Some things worth knowing about signing in:

- Email addresses are not case sensitive, but passwords are. A password typed with Caps Lock switched on is the most common reason for a rejected sign-in.
- Browser password managers sometimes fill in an old password. If a sign-in fails, type the password by hand once before trying anything else.
- If you belong to several workspaces, one account gives you access to all of them. You switch between them from the workspace name at the top of the left menu.
- Signing in from a new browser or device is allowed without extra steps.

If you cannot remember which email address you used, check your inbox for the original welcome message or an invitation email from a colleague.

## Changing your password

You can change your password at any time while you are signed in. You need to know your current password to do this. If you do not know it, use the reset procedure described in the next section instead.

1. Sign in to Lumen.
2. Go to **Settings -> Security -> Change password**.
3. Enter your current password.
4. Enter the new password twice.
5. Select **Save**.

A strong password is long rather than complicated. A phrase of several unrelated words is easier to remember than a short string of symbols and is harder to guess. Do not reuse a password you use for another service, and do not share it with colleagues. If several people need access to the same workspace, invite each of them with their own account; the team and roles guide explains how.

Lumen stores passwords in a hashed form, so nobody at Lumen Labs can read your password, and nobody can tell you what it is. This also means that a forgotten password cannot be recovered, only replaced.

After a successful change, you stay signed in on the device where you made the change. Other browsers and devices may ask you to sign in again the next time they contact Lumen. If you changed your password because you suspect somebody else knew it, also review the list of people in your workspace and, if anything looks unusual, tell the workspace Owner.

### Password change problems

| What you see | Likely cause | What to do |
|---|---|---|
| "Current password is incorrect" | Typing error or Caps Lock | Retype slowly; if it still fails, use "Forgot password?" |
| "New passwords do not match" | The two entries differ | Retype both fields |
| The Security page is missing | You are in the mobile app, or the page is still loading | Use a desktop browser and reload |
| Save button stays grey | A required field is empty | Fill in all three fields |

## Forgot password

If you cannot remember your password, you can set a new one without help from support.

1. Open the sign-in page.
2. Select **Forgot password?** below the password field.
3. Enter the email address of your account and submit the form.
4. Open the email from Lumen and select the reset link.
5. Choose a new password and confirm it.

The reset link is valid for **60 minutes** and can be used **once**. After you have set the new password, the same link stops working. If you need another one, start again from the sign-in page. A new request makes earlier links obsolete, so always use the most recent email.

The email usually arrives within **5 minutes**. If it has not arrived after that time:

- Check your Spam or Junk folder, and any "Promotions" or "Updates" tabs your mail provider creates.
- Make sure you typed the address of the account, not another address you own. Lumen shows the same confirmation message whether or not the address is registered, so that outsiders cannot discover who has an account.
- Ask your IT administrator whether your company mail system filters or delays automated messages. Messages are sent from a lumen.example sender address, which can be added to an allow list.
- Wait for the full 5 minutes before requesting a second email. Requesting many emails in a row only makes the earlier links stop working.

If the link says it has expired or was already used, request a new one. If the email never arrives even after these checks, the support team can look at the situation, but they cannot set a password for you and will never ask you to tell them a password.

## Sign-in lockout (E-3001)

To protect accounts from guessing attacks, Lumen temporarily locks sign-in after repeated failures. After **5 failed sign-ins** in a row, the account is locked for **15 minutes**. During that time the sign-in page shows error **E-3001**, and even the correct password is rejected.

What to do when you see E-3001:

1. Stop trying to sign in. Every attempt during the lockout is rejected, and it does not shorten the wait.
2. Wait 15 minutes. The lock lifts by itself; there is nothing to approve and no one needs to unlock it.
3. After 15 minutes, sign in again with the correct password. If you are not sure about the password, use **Forgot password?** instead of guessing.

A successful sign-in resets the count of failed attempts. A password reset completed by email also lets you sign in again, but it does not remove the 15-minute wait that has already started, so the new password may be rejected until the lock ends.

If you did not try to sign in yourself and you see E-3001 repeatedly, someone else may be guessing your password. Change your password after the lock ends, switch on two-factor authentication, and tell your workspace Owner. Support staff handling such a ticket should treat it as a normal single-user issue unless the customer reports suspicious activity inside the workspace, in which case the escalation policy applies.

The lockout is per account, not per device. Colleagues with their own accounts are not affected when one person is locked.

## Two-factor authentication

Two-factor authentication (2FA) adds a second step to sign-in. After your password, Lumen asks for a short-lived code produced by an authenticator app on your mobile device. Anyone who learns your password still cannot sign in without that device.

### Switching 2FA on

1. Install any standard authenticator app on your mobile device, if you do not have one.
2. Sign in to Lumen on a desktop browser and open **Settings -> Security**.
3. Select the option to enable two-factor authentication.
4. Scan the QR code shown on the screen with your authenticator app. If you cannot scan, use the text key displayed below the code.
5. Enter the six-digit code the app shows to confirm that the pairing works.
6. Lumen displays your recovery codes. Save them before closing the page.

Authenticator codes change every 30 seconds. If a correct-looking code is rejected, check that the clock on your mobile device is set to automatic. A device clock that is a minute or two off is the usual reason for codes being refused.

### Recovery codes

When you switch on 2FA, Lumen creates **10 single-use recovery codes**. Each code works for one sign-in only, and after it has been used it cannot be used again. Treat the codes like a spare key:

- Print them or store them in a password manager, not in a plain note on the phone that holds your authenticator app.
- Do not take a screenshot and leave it in a shared folder.
- When you have used most of them, generate a new set from **Settings -> Security**. A new set replaces the previous one.

To sign in with a recovery code, select the "Use a recovery code" link on the code prompt and type one of the codes.

## Lost phone or lost authenticator access

If you can no longer open your authenticator app, for example because the phone was lost, stolen, or reset, the way back in depends on what you still have.

| Situation | What to do |
|---|---|
| You still have recovery codes | Sign in with one recovery code, then go to **Settings -> Security** and set up 2FA again on the new device |
| No recovery codes, and you are a Member, Viewer or Admin | Ask the workspace Owner to reset 2FA for you |
| No recovery codes, and you are the Owner | Identity verification by the Security team is required |

Only the workspace **Owner** can reset two-factor authentication for other members. After the reset, the member signs in with email and password only and then sets up a new authenticator. Admins cannot do this on behalf of members.

For an Owner who has lost both the phone and the recovery codes, the process is different. The Security team must verify the Owner's identity before 2FA is reset. This is not something the first line can do or approve, and the customer should not be asked to send documents or personal details through the ticket. The support operator explains that the request goes to the Security team, which will contact the account holder directly, and escalates the ticket with a one-sentence reason.

Support staff must never switch off 2FA, never read out or request a code, and never accept a screenshot of an authenticator code as proof of identity.

## Changing the account email address

You can change the email address of your account if your address changes, for example when you move to a new company mailbox. Because the email address is how Lumen identifies you and where reset links are sent, this change has extra safeguards.

1. Sign in and open **Settings -> Account**.
2. Select **Change email** and enter the new address.
3. Enter your **current password** to confirm that it is really you.
4. Lumen sends a confirmation link to the **old address** and another confirmation link to the **new address**.
5. Open both emails and confirm both links.

The change takes effect only after both links have been confirmed. Until then, you continue to sign in with the old address. If the old mailbox no longer exists and you cannot receive the first link, the change cannot be completed on your own; ask the workspace Owner to remove your old account from the team and invite your new address instead.

Things to check when the change does not go through: the new address must not already belong to another Lumen account, and confirmation emails can end up in Spam, as with reset links. If you have 2FA switched on, it stays on after the email change.

### Common questions

**I never received the reset email. Can support send me a password?** No. Support cannot see, set, or send passwords. Follow the reset steps and check Spam first.

**Can I be locked out for good?** No. The lockout lasts 15 minutes and then ends by itself.

**Do I need 2FA?** It is optional, but strongly recommended for Owners and Admins.

**Can two people share one account?** This is discouraged. Invite people individually instead.

**Who can I ask for help?** Use the chat or email channels listed in the support hours and SLA document. Support will never request your password, a one-time code, or your full card number.
