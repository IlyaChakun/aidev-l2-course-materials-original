---
title: Team Management and Roles
section: Account
date: 2026-04-02
---

# Team Management and Roles

A Lumen workspace is shared by the people who track orders and build reports together. This guide describes the four roles, who is allowed to invite or remove people, how invitations work, and what happens with seats. It also lists the most frequent questions about team management so that customers and support staff can find the answer in one place.

## The four roles

Every person in a workspace holds exactly one of four roles. The role controls what the person can do; it can be changed later by someone with sufficient rights.

| Role | Can create and export reports | Can manage team | Can manage integrations | Can manage billing |
|---|---|---|---|---|
| Owner | Yes | Yes | Yes | Yes |
| Admin | Yes | Yes | Yes | No |
| Member | Yes | No | No | No |
| Viewer | View only, cannot export | No | No | No |

In plain words:

- **Owner**: the person who is responsible for the workspace. The Owner can do everything an Admin can do and, in addition, can manage billing, which includes seeing invoices and changing the payment method. There is **exactly one Owner per workspace**.
- **Admin**: a trusted colleague who runs the day-to-day setup. Admins can manage the team and the integrations of the workspace, but they cannot manage billing.
- **Member**: a regular user. Members can create reports and export them, but they cannot change who is in the workspace and they cannot change integrations.
- **Viewer**: a read-only role, useful for managers, accountants, or external partners who only need to look at the data. A **Viewer cannot export reports**. A Viewer who needs a file must ask a Member, Admin, or Owner to produce it.

Roles apply per workspace. If one person belongs to two workspaces, they can be an Admin in one and a Viewer in the other.

A role does not change what a person sees in the mobile app compared with the browser: the same rules apply everywhere. If a user reports that a button is missing, the first thing to check is the role of that user, because buttons that the role is not allowed to use are hidden rather than greyed out.

## Who can invite and remove people

**Only Owners and Admins can invite or remove people.** Members and Viewers do not see the invitation controls at all. This is deliberate: it keeps the list of people with access to business data under the control of the people who are accountable for the workspace.

This rule has a few practical consequences:

- A Member who wants a colleague added should ask an Admin or the Owner to send the invitation.
- An Admin can invite and remove Members and Viewers and other Admins. Only the Owner can hand over the Owner role (see the section on transferring ownership).
- If the Owner leaves the company without transferring ownership, nobody else can manage billing for the workspace. Owners should therefore transfer ownership before they leave.
- A support operator cannot invite or remove people on behalf of a customer. The operator explains the steps and the required role.

When a customer asks "why can't I invite my colleague", the answer is almost always one of two things: their role is Member or Viewer, or every included seat is already taken (described below). Check the role first, since it takes only a moment: the role is shown next to the user's name on the **Settings -> Team** page.

## Inviting a new user

To invite someone you must be an Owner or an Admin.

1. Sign in and open **Settings -> Team**.
2. Select **Invite**.
3. Enter the email address of the person.
4. Choose a role: Admin, Member, or Viewer.
5. Select **Send invitation**.

The person receives an email with an invitation link. The link is valid for **7 days**. When the invited person opens it, they either create a new Lumen account or, if they already have an account under that address, sign in and accept. They then appear in the team list with the role you chose.

Invitations that have not been accepted appear in the team list with the status "Pending". From there you can:

- **Re-send** the invitation. The invitation link can be re-sent at any time while it is pending, and re-sending is also the right action once the 7 days have passed and the link has expired.
- **Revoke** the invitation if you invited the wrong address.
- **Change the role** before the person accepts.

Some tips that prevent the usual problems:

- Check the spelling of the address before sending. An invitation to a mistyped address cannot be redirected; revoke it and send a new one.
- Ask the invitee to look in Spam if the email does not arrive.
- The invitation is tied to the address it was sent to. If the person wants to use a different address for the account, send a new invitation to that address.
- Pending invitations count toward the use of seats only after they are accepted, so a pending invitation by itself does not take a seat.

## Seats and invitation limits

Each workspace includes a fixed number of seats, depending on the plan. The exact numbers and the price of additional seats are listed in the plans and pricing document, and are deliberately not repeated here.

A seat is used by every person who has accepted an invitation and holds any role, including Viewers and Admins. The Owner also uses a seat.

When **all included seats are used, invitations are blocked** until a seat is freed or extra seats are added. In practice, the customer sees a message on the Invite screen that no seats are available. There are two ways to continue:

1. **Free a seat** by removing a person who no longer needs access.
2. **Add extra seats** to the workspace. Which plans allow this, and for how much, is described in the plans and pricing document. The Owner makes this change in the billing settings.

The workspace is not blocked as a whole if seats run out; existing users continue to work normally. Only sending new invitations is affected.

If a customer on the smallest plan asks to add seats, point them to the plans and pricing document for the available options; the first line does not calculate prices or promise a particular arrangement.

| Situation | What the customer sees | Next step |
|---|---|---|
| Seats available, role allows | Invite works | Send the invitation |
| Seats full | Invitation blocked | Remove a user or add seats |
| Role is Member or Viewer | No Invite button | Ask an Admin or the Owner |

## Removing a user

An Owner or an Admin can remove someone from the workspace.

1. Open **Settings -> Team**.
2. Find the person in the list.
3. Open the menu next to their name and choose **Remove from workspace**.
4. Confirm.

**Removing a user frees the seat immediately.** There is no waiting period, so a replacement can be invited right away. The removed person loses access to the workspace at once and will see a message that they no longer belong to it the next time they open the app.

What removal does not do:

- It does not delete the person's Lumen account. The person can still sign in and can belong to other workspaces.
- It does not delete reports or other content the person created. Saved reports stay in the workspace, so a colleague's departure does not break the reports other people rely on.
- It does not cancel anything related to billing.

Two special cases deserve attention. First, the **Owner cannot be removed** while they hold the Owner role; ownership must be transferred first. Second, an Admin cannot remove the Owner, and cannot remove themselves if they are the only person able to manage the team. In that situation, ask the Owner to promote another Admin first.

When an employee leaves your company, remove them from the workspace on their last day. This is the fastest way to end their access to order data and also frees a seat for a replacement.

## Changing roles

The Owner and Admins can change the role of a team member.

1. Open **Settings -> Team**.
2. Select the person.
3. Choose the new role from the list and save.

The new role takes effect immediately; the person does not need to sign in again, but may have to reload the page to see new controls. Typical reasons to change a role are:

- Promoting a Member to Admin when they take over the setup of the workspace.
- Demoting an Admin to Member when their responsibilities change.
- Giving an accountant the Viewer role so that they can check figures without being able to export data.
- Moving a Viewer to Member because they now need to produce exports.

A change of role never changes the person's email address, password, or two-factor authentication settings. Those belong to the personal account and are covered in the account and login guide.

Keep the number of Admins small. Admins can manage integrations and the team, so each Admin is another person who can change how the workspace connects to your store and who has access. Many workspaces work well with one Owner, one or two Admins, and everybody else as Members or Viewers.

## Transferring ownership

There is exactly one Owner per workspace, but ownership is not permanent. The current Owner can transfer it to another person who is already in the workspace.

1. The Owner opens **Settings -> Team**.
2. The Owner selects the person who should become the new Owner.
3. The Owner chooses **Transfer ownership** and confirms.

After confirmation, the new person becomes the Owner and the previous Owner becomes an Admin. Billing access moves with the Owner role: the new Owner can see invoices and manage the payment method, and the former Owner can no longer do so.

Only the current Owner can start a transfer. Admins cannot do it, and neither can support staff. If the Owner is no longer reachable, for example because they have left the company, a transfer cannot be done by the first line. Collect the workspace name and a short description of the situation and escalate the ticket according to the escalation policy. Do not ask the customer to share passwords, and do not suggest workarounds that involve logging in as the former Owner.

Before you transfer ownership, make sure that:

- The new Owner has a working sign-in and, ideally, two-factor authentication switched on.
- Any exports or data requests that only the Owner can perform have been completed, or the new Owner knows about them.
- The new Owner is aware that they are now the contact for billing matters.

## Common questions

**A new colleague says they never got the invitation.** Ask them to check Spam. If it is still missing, an Owner or Admin can re-send it from **Settings -> Team**. If more than 7 days have passed, re-send it as well; the link is valid for 7 days from each sending.

**The invitation says it has expired.** Ask an Owner or Admin to re-send the invitation.

**I am an Admin but cannot see billing.** That is expected. Admins manage the team and integrations; billing belongs to the Owner.

**A Viewer needs a CSV file.** Viewers cannot export reports. Ask a Member, Admin, or Owner to export it, or change the Viewer's role to Member.

**Can I have two Owners?** No. A workspace has exactly one Owner. Admins are the right way to share responsibility.

**I removed someone by mistake.** Invite them again. Since removal frees the seat immediately, the seat is available for the new invitation, provided no one else has taken it in the meantime.

**Do removed people lose their own account?** No. Only their access to this workspace is removed.

**Where do I reset someone's two-factor authentication?** The workspace Owner can do this for members; see the account and login guide for the full procedure.
