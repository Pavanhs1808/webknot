 Campus Event Reporting – Design Document

This document outlines a minimal yet scalable design for the Campus Event Management Platform’s event and program reporting features.

- Event creation
- Student registration
- Attendance
- Feedback (rating 1–5, and feedback)

- Event and student data are scoped by college_id to keep queries fast and to allow multi-tenant separation in the future.

Database Schema (ER)(mermaid style because of time constraint)
  mermaid 
erDiagram
  COLLEGES ||--o{ STUDENTS : has
  COLLEGES ||--o{ EVENTS : hosts
  STUDENTS ||--o{ REGISTRATIONS : makes
  EVENTS ||--o{ REGISTRATIONS : has
  REGISTRATIONS ||--o| ATTENDANCE : records
  REGISTRATIONS ||--o| FEEDBACK : gives

  COLLEGES {
    int id Primary Key
    string name
  }
  STUDENTS {
    int id Primary Key
    int college_id Foreign key
    string name
    string email UNIQUE
  }
  EVENTS {
    int id Primary Key
    int college_id Foreign Key
    string name
    string type
    string date
    int capacity
    string venue
    string description
    string status
  }
  REGISTRATIONS {
    int id Primary Key
    int student_id Foreign Key
    int event_id Foreign Key
    ts ts
    UNIQUE(student_id,event_id)
  }
  ATTENDANCE {
    int id Primary Key
    int registration_id Foreign Key UNIQUE
    int present (0/1)
    ts ts
  }
  FEEDBACK {
    int id Primary Key
    int registration_id Foreign Key UNIQUE
    int rating 1..5
    string comment
    ts ts
  }


API Design
- `POST /colleges` – create college
- `POST /students` – create student
- `POST /events` – create event
- `POST /register` – register student for event
- `POST /attendance` – mark attendance
- `POST /feedback` – submit feedback
- Reports:
  - `GET /reports/event-popularity[?type=&college_id=]`
  - `GET /reports/attendance?event_id=`
  - `GET /reports/feedback?event_id=`
  - `GET /reports/student-participation?student_id=`
  - `GET /reports/top-students[?college_id=&limit=3]`

Workflows (Sequence)
 Registration → Attendance → Reporting
mermaid
sequenceDiagram
  participant Admin
  participant Student
  participant API
  participant DB

  Admin->>API: Create Event
  API->>DB: INSERT events
  Student->>API: Register for Event
  API->>DB: INSERT registrations (UNIQUE student,event)
  Student->>API: Check-in (Attendance)
  API->>DB: UPSERT attendance (present=1/0)
  Student->>API: Submit Feedback (1–5)
  API->>DB: UPSERT feedback
  Admin->>API: Fetch Reports
  API->>DB: Aggregations (JOINs)
  API-->>Admin: Popularity, Attendance %, Avg Rating


Assumptions & Edge Cases
- Duplicate registration prevented via `UNIQUE(student_id,event_id)`.
- Attendance is only recorded for existing registrations.
- Feedback is one per registration; subsequent submissions update the previous one.
- Cancelled events remain in DB with status=`Cancelled` and can be excluded in UI-level filters.
- Multi-tenancy: include `college_id` on entities; queries can filter by college.

 Example SQL (Reports)

Event Popularity
(The events that are given are global and unique)
sql=>

SELECT e.id, e.name, e.type, e.date, COUNT(r.id) AS registrations
FROM events e
LEFT JOIN registrations r ON r.event_id = e.id
GROUP BY e.id
ORDER BY registrations DESC;

Attendance Percentage (per event)
(attendance is calculated using the unique event id)
sql=>

SELECT e.id AS event_id, e.name,
       COUNT(DISTINCT r.id) AS total_registrations,
       SUM(CASE WHEN a.present=1 THEN 1 ELSE 0 END) AS present_count,
       ROUND(100.0 * SUM(CASE WHEN a.present=1 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT r.id),0), 2) AS attendance_percentage
FROM events e
LEFT JOIN registrations r ON r.event_id = e.id
LEFT JOIN attendance a ON a.registration_id = r.id
WHERE e.id = :event_id
GROUP BY e.id;


Average Feedback (per event)
(Feed back can only be given if the student has attended the event if not it will not give)
sql=>

SELECT e.id AS event_id, e.name,
       ROUND(AVG(f.rating), 2) AS avg_rating,
       COUNT(f.id) AS feedback_count
FROM events e
LEFT JOIN registrations r ON r.event_id = e.id
LEFT JOIN feedback f ON f.registration_id = r.id
WHERE e.id = :event_id
GROUP BY e.id;


Student Participation
sql=>

SELECT s.id AS student_id, s.name, COUNT(a.id) AS events_attended
FROM students s
LEFT JOIN registrations r ON r.student_id = s.id
LEFT JOIN attendance a ON a.registration_id = r.id AND a.present=1
WHERE s.id = :student_id
GROUP BY s.id;


Top 3 Most Active Students (by college)
sql=>

SELECT s.id AS student_id, s.name, s.email, COUNT(a.id) AS events_attended
FROM students s
LEFT JOIN registrations r ON r.student_id = s.id
LEFT JOIN attendance a ON a.registration_id = r.id AND a.present=1
WHERE s.college_id = :college_id
GROUP BY s.id
ORDER BY events_attended DESC, s.name ASC
LIMIT 3;

