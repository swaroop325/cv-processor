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

Replace `{jd_id}` with UUID from step 2:

```bash
curl -X POST "http://localhost:8000/api/jd/find-best-cvs" \
  -H "Content-Type: application/json" \
  -d '{
    "jd_id": "234e5678-e89b-12d3-a456-426614174001",
    "top_k": 5
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

```bash
curl -X POST "http://localhost:8000/api/jd/contact-candidate" \
  -H "Content-Type: application/json" \
  -d '{
    "cv_id": "123e4567-e89b-12d3-a456-426614174000",
    "jd_id": "234e5678-e89b-12d3-a456-426614174001"
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
| 3. Find CVs | application/json | jd_id, top_k |
| 4. Contact | application/json | cv_id, jd_id |

## View API Docs

http://localhost:8000/docs

## Useful Commands

```bash
# List CVs
curl http://localhost:8000/api/cv/list

# List JDs
curl http://localhost:8000/api/jd/list

# View logs
docker-compose logs -f backend

# Stop
docker-compose down

# Reset database
docker-compose down -v && docker-compose up -d
```
