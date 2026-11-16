---
title: Security and Compliance
section: Policy
date: 2026-06-02
---

# Security and Compliance

This document describes how Lumen protects customer data, which security features are available in the product, and how security reports are handled. It is intended for support staff who need to answer general security questions correctly, and for customers who want to understand the protection measures that apply to their workspace.

## Encryption of data

Lumen protects data both when it is stored and when it travels between devices and servers.

| Where | Protection |
|---|---|
| Data at rest (databases, file storage, backups) | AES-256 encryption |
| Data in transit (browser, mobile apps, API, webhooks) | TLS 1.2 or higher |

### Data at rest

Everything that Lumen stores for a workspace, including orders, reports, settings and uploaded files, is encrypted with AES-256. Encryption keys are managed separately from the data they protect, and access to key management is restricted to a small group of engineers. Backups use the same encryption as the primary storage.

### Data in transit

All connections to Lumen use TLS 1.2 or higher. Connections that use older protocol versions are refused. This applies to the web app, the mobile apps and the public API. Webhook deliveries to customer systems are also sent over encrypted connections, and customers are encouraged to verify the signature header described in the integrations documentation.

### What staff may say

Operators may state the two facts in the table above. They should not describe key lengths for other layers, name specific cloud providers, or give details of the internal architecture. If a customer asks for a more detailed security description, for example in a vendor questionnaire, the ticket is escalated to the Security team.

## Data region

When a workspace is created, the Owner chooses the data region: **EU** or **US**. The workspace data is stored in the selected region.

### The choice is permanent

The data region is chosen at signup and **cannot be changed** afterwards. This is a deliberate design decision: moving data between regions would break the guarantee that the data stays where the customer expects it to be. A customer who wants a different region has to create a new workspace in the desired region and import the data there, for example by using the CSV import described in the onboarding guide.

### Questions that come up

| Question | Answer |
|---|---|
| Can the region be changed later? | No |
| Can support move a workspace to another region? | No, support cannot do this |
| Where can the customer see the region? | It was selected during workspace creation |
| Does the choice influence prices? | No statement is made here; see the plans overview |

Operators must not promise that a region change will become possible in the future. If a customer insists, the ticket can be passed to the Support Lead, who may involve the Privacy team where a legal requirement is mentioned.

### Relationship to privacy requests

The region of storage is a technical fact. It is not a legal statement about where data may be processed. Questions that ask for legal conclusions about data transfers, such as "is this region sufficient for our regulator?", are privacy requests and are handled by the Privacy team. See the data privacy document for details.

## Passwords and authentication

### Password storage

Passwords are never stored in readable form. Lumen stores them as **bcrypt** hashes, which means that even employees with access to the database cannot read a customer's password. Because passwords are hashed, support cannot look up a forgotten password; the only option is a reset by the customer, which is described in the account and login guide.

### Staff never ask for passwords

**Lumen staff never ask for passwords.** This applies to every channel and every team. A customer who receives a message that asks for a password, a one-time code or a full card number should treat it as suspicious, whatever name or logo it shows. Support staff must not ask for these items in tickets, even if the customer offers them. If a customer pastes a password into a ticket, the operator tells them to change the password at once and escalates the ticket so that the text can be removed from the ticket system.

### Two-factor authentication

Two-factor authentication (2FA) adds a second step to sign-in and is recommended for all users, especially Owners and Admins. The setup and recovery steps are in the account and login guide. The first line does not reset 2FA for Owners; that case requires identity verification by the Security team.

### Single sign-on

**SAML single sign-on is available on the Business plan only.** With SAML SSO, members sign in through the company's identity provider instead of using a Lumen password. Setting up SSO is done by the Owner or an Admin with the help of the identity provider's documentation. Plan availability is described in the plans overview; the first line does not make exceptions.

## Audit log

Lumen includes an audit log in the product. The log records important events in the workspace, such as sign-ins, changes to team members and roles, changes to integrations and API keys, and exports. Each entry shows the time in UTC, the user and the action.

### Reading the log

Owners and Admins can open the audit log from the workspace settings. Typical uses:

1. Find out who removed a team member or changed a role.
2. Check when an API key was created or revoked.
3. Confirm that an unusual sign-in was or was not the customer's own.

### Retention

How long audit log history is kept depends on the plan. The retention periods are plan facts and are listed in the plans overview, not here. If a customer asks for events that are older than the retention of their plan, the operator explains that the log does not hold them. Support cannot retrieve deleted log entries.

### Limits of the log

The audit log shows what happened inside Lumen. It does not show actions in other systems, such as a store connected through an integration. A customer who suspects unauthorised access should first check the audit log together with the list of team members, then follow the steps described in the next section.

## Reporting security incidents and vulnerabilities

Security incidents and vulnerability reports go to the **Security team**. They are **never handled by the first line**.

### What counts as a security matter

- A customer believes that someone has gained unauthorised access to their workspace.
- A customer has found a weakness in Lumen, for example a page that shows data of another workspace.
- Someone reports phishing messages that pretend to come from Lumen.
- A customer has exposed an API key publicly.
- A person claims to have found a flaw and offers details.

### What the first line does

The operator does not investigate, does not ask for technical details of the flaw and does not confirm or deny that a flaw exists. The operator escalates immediately with priority urgent, using one short factual sentence as the reason, such as "Customer reports possible unauthorised access to workspace."

For exposed credentials, the operator can give the general advice that is already in the product documentation: change the password, and revoke and recreate the API key. These steps are described in the account and login guide and the integrations documentation.

### Sample reply

```text
Hello, thank you for reporting this. Security matters are handled by our
Security team, so I have passed your message on to them straight away.
Please do not share passwords or access codes in this ticket.
```

### Researchers and vulnerability reports

People who report a vulnerability may write to the public security contact, `security@lumen.example`. Reports are read by the Security team. Operators who receive such a report in the support queue forward it as an escalation and do not discuss it with the sender.

## Compliance statements

Customers and prospects sometimes ask whether Lumen holds particular certifications or satisfies a particular regulation. Answers to these questions are statements with legal and commercial consequences, so they are not given by the first line.

### What the first line may do

The operator may describe the measures in this document: encryption, region choice, hashed passwords, audit log and SSO on Business. The operator may point to the help articles. The operator must not say that Lumen "is compliant" with any standard, "is certified" or "passes audits."

### Where compliance questions go

Questions about certifications, security questionnaires, audit reports and contractual security terms are escalated to the Security team, with the privacy aspects going to the Privacy team. The data privacy document explains the boundary between the two.

### Short reference

| Topic | Fact |
|---|---|
| Encryption at rest | AES-256 |
| Encryption in transit | TLS 1.2+ |
| Data region | EU or US, chosen at signup, cannot be changed |
| Password storage | bcrypt hashes |
| SAML SSO | Business plan only |
| Security reports | Security team only |
| Staff and passwords | Staff never ask for passwords |
