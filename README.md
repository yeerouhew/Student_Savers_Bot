# Studentsavers Bot

**Proposed Level of Achievement:** Project Gemini

![Image of bot icon]() <br />
Studentsavers bot is a telegram bot which helps NUS students to keep track of their weekly deliverables and also search for 
room availability in the school premises.

**Motivation** 
<br /> <br />
Many students in NUS struggle staying organized and often lose track of assessment's deadlines. Thus, Studentsavers bot can 
help to address this concern by **reminding them the due dates**.   
Instead of search each room physically by walking around different blocks in school, Studentsavers bot can automatically **do 
the searching of room availability** for the students.

**User stories**
<br /> 
1. As a student who does not check Luminus announcements frequently, Studentsavers bot can help to pull out important dates/
deadlines and add it to my Google calendar.
2. As a student who often loses track of my study process, it is rather efficient to have Studentsavers bot to send me a 
reminder message to allow me to be more mindful of assessment and assignment submission dates to prevent missing deadlines.
3. As a student who always spends time studying in between lessons, it is tedious to find an available room by walking 
around and searching each room physically.    
4. As a teaching assistant or professor, I would like to be able to check the schedule of the tutorial room I am using 
so that I do not extend/overshoot my lesson and inconvenience the next group of users for the room.  

**Scope of Project:**
<br /> <br />
The Telegram bot provides a chat-like interface for students to find out academic assessment/assignment deadlines in a single platform. It also offers the convenience of checking deadlines by sending out reminders through scheduled messages and automatically adding the important dates to the Google calendar.  

Besides that, the bot also provides the feature for students to search for empty tutorial rooms within SoC in a particular time frame. Students will have to choose the buildings(COMS1 , COMS2), the level and input the respective time frame (ie, 12pm to 1pm). The bot will process the data and return them a list of empty tutorial rooms within that time frame. 

**Features to be completed**
* by end-June
  1. Unfinished Telegram UI
  2. Integrating Nusmods API to the telegram bot
     * Being able to process data from Nusmods API (venues information)  to telegram
  3. Telegram bot will be able to send out reminder messages to students from the “hard-coded” data from database
* by end-July
  1. Integrating Luminus API to the telegram bot
  2. Telegram bot will be able to allow students to add important dates to Google calendar.
