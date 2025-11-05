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

### 3. Find Best CVs (JSON)

Use the job title from step 2:

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

### 4. Contact Candidate (JSON)

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
| 3. Find CVs | application/json | job_title, top_k (optional, default: 5) |
| 4. Contact | application/json | candidate_name, job_title |

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
