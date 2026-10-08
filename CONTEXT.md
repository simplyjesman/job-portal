# Job Portal — Domain Model

## Entities & Core Concepts

### User Types

**Candidate**
A person seeking employment. Has a profile containing structured CV data (name, contact, skills, work history, education, certifications, portfolio links). Receives interview invites from employers. Can accept or decline invites. Not tied to an employer.

**Employer**
A company or organization hiring. Represented by a team account with multiple team members (HR staff). Searches candidates by skills/location and sends interview invites. Pays commissions on successful hires.

**Employer Team Member** (or **Team User**)
A person who belongs to an Employer account (e.g., HR manager, recruiter). Can search candidates, send interview invites, confirm hires, manage team members. Multiple team members per Employer.

### Candidate Profile & Skills

**Candidate Profile**
Structured CV data entered by a Candidate: name, email, phone, location, skills (multi-select from predefined list), work history (company, role, dates, description), education (institution, degree, field, dates), certifications, portfolio links, availability, salary expectations. The profile IS the CV (no separate CV file upload).

**Supporting Document**
Optional file uploaded by a Candidate to supplement their profile. Types: cover letter, portfolio sample, certification image, reference. Max 5 per Candidate. Visible on their profile.

**Skill**
A searchable, predefined tag (e.g., "Python", "Django", "AWS", "Leadership"). Candidates select from this list on their profile. Employers search/filter by skills to find candidates. Searchable and filterable.

### Interview Invites & Hiring

**Interview Invite**
Employer sends an interview invite to a Candidate with:
- Job description/role details
- Salary range (optional)
- Required skills (optional)
- Custom message from Employer

Candidate can **accept** or **decline** the invite. Statuses: **sent**, **accepted**, **declined**.

**Hire Confirmation**
When Candidate accepts an interview invite, a Hire is automatically confirmed. Commission is triggered immediately on acceptance (no mutual confirmation step needed). Employer can track:
- When invite was sent
- When candidate accepted
- When hire is finalized (30 days post-acceptance)

**Commission**
Payment from Employer to Platform on successful hire. Triggered automatically when Candidate **accepts** interview invite.

**Commission Invoice**
Monthly batch invoice to Employer for all accepted hires that month. Settled via Stripe or bank transfer.

**Refund Window**
30-day period after hire acceptance. If Candidate leaves or is terminated within 30 days, Employer is refunded the commission. After 30 days, commission is non-refundable and hire is finalized (no new disputes allowed).

### Data Lifecycle

**Archive** (soft-delete)
When a Candidate deletes their account, their profile and documents are marked archived (soft-deleted), not immediately erased. Archived data is retained for 90 days to resolve hire disputes.

**Erasure** (true deletion)
After 90-day archive period, archived Candidate data is permanently deleted per GDPR right to erasure.

---

## Relationships & Constraints

| Relationship | Cardinality | Notes |
|---|---|---|
| Candidate → Profile | 1:1 | One profile per Candidate. |
| Candidate → Supporting Documents | 1:N | Max 5 documents per Candidate. |
| Candidate → Interview Invites | 1:N | Multiple invites from different employers. |
| Employer → Team Members | 1:N | Multiple HR staff per Employer. |
| Employer → Interview Invites | 1:N | One Employer sends many invites. |
| Employer → Hires | 1:N | Multiple hires from accepted invites. |
| Interview Invite → Hire (if accepted) | 0:1 | Becomes a Hire when Candidate accepts. |
| Hire → Commission Invoice | N:1 | Multiple hires billed on one monthly invoice. |

---

## Candidate Discovery

**Employer searches Candidates**
Employers search/filter candidate profiles by:
- Skills (predefined dropdown, multi-select)
- Location (text search)
- Salary expectations (range)
- Availability (when they can start)
- Experience level (optional, from work history)

Results ranked by relevance and newest-first. Full-text search on profile text supported (PostgreSQL FTS).

---

## Architectural Decisions (ADRs)

See `/docs/adr/` for detailed architectural decision records:

- **[ADR 0001: Profile-as-CV](../docs/adr/0001-profile-as-cv.md)** — Candidates provide structured profile data (skills, work history, education) instead of uploading CV files. Supporting documents (cover letter, portfolio) are optional supplements.

- **[ADR 0002: Invite-Based Hiring (Replaces Mutual Confirmation)](../docs/adr/0002-invite-based-hiring.md)** — Employers send interview invites to candidates (not job postings). Commission is triggered when candidate accepts invite. Simpler flow, no mutual confirmation step.

## Policy Decisions (To Be Determined)

- **Off-platform hiring**: Platform cannot prevent Candidates and Employers from hiring outside the platform. Requires Terms of Service clause and enforcement strategy (flagging, account suspension for repeat abuse).
- **Dispute resolution**: Disputes must be raised within 30 days of hire acceptance. After 30 days, hire is finalized and no disputes/refunds allowed.
- **Interview invite expiry**: Do invites expire after a certain period (e.g., 14 days)? Or do they remain valid indefinitely until accepted/declined?
