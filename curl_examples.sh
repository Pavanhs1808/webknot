# Sample cURL commands to test the API (run after starting the Flask app)
# Start server:  python app.py

# 1) Create a college
curl -X POST http://127.0.0.1:5000/colleges -H "Content-Type: application/json" -d "{\"name\":\"ABC Institute\"}"

# 2) Create students
curl -X POST http://127.0.0.1:5000/students -H "Content-Type: application/json" -d "{\"college_id\":1,\"name\":\"Pavan HS\",\"email\":\"pavan@example.com\"}"
curl -X POST http://127.0.0.1:5000/students -H "Content-Type: application/json" -d "{\"college_id\":1,\"name\":\"Riya\",\"email\":\"riya@example.com\"}"

# 3) Create events
curl -X POST http://127.0.0.1:5000/events -H "Content-Type: application/json" -d "{\"college_id\":1,\"name\":\"Intro to ML\",\"type\":\"Workshop\",\"date\":\"2025-09-21\",\"capacity\":100,\"venue\":\"Auditorium\",\"description\":\"Basics of ML\"}"
curl -X POST http://127.0.0.1:5000/events -H "Content-Type: application/json" -d "{\"college_id\":1,\"name\":\"Hackathon 1\",\"type\":\"Hackathon\",\"date\":\"2025-10-05\",\"capacity\":200,\"venue\":\"Lab-1\",\"description\":\"24h hack\"}"

# 4) Register students
curl -X POST http://127.0.0.1:5000/register -H "Content-Type: application/json" -d "{\"student_id\":1,\"event_id\":1}"
curl -X POST http://127.0.0.1:5000/register -H "Content-Type: application/json" -d "{\"student_id\":2,\"event_id\":1}"
curl -X POST http://127.0.0.1:5000/register -H "Content-Type: application/json" -d "{\"student_id\":1,\"event_id\":2}"

# 5) Mark attendance
curl -X POST http://127.0.0.1:5000/attendance -H "Content-Type: application/json" -d "{\"student_id\":1,\"event_id\":1,\"present\":true}"
curl -X POST http://127.0.0.1:5000/attendance -H "Content-Type: application/json" -d "{\"student_id\":2,\"event_id\":1,\"present\":false}"
curl -X POST http://127.0.0.1:5000/attendance -H "Content-Type: application/json" -d "{\"student_id\":1,\"event_id\":2,\"present\":true}"

# 6) Submit feedback
curl -X POST http://127.0.0.1:5000/feedback -H "Content-Type: application/json" -d "{\"student_id\":1,\"event_id\":1,\"rating\":5,\"comment\":\"Great!\"}"
curl -X POST http://127.0.0.1:5000/feedback -H "Content-Type: application/json" -d "{\"student_id\":2,\"event_id\":1,\"rating\":3,\"comment\":\"OK\"}"

# 7) Reports
curl "http://127.0.0.1:5000/reports/event-popularity"
curl "http://127.0.0.1:5000/reports/event-popularity?type=Workshop&college_id=1"
curl "http://127.0.0.1:5000/reports/attendance?event_id=1"
curl "http://127.0.0.1:5000/reports/feedback?event_id=1"
curl "http://127.0.0.1:5000/reports/student-participation?student_id=1"
curl "http://127.0.0.1:5000/reports/top-students?college_id=1&limit=3"
