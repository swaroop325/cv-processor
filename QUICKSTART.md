# Quick Start Guide

## Start the Backend

```bash
docker-compose up -d
```

Check health:
```bash
curl http://localhost:8000/health
```

## Test the 4 APIs

### 1. Upload CV (Multipart - File Only)

Just upload the file - everything is extracted automatically!

```bash
curl -X POST "http://localhost:8000/api/cv/upload" \
  -F "file=@resume.pdf"
```

Response:
```json
{
  "id": "123e4567-...",
  "candidate_name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+1234567890",
  "skills": ["Python", "FastAPI"],
  "summary": "Experienced developer...",
  "embedding_generated": true
}
```

### 2. Create JD (JSON - Title + Requirements)

```bash
curl -X POST "http://localhost:8000/api/jd/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "requirements": "5+ years Python, FastAPI, PostgreSQL, Docker, AWS"
  }'
```

Response:
```json
{
  "id": "234e5678-...",
  "title": "Senior Python Developer",
  "requirements": "5+ years Python, FastAPI...",
  "embedding_generated": true
}
```

### 3. List JDs (Optional Query Params)

Get all job descriptions with optional filtering:

```bash
# Basic list (returns all active JDs)
curl "http://localhost:8000/api/jd/list"

# With search
curl "http://localhost:8000/api/jd/list?search=Python"

# With pagination
curl "http://localhost:8000/api/jd/list?skip=0&limit=10"

# Include inactive JDs
curl "http://localhost:8000/api/jd/list?active_only=false"
```

Response:
```json
[
  {
    "id": "234e5678-e89b-12d3-a456-426614174001",
    "title": "Senior Python Developer",
    "company": "Our Company",
    "department": null,
    "location": null,
    "description": "5+ years Python, FastAPI, PostgreSQL, Docker, AWS",
    "requirements": "5+ years Python, FastAPI, PostgreSQL, Docker, AWS",
    "responsibilities": null,
    "required_skills": null,
    "preferred_skills": null,
    "benefits": null,
    "employment_type": null,
    "experience_level": null,
    "salary_range": null,
    "is_active": true,
    "embedding_generated": true,
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00"
  }
]
```

### 4. List CVs (Optional Query Params)

Get all uploaded CVs with optional filtering:

```bash
# Basic list (returns all CVs)
curl "http://localhost:8000/api/cv/list"

# With search (by name or email)
curl "http://localhost:8000/api/cv/list?search=Jane"

# With pagination
curl "http://localhost:8000/api/cv/list?skip=0&limit=10"
```

Response:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "candidate_name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+1234567890",
    "raw_text": "Full CV text content...",
    "summary": "Experienced developer with 5+ years...",
    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
    "experience": {...},
    "education": {...},
    "file_name": "resume.pdf",
    "file_type": "pdf",
    "embedding_generated": true,
    "created_at": "2025-01-15T09:30:00",
    "updated_at": "2025-01-15T09:30:00"
  }
]
```

### 5. Find Best CVs (JSON)

Use the job title from step 2 or from the list response:

```bash
curl -X POST "http://localhost:8000/api/jd/find-best-cvs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Senior Python Developer"
  }'
```

Note: `top_k` is optional and defaults to 5. You can override it:

```bash
curl -X POST "http://localhost:8000/api/jd/find-best-cvs" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Senior Python Developer",
    "top_k": 10
  }'
```

Response:
```json
[
  {
    "cv": {
      "id": "123e4567-...",
      "candidate_name": "Jane Smith",
      "email": "jane@example.com",
      ...
    },
    "similarity_score": 0.87
  }
]
```

### 6. Contact Candidate (JSON)

Use candidate name and job title:

```bash
curl -X POST "http://localhost:8000/api/jd/contact-candidate" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "Jane Smith",
    "job_title": "Senior Python Developer"
  }'
```

Response:
```json
{
  "message": "Acceptance email sent successfully",
  "candidate_email": "jane@example.com",
  "candidate_name": "Jane Smith",
  "job_title": "Senior Python Developer"
}
```

## API Summary

| API | Content-Type | Input |
|-----|--------------|-------|
| 1. Upload CV | multipart/form-data | file only |
| 2. Create JD | application/json | title, requirements |
| 3. List JDs | none | query params: search, skip, limit, active_only |
| 4. List CVs | none | query params: search, skip, limit |
| 5. Find Best CVs | application/json | job_title, top_k (optional, default: 5) |
| 6. Contact Candidate | application/json | candidate_name, job_title |

## View API Docs

http://localhost:8000/docs

## Useful Commands

```bash
# List CVs
curl http://localhost:8000/api/cv/list

# List JDs
curl http://localhost:8000/api/jd/list

# Clear all records from CV and JD tables
./clear_database.sh

# View logs
docker-compose logs -f backend

# Stop
docker-compose down

# Reset database (removes all data and volumes)
docker-compose down -v && docker-compose up -d
```
