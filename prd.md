# Product Requirements Document (PRD)

# HireLens – AI Resume Screening Assistant (MVP)

## 1. Overview

HireLens is an AI-powered resume screening platform that helps recruiters quickly identify the most suitable candidates for a job opening.

Instead of manually reviewing every resume, recruiters create a job posting, upload multiple resumes, and receive a ranked list of candidates based on how well they match the job requirements. The AI extracts and summarizes information from resumes, while the backend performs objective scoring and ranking.

The goal of the MVP is to reduce the time spent on initial resume screening while providing transparent and explainable candidate rankings.

---

# 2. Problem Statement

Recruiters and hiring managers often receive dozens or even hundreds of resumes for a single position. Manually reviewing every resume is time-consuming, repetitive, and can lead to inconsistent evaluations.

There is a need for a system that can automatically analyze resumes, compare them against job requirements, and present recruiters with a prioritized list of candidates while explaining why each candidate received their score.

---

# 3. Goals

The MVP should allow recruiters to:

- Create a job opening.
- Define required and preferred skills.
- Upload multiple resumes.
- Automatically extract candidate information.
- Compare each resume against job requirements.
- Rank candidates based on objective criteria.
- Display an explanation of each candidate's score.

---

# 4. Target Users

- HR Teams
- Recruiters
- Startup Founders
- Small and Medium Businesses
- Hiring Managers

---

# 5. Core Features

## 5.1 Create Job

Recruiters can create a new job posting by providing:

- Job Title
- Job Description
- Required Skills
- Preferred Skills
- Minimum Years of Experience

Example:

Job Title:
Backend Developer

Required Skills:
- Python
- FastAPI
- PostgreSQL

Preferred Skills:
- Redis
- Docker

Minimum Experience:
2 Years

---

## 5.2 Upload Resumes

Recruiters can upload multiple resumes for a specific job.

Supported file types:

- PDF
- DOCX

The system should support bulk uploads.

---

## 5.3 Resume Processing

For every uploaded resume, the system should extract:

- Candidate Name
- Contact Information
- Skills
- Work Experience
- Education
- Certifications
- Projects
- Technologies Used

The extracted information should be stored in the database for future searches and analysis.

---

## 5.4 Candidate Matching

The backend compares every candidate against the job requirements.

Matching should consider:

- Required Skills
- Preferred Skills
- Years of Experience

Each candidate receives a score out of 100.

Example scoring:

- Required Skills: 50%
- Experience: 30%
- Preferred Skills: 20%

The scoring algorithm should be implemented in the backend instead of relying solely on AI.

---

## 5.5 Candidate Ranking

After processing, candidates are displayed in descending order based on their overall score.

Example:

1. John Doe — 92%
2. Sarah Ali — 86%
3. Ahmed Khan — 74%

---

## 5.6 Candidate Details

Clicking on a candidate should display:

- Overall Match Score
- Extracted Skills
- Experience Summary
- Education
- Missing Required Skills
- AI-generated Summary

Example:

Overall Score: 91%

Strengths:
- Python
- FastAPI
- PostgreSQL

Missing Skills:
- Docker

Summary:
Experienced backend developer with strong API development experience and relevant database knowledge.

---

# 6. User Flow

Recruiter Login

↓

Create Job

↓

Upload Resumes

↓

Resume Processing

↓

Information Extraction

↓

Candidate Scoring

↓

Candidate Ranking

↓

Candidate Details

---

# 7. Technology Stack

Frontend:
- React

Backend:
- FastAPI

Database:
- PostgreSQL

Background Tasks:
- Celery
- Redis

Resume Parsing:
- PyMuPDF
- python-docx

AI Provider:
- OpenRouter Free Models

---

# 8. Non-Functional Requirements

- Resume processing should happen asynchronously.
- The system should support at least 50 resumes per upload.
- Candidate rankings should be generated within a reasonable time.
- Resume data should be securely stored.
- Duplicate resume uploads should be handled gracefully.

---

# 9. Future Enhancements

- Candidate comparison
- Resume search
- Interview question generation
- Candidate filtering
- Email shortlisted candidates
- AI chat with candidate profiles
- Resume version history
- Recruiter dashboard
- Export shortlisted candidates
- Multi-company support
- Team collaboration

---

# 10. Out of Scope (MVP)

The following features are intentionally excluded from the first version:

- Applicant Tracking System (ATS)
- LinkedIn Integration
- Email Automation
- Interview Scheduling
- Multi-Tenant Organizations
- Video Interviews
- Automatic Hiring Decisions
- Payroll Integration

---

# 11. Success Criteria

The MVP will be considered successful if a recruiter can:

1. Create a job opening.
2. Upload multiple resumes.
3. Automatically process resumes.
4. View ranked candidates.
5. Understand why each candidate received their score.
6. Shortlist the best candidates in minutes instead of manually reviewing every resume.

---

# 12. MVP Summary

HireLens is an AI-assisted resume screening platform designed to simplify the first stage of recruitment. Recruiters define job requirements, upload candidate resumes, and receive an explainable ranked shortlist based on objective matching criteria. The AI is responsible for extracting and summarizing resume information, while the backend handles scoring and ranking to ensure consistent, transparent, and reliable results.