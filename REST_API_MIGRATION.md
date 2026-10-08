# REST API Migration Guide

## Overview
Migrating from action-based URLs to REST-compliant state-based endpoints using PATCH requests and context-aware authentication.

---

## Key Changes

### 1. **Context-Aware Profiles** (No `/me` endpoint)

| Operation | Old Endpoint | New Endpoint | Method | Notes |
|-----------|-------------|-------------|--------|-------|
| Get own profile | `/api/candidates/profile/` | `/api/profiles` | GET | Returns authenticated user's profile |
| Get other's profile | `/api/candidates/<id>/profile/` | `/api/candidates/<id>` | GET | Public profile view |
| Update own profile | `PATCH /api/candidates/profile/` | `PATCH /api/profiles` | PATCH | Updates authenticated user's profile |

### 2. **Action Endpoints → State Changes (PATCH)**

#### Profile Status Changes
```diff
- POST /api/profiles/<id>/pause       → PATCH /api/profiles {"status": "paused"}
- POST /api/profiles/<id>/unpause     → PATCH /api/profiles {"status": "active"}
- POST /api/candidates/profile/publish/ → PATCH /api/profiles {"status": "published"}
- POST /api/candidates/profile/revert/  → PATCH /api/profiles {"status": "draft"}
- POST /api/profiles/<id>/delete      → DELETE /api/profiles
```

#### Job Status Changes
```diff
- POST /api/employer/jobs/<id>/publish   → PATCH /api/employer/jobs/<id> {"status": "published"}
- POST /api/employer/jobs/<id>/close     → PATCH /api/employer/jobs/<id> {"status": "closed"}
- POST /api/employer/jobs/<id>/unpublish → PATCH /api/employer/jobs/<id> {"status": "draft"}
```

#### Application Status Changes
```diff
- POST /api/employer/applications/<id>/mark-hired → PATCH /api/employer/applications/<id> {"status": "hired"}
```

### 3. **Search Endpoints → Query Parameters**

```diff
- GET /api/candidates/search?location=London&skills=React
+ GET /api/candidates?location=London&skills=React
```

### 4. **Payment Endpoints**

```diff
- POST /api/employer/invoices/<id>/pay
+ POST /api/employer/invoices/<id>/payments
```

Creates a payment resource instead of an action.

### 5. **Sub-Resource Consolidation**

#### Simplified paths for own profile
```diff
- /api/candidates/profile/work-history/
+ /api/profiles/work-history

- /api/candidates/profile/education/
+ /api/profiles/education

- /api/candidates/profile/links/
+ /api/profiles/links

- /api/profiles/<id>/skills
+ /api/profiles/skills (own only)
```

---

## Complete REST API Structure

### **CANDIDATES (Public)** 
```
GET    /api/candidates                    # Search with ?location=...&skills=...
GET    /api/candidates/<id>               # View public profile
```

### **PROFILES (Own Profile)**
```
GET    /api/profiles                      # Get own profile (context-aware)
POST   /api/profiles                      # Create profile (if new)
PATCH  /api/profiles                      # Update own profile (including status)
DELETE /api/profiles                      # Delete own profile

GET    /api/profiles/skills               # List own skills
POST   /api/profiles/skills               # Add skill
PATCH  /api/profiles/skills/<id>          # Update skill

GET    /api/profiles/work-history         # List own work history
POST   /api/profiles/work-history         # Add work history
PATCH  /api/profiles/work-history/<id>    # Update work history
DELETE /api/profiles/work-history/<id>    # Delete work history

GET    /api/profiles/education            # List own education
POST   /api/profiles/education            # Add education
PATCH  /api/profiles/education/<id>       # Update education
DELETE /api/profiles/education/<id>       # Delete education

GET    /api/profiles/links                # List own links
POST   /api/profiles/links                # Add link
PATCH  /api/profiles/links/<id>           # Update link
DELETE /api/profiles/links/<id>           # Delete link

GET    /api/profiles/availability         # Get own availability
PATCH  /api/profiles/availability         # Update availability
```

### **EMPLOYER PROFILE & TEAM**
```
GET    /api/employer/profile              # Get own employer profile
PATCH  /api/employer/profile              # Update own employer profile

GET    /api/employer/team-members         # List team
POST   /api/employer/team-members         # Add team member
PATCH  /api/employer/team-members/<id>    # Update team member
DELETE /api/employer/team-members/<id>    # Remove team member
```

### **JOBS**
```
GET    /api/employer/jobs                 # List own jobs
POST   /api/employer/jobs                 # Create job
GET    /api/employer/jobs/<id>            # Get job details
PATCH  /api/employer/jobs/<id>            # Update job (including status: draft/published/closed)
DELETE /api/employer/jobs/<id>            # Delete job
GET    /api/employer/jobs/<id>/metrics    # Get job metrics
```

### **SHORTLISTS**
```
GET    /api/employer/shortlists           # List shortlists
POST   /api/employer/shortlists           # Create shortlist
GET    /api/employer/shortlists/<id>      # Get shortlist
PATCH  /api/employer/shortlists/<id>      # Update shortlist
DELETE /api/employer/shortlists/<id>      # Delete shortlist
```

### **APPLICATIONS**
```
GET    /api/employer/applications         # List applications (with filters)
GET    /api/employer/applications/<id>    # Get application details
PATCH  /api/employer/applications/<id>    # Update application (including status: hired/rejected/reviewed)
```

### **APPLICATION SHORTLISTS**
```
GET    /api/employer/application-shortlists      # List
POST   /api/employer/application-shortlists      # Create
GET    /api/employer/application-shortlists/<id> # Get
PATCH  /api/employer/application-shortlists/<id> # Update
DELETE /api/employer/application-shortlists/<id> # Delete
```

### **COMMISSIONS**
```
GET    /api/employer/commissions          # List (with filters)
GET    /api/employer/commissions/<id>     # Get details
PATCH  /api/employer/commissions/<id>     # Update (including dispute status)
```

### **INVOICES**
```
GET    /api/employer/invoices             # List
GET    /api/employer/invoices/<id>        # Get details
PATCH  /api/employer/invoices/<id>        # Update status
POST   /api/employer/invoices/<id>/payments  # Create payment
```

### **PAYMENTS**
```
GET    /api/employer/payments             # List
GET    /api/employer/payments/<id>        # Get details
```

---

## Frontend Migration Examples

### Before (Action-based)
```javascript
// Profile status change
await api.post('/api/profiles/123/pause');
await api.post('/api/candidates/profile/publish/');

// Job publishing
await api.post('/api/employer/jobs/5/publish');

// Payment
await api.post('/api/employer/invoices/3/pay');
```

### After (State-based PATCH)
```javascript
// Profile status change
await api.patch('/api/profiles', { status: 'paused' });
await api.patch('/api/profiles', { status: 'published' });

// Job publishing
await api.patch('/api/employer/jobs/5', { status: 'published' });

// Payment (creates payment resource)
await api.post('/api/employer/invoices/3/payments', { amount: 1000, ... });
```

---

## Implementation Checklist

- [ ] Update URL routes in `config/urls.py` and `employers/urls.py`
- [ ] Create/update views to handle PATCH for state changes
- [ ] Remove action-specific views (PauseView, UnpauseView, PublishView, etc.)
- [ ] Update ProfileDetailView to handle context-aware own/other profile logic
- [ ] Update all serializers to accept `status` field for state changes
- [ ] Update frontend API calls to use new endpoints
- [ ] Update API documentation
- [ ] Write migration guide for API consumers
- [ ] Add tests for PATCH state change endpoints
- [ ] Update Postman/API client collections

---

## Benefits

✅ **True REST compliance** - Uses HTTP methods correctly  
✅ **Reduced URL surface** - No special action endpoints  
✅ **Consistent patterns** - All state changes via PATCH  
✅ **Better semantics** - URLs represent resources, not actions  
✅ **Simpler versioning** - Fewer endpoints to maintain  
✅ **Standard practices** - Follows GitHub, GitLab, AWS patterns
