# Smart support — vision

> Updated: 04.08.2026 · Strategy: [`strategy.md`](strategy.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Where we are headed

**The user and their world.** A support on-call person in a team of four, through whom about
forty requests a day pass. They read the queue in order, because urgency is visible only from
the text, and spend half their time on requests whose answer sits in a policy they last read
half a year ago.

**What it looks like when it works.** The on-call person opens a queue sorted by urgency, and
every request already has a draft answer with links to the policy. They check and send instead
of searching. What the first line cannot close reaches an engineer with the context already
assembled, and the engineer does not re-ask the basics.

**Why I am the one to do it.** I have half a year of closed requests and the policies this
support really works by, not generic articles from the internet. The system will answer in our
wording and by our escalation rules.

**What it will not be.** The system does not send anything to the customer by itself and does
not close requests without a human.

## Boundary

What we do not do and do not intend to do:

- Answer the customer directly: the answer goes out from a human, and this is not a technical
  limitation but the essence of the idea. Support already had an auto-responder, and it was
  abandoned.
- Calculate metrics of the on-call people's work and compare people with each other: the
  system helps, it does not evaluate.
- Replace the first line entirely: the goal is to remove searching and typing, not the person.
- Work with audio: for phone requests the queue already holds text typed by the on-call
  person. We do not connect to call recordings and do not intend to transcribe them.

## Check

| Question | What the vision answers |
|---|---|
| Add an auto-reply to simple requests without the on-call person? | No, that is directly outside the boundary |
| Support found no solution in the knowledge base. Let it answer from the model's general knowledge? | No. We answer from our policies, otherwise the only advantage is lost |
| Show the on-call person how many requests they closed in a day? | No, that is evaluating people |
| Assemble context for the engineer that they did not ask for? | Yes. That is exactly the future state the whole thing is done for |

## What this file does not contain

Technical decisions, the list of features, deadlines and metrics. Product framing is in
[`strategy.md`](strategy.md), stages in [`roadmap.md`](roadmap.md), the breakdown of work in
[`backlog/`](backlog/).
