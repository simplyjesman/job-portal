# ADR 0002: Invite-Based Hiring Model (Replaces Job Postings)

**Status:** Accepted (Revised)  
**Date:** 2026-10-08  
**Replaces:** Original ADR 0002 (Mutual Hire Confirmation)  
**Context:** Employers need to find and hire candidates directly, without posting job listings.

## Problem

Two approaches to hiring:

1. **Job Postings Model** (original): Employer posts job → Candidate applies → Employer shortlists → Mutual confirmation → Commission
   - ❌ Extra friction: requires job listing creation upfront
   - ❌ Candidates must actively search jobs
   - ✅ Candidates know what role they're applying for

2. **Invite-Based Model** (chosen): Employer searches candidates by skills → Sends invite with job details → Candidate accepts/declines → Commission
   - ✅ Simpler flow: employer-driven hiring
   - ✅ No job listing overhead
   - ✅ Direct candidate targeting by skills
   - ❌ Candidates may receive unsolicited invites

## Decision

Replace job postings with **interview invites**. Employers:
1. Search candidate profiles by skills/location
2. Send interview invite (includes job description, salary, custom message)
3. Candidate accepts or declines
4. On acceptance → Hire confirmed + Commission triggered

### Process Flow
```
Employer searches by skills
    ↓
Employer selects candidate(s)
    ↓
Employer sends Interview Invite (with job description)
    ↓
Candidate receives invite
    ↓
Candidate accepts or declines
    ↓
If accepted → Hire (commission triggered immediately)
If declined → Invite closed
```

### Key Differences from Original
| Aspect | Job Postings | Invites |
|--------|-----|---------|
| **Who initiates** | Candidate (apply) | Employer (invite) |
| **Job visibility** | Public listing | Private invite |
| **Shortlisting step** | Required | Removed |
| **Mutual confirmation** | Both parties confirm | Candidate accepts (auto-confirm) |
| **Commission trigger** | Both confirm | Candidate accepts |
| **Timeline** | Longer (apply → shortlist → confirm) | Faster (invite → accept) |

## Rationale

| Aspect | Job Postings | Invites |
|--------|-----|---------|
| **Friction** | Higher (multi-step) | Lower (direct approach) |
| **Employer effort** | Post job, wait, review apps | Search skills, send invites |
| **Candidate experience** | Active job search | Passive (receive invites) |
| **Volume** | Many candidates per job | Many jobs per candidate |
| **Conversion** | Some% apply, some% hired | Higher (targeted invites) |

**Trade-off:** Invites are less discoverable for candidates (they don't see open roles), but more efficient for employers (direct targeting). Better for employer-driven hiring in a niche market.

## Consequences

### Positive
- **Simpler flow** — No job postings, no multi-step confirmation
- **Faster hiring** — Employer to hire in 2-3 steps, not 5-6
- **Targeted** — Employer selects candidates by exact skills needed
- **Lower friction** — No job description upfront, included in invite
- **Better match** — Employer pre-filters before inviting

### Negative
- **Less transparent** — Candidates don't see available roles upfront
- **Invite spam risk** — Bad actors could send mass invites
- **No job history** — No public listing of "open roles"
- **Candidate needs profile** — Must complete profile before receiving invites

## Implementation

### New Entities
- `InterviewInvite` — Replaces `Job` and `Application`
  - Candidate (FK)
  - Employer (FK)
  - Job description (text)
  - Salary min/max (optional)
  - Required skills (optional)
  - Custom message (optional)
  - Status: sent, accepted, declined
  - Sent/accepted/declined timestamps

### Removed Entities
- `Job` — No longer needed
- `JobSkill` — No longer needed (skills stay on Candidate profile)

### Updated Entities
- `HireConfirmation` → Simplified (candidate just accepts invite, no mutual step)
- `Commission` — Triggered on `InterviewInvite.accepted` instead of mutual confirmation

### Workflow
1. Employer searches candidates (GET /api/candidates?skills=python,django&location=london)
2. Employer sends invite (POST /api/invites)
3. Candidate sees pending invites (GET /api/invites/pending)
4. Candidate accepts/declines (PATCH /api/invites/{id})
5. On accept → Auto-create Hire + Commission

## Decision Reversibility

**Hard to reverse.** Changing back to job postings would require:
- Re-adding Job model and migrations
- Rebuilding Application/invite workflow
- Data migration: convert InterviewInvites to Jobs
- Re-implementing job discovery UX
- Re-training users on new flow

However, invites can be extended to include job posting features (e.g., "publish this invite as a public job") without major rework.

## Related Decisions

- ADR 0001: Profile-as-CV still applies (candidates need rich profiles for search/invite)
- See CONTEXT.md for updated entity relationships and workflow
