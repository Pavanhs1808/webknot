Campus Event Management API

Overview:

This project is a minimal Campus Event Reporting API that allows colleges to manage events, student registrations, attendance, and feedback along with providing various reports such as event popularity, attendance percentage, average feedback, student participation, and top students wher there would be many feature like adding adresss and develop a fully fledged web application for the sake of monitoring and adding teh evenys and managing it and ther will be a mobile aplicatin wher student sget to acces the event details and tickets for the event adn get insights whic can hel the campus to manage time and effort.

Now lets break the working of the workflow: \n

-> First the admin create the event with the help of the website which is only accesible for the campus management.

-> Now the student gets notification the=at an event is being hosted and they register for the event.

-> On the event day the student checks by scanning the ticket and thus the database is updated for the students who have scaned the Qr code.

-> After the event the student submits the feedback (1-5).

-> Now the management can generate the repost on how many students have attendded the event and how many have not.

🚀 Run the project The working of the project:

-> check that you have py version 3.10+ installed if not install it

->install dependencies

 pip install -r requirements.txt

->Run the flask server

python app.py

Health check: openhttp://127.0.0.1:5000/healthin a browser.]

Now seedin the data(here i have used postman one can use basuc crul becase ithas inbuilt data base to stire these data) The seedin data is store in the repo as event.js which one can acces to check how it works

Endpoints Tested POST Endpoints

/colleges → Create a college

/students → Create students

/events → Create events

/register → Register students for events

/attendance → Mark student attendance

/feedback → Submit feedback

![Event Popularity] (screenshots/eventpopularity.png)

or check the folder screeshots

GET Reports

/reports/event-popularity → Event popularity (registrations)

/reports/attendance?event_id=1 → Attendance % for Intro to ML

/reports/feedback?event_id=1 → Average feedback for Intro to ML

/reports/student-participation?student_id=1 → Participation for Pavan HS

/reports/top-students?college_id=1&limit=3 → Top 3 active students

Dcreen shots are in the folder  screenshots

->then implementing an web application that daels directly with i sapi request where ione acn register the events(===>>>screenshot in screeshot folder<<<====)