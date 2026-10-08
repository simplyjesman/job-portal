# Local Docker Testing Guide

This guide explains how to test the Docker setup on your local machine.

## Prerequisites

1. **Docker Desktop** - Download from https://www.docker.com/products/docker-desktop
   - Includes Docker and Docker Compose
   - Available for Mac, Windows, and Linux
   - Minimum 4GB RAM recommended

2. **Verify Installation**
   ```bash
   docker --version
   docker-compose --version
   docker info
   ```

## Quick Test (Automated)

The easiest way to test is using the provided test script:

```bash
cd job-portal
./test-docker-local.sh
```

This script will:
- ✓ Verify Docker installation
- ✓ Build Docker images
- ✓ Start containers (database + web)
- ✓ Run health checks
- ✓ Test database connectivity
- ✓ Run test suite
- ✓ Generate a report

### Expected Output

```
🧪 Job Portal Docker Local Test
================================

Checking Docker installation... ✓ OK
Checking Docker Compose installation... ✓ OK
Checking Docker daemon... ✓ OK

📦 Docker Build Test
-------------------
Building Docker images... ✓ OK

🚀 Starting Containers
---------------------
Starting database container... ✓ Started
Waiting for database to be healthy... ✓ Ready
Starting web application container... ✓ Started
Waiting for web application to start... ✓ Ready

✅ Container Status
-------------------
NAME              STATUS
job_portal_db     Up (healthy)
job_portal_app    Up

🔍 Health Checks
----------------
Database connection... ✓ OK
API endpoint... ✓ OK
Admin panel... ✓ OK

📊 Database Check
-----------------
Checking migrations... ✓ OK (45 lines)
Counting database tables... ✓ OK (12 tables)

🧪 Running Tests
----------------
Running pytest... ✓ PASSED (42 passed in 3.45s)

================================
✅ All tests passed!
================================
```

## Manual Testing

### 1. Start the Application

```bash
docker-compose up --build
```

Wait for output like:
```
job_portal_app    | [2026-10-07 10:30:00 +0000] [42] [INFO] Listening at: http://0.0.0.0:8000 (42)
```

### 2. Create Admin User (New Terminal)

```bash
docker-compose exec web python manage.py createsuperuser
```

Follow prompts:
```
Email: admin@example.com
Password: (enter password)
Password (again): (confirm)
```

### 3. Access the Application

**API**: http://localhost:8000/api/
**Admin**: http://localhost:8000/admin

Login with the credentials created in step 2.

### 4. Test API Endpoints

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-password"
  }'
```

Expected response:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "admin@example.com"
  }
}
```

**Create Profile:**
```bash
curl -X POST http://localhost:8000/api/profiles/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "headline": "Software Engineer"
  }'
```

## Advanced Testing

### Run Full Test Suite

```bash
docker-compose exec web pytest -v
```

### Run Specific Test File

```bash
docker-compose exec web pytest accounts/tests.py -v
```

### Run Tests with Coverage

```bash
docker-compose exec web pytest --cov=accounts --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Database Access

Connect directly to PostgreSQL:

```bash
docker-compose exec db psql -U postgres -d job_portal
```

Useful commands:
```sql
\dt                    -- List tables
\d table_name          -- Describe table
SELECT COUNT(*) FROM users;
\q                     -- Exit
```

### View Logs

All services:
```bash
docker-compose logs -f
```

Specific service:
```bash
docker-compose logs -f web    # Django
docker-compose logs -f db     # PostgreSQL
```

Recent logs (last 100 lines):
```bash
docker-compose logs --tail=100 web
```

### Performance Monitoring

Check resource usage:
```bash
docker stats
```

Expected usage:
- Memory: 300-500 MB
- CPU: < 5% at idle

### Interactive Django Shell

```bash
docker-compose exec web python manage.py shell

>>> from accounts.models import User
>>> User.objects.count()
```

## Troubleshooting

### Port Already in Use

If port 8000 or 5432 is in use:

```bash
# Find process using port
lsof -i :8000

# Kill process (macOS/Linux)
kill -9 <PID>

# Or change port in docker-compose.yml:
# ports:
#   - "8001:8000"
```

### Database Connection Failed

```bash
# Check database status
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Web Application Won't Start

```bash
# Check web logs
docker-compose logs web

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Permission Issues (Linux)

Add your user to docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Out of Disk Space

Clean up Docker resources:
```bash
docker system prune -a
```

## Testing Checklist

After running tests, verify:

- [ ] Docker builds without errors
- [ ] PostgreSQL container starts
- [ ] Django migrations run automatically
- [ ] Web server accessible at localhost:8000
- [ ] Admin panel loads at localhost:8000/admin
- [ ] Can create superuser account
- [ ] Can login via API
- [ ] Database stores data correctly
- [ ] All tests pass
- [ ] No permission errors

## CI/CD Integration

The Docker setup is ready for CI/CD:

```bash
# GitHub Actions example
docker-compose build
docker-compose run web pytest
docker-compose down
```

## Environment Variables

To test with custom settings, create `.env`:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,web
DB_NAME=job_portal_test
DB_USER=postgres
DB_PASSWORD=test_password_123
```

Then run:
```bash
docker-compose up
```

## Next Steps

After successful testing:

1. **Review logs** - Ensure no warnings or errors
2. **Run test suite** - Verify all tests pass
3. **Test API endpoints** - Confirm functionality
4. **Check database** - Verify data persistence
5. **Deploy to production** - Use tested configuration

## Resources

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/4.2/howto/deployment/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)

---

**Test Status**: ✅ Ready for testing  
**Last Updated**: 2026-10-07
