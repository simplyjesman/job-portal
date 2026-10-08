# Migration & Testing Commands

Since the sandboxed environment lacks Python and Docker Compose, run these commands locally.

## Database Migrations

After pulling the latest code, run migrations to create new tables for the Candidate Profile feature:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### New Models Created
- `ExternalLink` — GitHub, LinkedIn, portfolio links
- Updated `CandidateProfile` — headline, photo, profile_status, published_at
- Updated `WorkHistory` — M2M relationship to Skill

## Testing Locally

### Option 1: Direct Python (Recommended for Quick Testing)

```bash
cd backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run tests
python manage.py test

# Run specific app tests
python manage.py test profiles

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Opens htmlcov/index.html in browser
```

### Option 2: Docker (Full Environment)

```bash
# Run the automated test script
./test-docker-local.sh

# Or manually with docker-compose
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py test
docker-compose down
```

### Option 3: Using test_api.sh Script

For API integration testing without running full Django tests:

```bash
# Start backend server locally (in backend directory with venv activated)
python manage.py runserver

# In another terminal, run the test script
./test_api.sh
```

## Manual Testing Checklist

### Candidate Profile Creation & Publishing

1. **Signup as Candidate**
   - Sign up with candidate user type
   - Redirect to dashboard

2. **Edit Profile (Draft Mode)**
   - Navigate to "My Profile"
   - Click "Edit Profile" button
   - Fill in:
     - Headline (required, e.g., "Senior Backend Engineer, 8 years")
     - Location (required)
     - Notice period (required dropdown)
     - Add work experience (required, at least 1)
       - Add job title, company, dates, description, skills
       - Mark "current" job if applicable
     - Add education (optional)
       - Add degree, school, field, graduation year
     - Add external links (optional)
       - GitHub, LinkedIn, portfolio
   - Save changes

3. **Publish Profile (Go Live)**
   - Click "Make Live" button
   - Verify required fields check passes
   - Profile status changes to "Live"
   - Publication date displayed

4. **View Profile as Candidate (Live)**
   - Profile is read-only
   - Edit buttons hidden
   - "Make Draft" button visible (if no interviews)

5. **Employer Views Profile**
   - Signup as Employer
   - Search candidates
   - Click "View Profile" on a candidate card
   - See live profile (read-only, no edit controls)
   - See publication date
   - See work timeline, education, links

6. **Revert Profile to Draft**
   - Go back to own profile
   - Click "Make Draft"
   - Confirm: should only work if NO in-progress interviews
   - Profile returns to draft, editable

### Experience Level Calculation

Verify auto-calculated experience levels appear correctly:
- **Junior** (0-2 years): Light blue badge
- **Mid** (2-5 years): Purple badge
- **Senior** (5-10 years): Amber badge
- **Lead** (10+ years): Red badge

### Work History Timeline

- Current jobs appear at top with "Current" badge
- Past jobs reverse-chronological
- Skills displayed per job
- Dates formatted correctly (e.g., "Sep 2020 – Present")

### External Links

- GitHub links formatted as `https://github.com/{username}`
- LinkedIn links formatted as `https://linkedin.com/in/{username}`
- Portfolio links use as-is
- All links are clickable and open in new tab

## Expected Test Results

After running `python manage.py test`, you should see:
```
Ran X tests in X.XXXs
OK
```

Or with coverage:
```
Name                          Stmts   Miss  Cover
------------------------------------------------
profiles/models.py                50      0   100%
profiles/serializers.py           80      2    97%
profiles/views.py                 120     5    96%
...
```

## Troubleshooting

**Migration Fails: "Table already exists"**
- Delete your local SQLite database (`db.sqlite3`)
- Rerun: `python manage.py migrate`

**Import Errors in profile_views.py**
- Make sure `profiles` app is in `INSTALLED_APPS` in settings.py
- Check that `jobs` app is installed (needed for InterviewInvite)

**Frontend Routes Not Found**
- Verify ProfilePage component is imported in App.tsx
- Check that routes are added: `/profile` and `/profile/:id`

**Frontend API Calls Fail (404)**
- Verify backend API endpoints are registered in `config/urls.py`
- Check Django development server is running on `http://localhost:8000`

## Performance Notes

- Profile queries use `.select_related()` and `.prefetch_related()` for work history, education, links
- Experience level is calculated in-memory (no DB query)
- Profile serializers only include necessary fields to reduce payload size

---

**Next:** Once migrations pass locally, commit the migration files and deploy to production following your CD pipeline.
