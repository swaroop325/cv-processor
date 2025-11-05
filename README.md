# CV Processing Backend

A FastAPI backend for processing CVs and matching them with Job Descriptions using vector similarity search.

## Features

- **Upload CV**: Upload PDF/DOCX - automatically extracts name, email, phone, skills
- **Create JD**: Add job with title and requirements - generates embeddings
- **Find Matches**: Find top matching CVs using pgvector cosine similarity
- **Contact Candidate**: Send automated acceptance emails
- **Secured**: All endpoints require SECRET_KEY authentication

## Quick Start

```bash
docker-compose up -d
```

Access: http://localhost:8000/docs

**Important**: Set `SECRET_KEY` in docker-compose.yml before deploying to production!

## Authentication

**All API endpoints require authentication via header:**

```
X-Secret-Key: your-secret-key-here
```

The SECRET_KEY is configured in:
- `docker-compose.yml` (for Docker)
- `.env` file (for local development)

**Without the correct SECRET_KEY, all requests will return 401 Unauthorized.**

## API Endpoints

### 1. Upload CV
```bash
POST /api/cv/upload
Content-Type: multipart/form-data
X-Secret-Key: your-secret-key
```

**Request**:
- `file`: CV file (PDF or DOCX)

**Example**:
```bash
curl -X POST "http://localhost:8000/api/cv/upload" \
  -H "X-Secret-Key: my-super-secret-key-change-in-production" \
  -F "file=@resume.pdf"
```

---

### 2. Create Job Description
```bash
POST /api/jd/create
Content-Type: application/json
X-Secret-Key: your-secret-key
```

**Request**:
```json
{
  "title": "Senior Python Developer",
  "requirements": "5+ years Python, FastAPI, PostgreSQL, Docker"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/jd/create" \
  -H "Content-Type: application/json" \
  -H "X-Secret-Key: my-super-secret-key-change-in-production" \
  -d '{"title":"Senior Python Developer","requirements":"5+ years Python"}'
```

---

### 3. Find Best CVs
```bash
POST /api/jd/find-best-cvs
Content-Type: application/json
X-Secret-Key: your-secret-key
```

**Request**:
```json
{
  "jd_id": "uuid-here",
  "top_k": 10
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/jd/find-best-cvs" \
  -H "Content-Type: application/json" \
  -H "X-Secret-Key: my-super-secret-key-change-in-production" \
  -d '{"jd_id":"YOUR_JD_UUID","top_k":5}'
```

---

### 4. Contact Candidate
```bash
POST /api/jd/contact-candidate
Content-Type: application/json
X-Secret-Key: your-secret-key
```

**Request**:
```json
{
  "cv_id": "uuid-here",
  "jd_id": "uuid-here"
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/jd/contact-candidate" \
  -H "Content-Type: application/json" \
  -H "X-Secret-Key: my-super-secret-key-change-in-production" \
  -d '{"cv_id":"YOUR_CV_UUID","jd_id":"YOUR_JD_UUID"}'
```

---

### 5. Health Check
```bash
GET /health
X-Secret-Key: your-secret-key
```

**Example**:
```bash
curl -H "X-Secret-Key: my-super-secret-key-change-in-production" \
  http://localhost:8000/health
```

## Summary

| API | Method | Content-Type | Auth | Input |
|-----|--------|--------------|------|-------|
| Upload CV | POST /api/cv/upload | multipart/form-data | Required | file only |
| List CVs | GET /api/cv/list | - | Required | pagination |
| Create JD | POST /api/jd/create | application/json | Required | title, requirements |
| List JDs | GET /api/jd/list | - | Required | pagination |
| Find CVs | POST /api/jd/find-best-cvs | application/json | Required | jd_id, top_k |
| Contact | POST /api/jd/contact-candidate | application/json | Required | cv_id, jd_id |
| Health | GET /health | - | Required | none |

**All endpoints require `X-Secret-Key` header!**

## Configuration

### SECRET_KEY (Required)

Set in `docker-compose.yml`:
```yaml
environment:
  - SECRET_KEY=your-strong-secret-key-here
```

Or in `.env` for local development:
```env
SECRET_KEY=your-strong-secret-key-here
```

**Generate a strong SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Tech Stack

- **FastAPI**: Web framework
- **PostgreSQL + pgvector**: Vector search
- **sentence-transformers**: Text embeddings
- **pdfplumber + python-docx**: CV processing

## Docker Commands

```bash
# Start
docker-compose up -d

# Logs
docker-compose logs -f backend

# Stop
docker-compose down

# Reset
docker-compose down -v && docker-compose up -d
```

## CV Auto-Parsing

Automatically extracts from uploaded CVs:
- Name
- Email
- Phone
- Skills
- Summary

## License

MIT
