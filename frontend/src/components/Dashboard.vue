<!--Created by: John Montesa-->
<!-- This is student dashboard page for Course Compass -->
<!-- This page will contain student information about their schedule including courses they have
today and tomorrow, specific notifications and deadlines from their school or instructors, they can 
turn on email notifications for these or create custom deadlines and notifications. 
They can also see course details they are enrolled in and unenroll in them-->

<template>
<div v-if="userType ==='Student'">
    <br>
    <!-- Welcome Text -->
    <div class="top-container">
        <v-row v-if="user && user.firstname">
            <h1 class="welcome-text">
                Welcome, {{ user.firstname }}
            </h1>
        </v-row>
    </div>

    <v-container class="dashboard-container">
        <v-row>
            <!-- Display of courses today and tomorrow for student's schedule -->
            <v-col>
                <p>Today: {{ currentDate }}</p>
                <v-container class="upcoming-container">
                    <p>Classes Today:</p>

                    <v-container class="class-block">
                        <v-row class="class-rows" no-gutters v-for="(course, index) in retrieveSchedule" :key="index">
                            <v-col class="class-block-left2" cols="2" :class="{'class-block-left': index === 0}">
                                <v-sheet class="pa-2 ma-2">
                                    {{ course.course }}
                                </v-sheet>
                            </v-col>
                            <v-col class="class-block-right2" :class="{'class-block-right': index === 0}">
                                <v-sheet class="pa-2 ma-2">
                                    {{ course.time }} - {{ course.location }}
                                </v-sheet>
                            </v-col>
                        </v-row>
                        <p v-if="retrieveSchedule.length === 0">No classes scheduled for today!</p>
                    </v-container>

                    <p>Classes Tomorrow:</p>
                        <v-container class="class-block">
                            <v-row class="class-rows" no-gutters v-for="(course, index) in retrieveScheduleTomorrow" :key="index">
                                <v-col class="class-block-left2" cols="2" :class="{'class-block-left': index === 0}">
                                    <v-sheet class="pa-2 ma-2">
                                        {{ course.course }}
                                    </v-sheet>
                                </v-col>
                                <v-col class="class-block-right2" :class="{'class-block-right': index === 0}">
                                    <v-sheet class="pa-2 ma-2">
                                        {{ course.time }} - {{ course.location }}
                                    </v-sheet>
                                </v-col>
                            </v-row> 
                            <p v-if="retrieveScheduleTomorrow.length === 0">No classes scheduled for tomorrow!</p>
                        </v-container>
                </v-container>
            </v-col>

            <v-col cols="3">
                <br>
                <!-- Notification/Announcement/Deadlines Center -->
                <v-container class="deadlines-container">
                    <v-row style="padding-bottom: 15px;">
                        <p style="margin-top: 3px;">Deadlines:</p>
                        <v-spacer></v-spacer>
                        <!-- Turn on notifications button and popup dialog -->
                        <v-dialog v-model="dialogNotifications" max-width="420" style="font-family: Poppins;">
                            <template v-slot:activator="{ props: activatorProps }">
                                <v-btn size="extra-small" v-bind="activatorProps" variant="plain" style="position: relative;">
                                    <span class="material-symbols-outlined" v-if="notificationsActive === false">
                                        notifications_off
                                    </span>
                                    <span class="material-symbols-outlined" v-if="notificationsActive === true">
                                        notifications_active
                                    </span>
                                </v-btn>
                            </template>
                            <!--Pop up -->
                            <v-card title="Notification Center">
                                <v-card-text>
                                    <v-row>
                                        <v-col cols="auto">
                                            <v-switch
                                                v-model="notificationsActive"
                                                color="primary"
                                                label="Turn on email notifications"
                                                style="margin-top: -10px; margin-bottom: -35px; color: black;"
                                            ></v-switch>
                                        </v-col>
                                    </v-row>
                                    <v-row v-if="notificationsActive === true">
                                        <v-col cols="auto">
                                            <p>Remind me <strong style="color: red">{{daysBeforeNotification}}</strong> days before a deadline.<br><span style="font-size: 12px; color: gray;">(Sent to <em>{{user.email}}</em>)</span></p>
                                        </v-col>
                                        <v-col cols="1">
                                            <v-btn :disabled="daysBeforeNotification === 1" size="extra-small" v-bind="activatorProps" variant="plain" style="position: relative;" @click="daysBeforeNotification--">
                                                <span class="material-symbols-outlined">
                                                    remove
                                                </span>
                                            </v-btn>
                                        </v-col>
                                        <v-col cols="1">
                                            <v-btn :disabled="daysBeforeNotification === 7" size="extra-small" v-bind="activatorProps" variant="plain" style="position: relative;" @click="daysBeforeNotification++">
                                                <span class="material-symbols-outlined">
                                                    add
                                                </span>
                                            </v-btn>
                                        </v-col>
                                    </v-row>
                                    <v-row v-if="notificationsActive === true">
                                        <v-col cols="auto">
                                            <p>Select your notification sources:</p>
                                        </v-col>
                                    </v-row>
                                    <v-row v-if="notificationsActive === true" style="margin-top: -10px; margin-bottom: -55px;">
                                        <v-col cols="6">
                                            <v-checkbox v-model="selectedNotificationSources" label="UNR" value="UNR"></v-checkbox>
                                        </v-col>
                                        <v-col cols="6">
                                            <v-checkbox v-model="selectedNotificationSources" label="Instructors" value="Instructor"></v-checkbox>
                                        </v-col>
                                    </v-row>
                                    <v-row v-if="notificationsActive === true" style="margin-top: -20px; margin-bottom: -55px;">
                                        <v-col cols="6">
                                            <v-checkbox v-model="selectedNotificationSources" label="Admins" value="Admin"></v-checkbox>
                                        </v-col>
                                        <v-col cols="6">
                                            <v-checkbox v-model="selectedNotificationSources" label="User Deadlines" :value="user.firstname + ' ' + user.lastname"></v-checkbox>
                                        </v-col>
                                    </v-row>
                                </v-card-text> 
                                <v-card-actions>
                                    <v-spacer></v-spacer>
                                    <v-btn text="Close" variant="plain" @click="dialogNotifications = false"></v-btn>
                                    <v-btn color="primary" text="Save" variant="tonal" @click="turnOnEmailNotifications()"></v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-dialog> 
                    </v-row>
                    <v-expansion-panels>
                        <!-- Displays notifications -->
                        <v-expansion-panel class="deadline-title" v-for="(notification, index) in upcomingNotifications" :key="index" :title="`${notification.date} - ${notification.source}`" :class="{'upcoming': index === 0}">
                            <v-expansion-panel-text>
                                {{notification.message}}
                                <br>
                                <div v-if="notification.source === this.user.firstname + ' ' + this.user.lastname">
                                    <!-- Delete notification IF it is a custom deadline created by the user -->
                                    <v-dialog v-model="dialogDeleteDeadline[index]" max-width="400" style="font-family: Poppins;">
                                        <template v-slot:activator="{ props: activatorProps }">
                                            <v-btn v-bind="activatorProps" class="announcement-btn" variant="tonal" @click="handleLogout">
                                                <p>Delete Deadline</p>
                                            </v-btn>
                                        </template>
                                        <!--Pop up -->
                                        <v-card title="Delete Deadline">
                                            <v-card-text>
                                                <v-row dense>
                                                    <p>Are you sure you want to delete deadline <strong>{{notification.message}}</strong>?</p>
                                                </v-row>
                                            </v-card-text> 
                                            <v-card-actions>
                                                <v-spacer></v-spacer>
                                                <v-btn text="Cancel" variant="plain" @click="dialogDeleteDeadline[index] = false"></v-btn>
                                                <v-btn color="red" text="Delete" variant="tonal" @click="deleteDeadline(notification, index)"></v-btn>
                                            </v-card-actions>
                                        </v-card>
                                    </v-dialog>   
                                </div>
                            </v-expansion-panel-text>
                        </v-expansion-panel>
                    </v-expansion-panels>
                </v-container>
                    <!-- Create deadline button and dialog popup -->
                    <v-dialog v-model="dialogDeadline" max-width="1000" style="font-family: Poppins;">
                        <template v-slot:activator="{ props: activatorProps }">
                            <v-btn v-bind="activatorProps" class="announcement-btn" variant="outlined" @click="handleLogout">
                                <p>Create Deadline</p>
                            </v-btn>
                        </template>
                        <!--Pop up -->
                        <v-card title="Create Deadline">
                            <v-card-text>
                                <v-row dense>
                                    <v-col cols = "12" md="6">  
                                        <br>
                                        <p>Enter deadline information:</p>
                                        <br>
                                        <v-textarea v-model="deadlineDescription" label="Deadline Description" single-line rows="7"></v-textarea>
                                        <br>
                                    </v-col>
                                    <v-col cols="12" md="6">
                                        <v-date-picker v-model="deadlineDate" width="100%"></v-date-picker>
                                    </v-col>
                                </v-row>
                            </v-card-text> 
                            <v-card-actions>
                                <v-spacer></v-spacer>
                                <v-btn text="Cancel" variant="plain" @click="dialogDeadline = false"></v-btn>
                                <v-btn color="success" text="Create" variant="tonal" @click="createDeadline()"></v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
            </v-col>
        </v-row>
    </v-container>

    <!-- Enrolled Courses display -->
    <v-container class="dashboard-container2">
        <div class="inner-container">
        <v-row>
            <h1 class="header-text">Enrolled Courses</h1>
        </v-row>
        <p v-if="schedule.length === 0"><br>No courses enrolled, please visit the <router-link to="/courses" >Courses</router-link> page to add courses!</p>

        <v-row>
            <!-- Course Cards that are displayed -->
            <v-card class="enrolled-cards" v-for="(course, index) in schedule" :key="index" :title="course.course" :subtitle="course.location">
                <v-card-text>
                    {{ formatDays(course.days) }}<br>
                    {{ course.time }}
                </v-card-text>
                <v-card-actions>
                    <!-- View Course Details Button and dialog -->
                    <v-dialog v-model="dialog[index]" max-width="500" style="font-family: Poppins;">
                        <template v-slot:activator="{ props: activatorProps }">
                            <v-btn color="dark-grey" variant="tonal" v-bind="activatorProps">View Details</v-btn>
                        </template>
                        <!--Pop up -->
                        <v-card title="Course Details">
                            <v-card-text>
                                <v-row dense>
                                    <v-col cols = "auto">
                                        <strong>Course Name: </strong> {{ course.courseName }}<br>
                                        <strong>Instructor: </strong> {{ course.instructors && course.instructors.length > 0 ? course.instructors.join(', ') : 'N/A' }}<br>
                                        <strong>Credits: </strong> {{ course.Credits }}<br>
                                        <strong>Section: </strong> {{ course.Section }}<br>
                                        <strong>Office Hours: </strong> {{ course.officeHours && course.officeHours.length > 0 ? course.officeHours.join(', ') : 'N/A' }}<br>
                                        <strong>Office Location: </strong> {{ course.officeLocations && course.officeLocations.length > 0 ? course.officeLocations.join(', ') : 'N/A' }}<br>
                                    </v-col>
                                </v-row>
                            </v-card-text>  

                            <v-card-actions>
                                <v-btn text="Close" variant="plain" @click="dialog[index] = false"></v-btn>
                                <v-spacer></v-spacer>
                                <v-btn color="dark-grey" text="Unenroll" variant="tonal" @click="confirmUnenrollment(course.scheduleID, index)"></v-btn>
                            </v-card-actions>
                        </v-card>
                    </v-dialog>
                </v-card-actions>
            </v-card>
        </v-row>
        <br>

        <!-- Unenroll course confirmation -->
        <v-dialog v-model="showUnenrollDialog" max-width="500" style="font-family: Poppins;">
            <v-card>
                <v-card-title class="headline">Confirm Unenrollment</v-card-title>
                <v-card-text>Are you sure you want to unenroll from this course?</v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="dark-grey" variant="tonal" text @click="showUnenrollDialog = false">Cancel</v-btn>
                    <v-btn color="primary" variant="tonal" text @click="unenrollCourse">Confirm</v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        </div>
    </v-container>



</div>
<div v-else>
<!-- Displayed if user is unauthorized -->
<v-container fluid fill-height>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6">
        <img src="../assets/course compass logo.png" alt="Course Compass Logo" class="mx-auto d-block" style="width: 225px; height:auto;">
        <br>
        <h1 class="text-center" style="font-family: Coolvetica;">You are unauthorized to view this page.</h1>
        <p class="text-center">
            <br>
            Redirect back to <router-link to="/" >Home</router-link> page.
        </p>
      </v-col>
    </v-row>
  </v-container>
</div>
</template>

<script>
    import axios from 'axios';
    
    export default {
        props:{
            userType:{
                type: String,
                required: '',
            }
        },

        data() {
            return {
                //unenroll dialog
                unenrollScheduleID: null,
                showUnenrollDialog: false,
                dialog: [],

                //student data
                currentDate: null,
                user: {
                    firstname: '',
                    lastname: '',
                    dob: '',
                    major: '',
                    term: 'Spring 2024',
                    avatar: require('@/assets/profile-picture.jpg'),
                    email: '',
                },

                //deadlines
                dialogDeadline: false,
                dialogDeleteDeadline: [],
                deadlineDescription: '',
                deadlineDate: new Date(),

                //notifications on/off
                notificationsActive: false,
                dialogNotifications: false,
                daysBeforeNotification: 1,
                selectedNotificationSources: [],

                //student schedule
                schedule: [],

                //notifications
                notifications: [
                    {date: '5/15/2024', source: 'UNR', message: 'Instruction Ends'},
                    {date: '3/1/2024', source: 'UNR', message: 'Deadline to apply for May graduation'},
                    {date: '3/25/2024', source: 'Professor Mike', message: 'Hello Students, hw 1 is due in the next few weeks, and there is an exam tomorrow about coffee.'},
                    {date: '3/1/2024', source: 'UNR', message: 'Deadline to apply for May graduation'},
                    {date: '3/18/2024', source: 'UNR', message: 'Summer Session registration starts'},
                    {date: '3/19/2024', source: 'UNR', message: 'Final fee payment due for those on a payment plan'},
                    {date: '3/23/2024', source: 'UNR', message: 'Spring Break (campus open; no classes)'},
                    {date: '4/1/2024', source: 'UNR', message: 'Fall semester enrollment begins'},
                    {date: '4/2/2024', source: 'UNR', message: 'No dropping of individual classes after this deadline'},
                    {date: '5/8/2024', source: 'UNR', message: 'Prep Day'},
                    {date: '5/9/2024', source: 'UNR', message: 'Finals week begins'},
                    {date: '5/15/2024', source: 'UNR', message: 'Instruction Ends'},
                    {date: '5/16/2024', source: 'UNR', message: 'On-campus residence hall move-out (11 a.m.)'},
                    {date: '5/16/2024', source: 'UNR', message: 'Commencement'},
                    {date: '5/20/2024', source: 'UNR', message: 'Faculty to post final grades in MyNEVADA by 5 p.m.'},
                    {date: '5/20/2024', source: 'UNR', message: 'Spring semester ends, last day faculty on campus for spring semester'},
                ],
                emailNotifications:[], //THESE ARE THE ONES SENT TO THE USERS EMAIL, they have the exact day to send to the email, which is a set amount of days before actual date
            };
        },
        methods: {
            //formats days for course schedule display
            formatDays(days){
                return days.map(day => day.slice(0,3)).join('');
            },

            //gets student user data
            fetchDashboardData() {
                axios.get('http://127.0.0.1:5000/dashboard', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }})
                .then(response => {
                    this.user.firstname = response.data.Fname;
                    this.user.lastname = response.data.Lname;
                    this.user.major = response.data.majorName;
                    this.user.dob = response.data.DOB;
                    this.user.email = response.data.Email;
                    console.log('Dashboard loaded successfully', response.data);
                })
                .catch(error => {
                    console.error("Error fetching dashboard data", error);
                });
            },
        
            //get student's enrolled courses
            async fetchEnrolledCourses() {
                try {
                    const response = await axios.get('http://127.0.0.1:5000/getEnrolledCourses', {
                        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
                    });
                    this.schedule = response.data.enrolledCourses.map(course => ({
                        ...course,
                        scheduleID: course.scheduleID
                    }));
                } catch (error) {
                    console.error("Error fetching enrolled courses:", error);
                }
            },

            //unenroll course from student's schedule
            async unenrollCourse() {
                try {
                    const response = await axios.post('http://127.0.0.1:5000/unenrollCourse', {
                        scheduleID: this.unenrollScheduleID
                    }, {
                        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
                    });

                    if (response.status === 200) {
                        this.schedule = this.schedule.filter(course => course.scheduleID !== this.unenrollScheduleID);
                        console.log('Course unenrolled successfully');
                        this.showUnenrollDialog = false;
                        this.$emit('show-toast', { message: 'Course unenrolled.', color: '#51da6e' });
                    }
                } catch (error) {
                    console.error("Error unenrolling course:", error);
                }
            },

            //confirmation dialog
            confirmUnenrollment(scheduleID, index) {
                this.unenrollScheduleID = scheduleID;
                this.showUnenrollDialog = true;
                this.dialog[index] = false;
            },

            //Create custom student deadlines
            createDeadline(){
                //Month/Date/Year
                const reformatDate = new Date(this.deadlineDate).toLocaleDateString('en-US', {
                    month: 'numeric',
                    day: 'numeric',
                    year: 'numeric',
                });

                const deadline = {
                    date: reformatDate,
                    source: this.user.firstname + ' ' + this.user.lastname,
                    message: this.deadlineDescription,
                };

                this.notifications.push(deadline);

                this.deadlineDate = new Date();
                this.deadlineDescription ='';
                this.dialogDeadline = false;
            },

            //Delete custom deadliens
            deleteDeadline(notification, index){
                const toDelete = notification;
                console.log('test', toDelete);
                //find deadline in array
                const deadlineIndex = this.notifications.findIndex(notification =>
                    notification.date === toDelete.date &&
                    notification.message === toDelete.message);

                this.notifications.splice(deadlineIndex, 1);
                this.dialogDeleteDeadline[index] = false;
            },

            //turn on email notifications
            turnOnEmailNotifications(){
                const currentDate = new Date();
                const grabNotifications = JSON.parse(JSON.stringify(this.notifications));//copy this.notifcations

                let filteredNotifications = grabNotifications.filter(notification => {
                    const notificationDate = new Date(notification.date);

                    const isSelectedSource = this.selectedNotificationSources.includes(notification.source);

                    const isFutureDate = notificationDate > currentDate;

                    const sendNotificationDate = new Date(notificationDate);
                    sendNotificationDate.setDate(sendNotificationDate.getDate() - this.daysBeforeNotification);

                    notification.date = sendNotificationDate.toISOString().split('T')[0];

                    return isSelectedSource && isFutureDate;
                });

                filteredNotifications.sort((a, b) => new Date(a.date) - new Date(b.date)); //filter by date

                this.emailNotifications = filteredNotifications;
                this.dialogNotifications = false;
                console.log('Filtered Notifications', filteredNotifications);
                this.sendEmail();                
            },

            //Send email notifications for deadlines
            sendEmail(){
                const notificationToEmail = this.emailNotifications[0];

                const reformatDate = new Date(notificationToEmail.date).toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                });

                const newDate = new Date().toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                });

                const originalDeadline = new Date(notificationToEmail.date);

                originalDeadline.setDate(originalDeadline.getDate() + this.daysBeforeNotification);

                const formattedDeadline = originalDeadline.toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric',
                });

                const email = {
                    date: newDate,
                    subject: 'Course Compass Upcoming Deadline Reminder ' + newDate,
                    to: this.user.email, 
                    content: 'This is an automated message to remind you of an upcoming deadline in ' + this.daysBeforeNotification + ' days:\nDeadline message: ' + notificationToEmail.message + '\nDeadline source: ' + notificationToEmail.source + '\nEmail received on ' + reformatDate + '\nDate of deadline: ' + formattedDeadline,
                };

                axios.post('http://127.0.0.1:5000/send-email', email)
                .then(response => {
                    console.log("Email sent successfully");
                })
                .catch(error => {
                    console.error("Failed to send email: ", error);
                });
            },

            //Send email based on if it is time for email to be sent
            deadlineCheck(){
                const notification = this.emailNotifications[0];

                const today = newDate();
                const deadline = new Date(notification.date)
                if(today >= deadline){
                    this.sendEmail();
                }
            },
        },
        
        beforeRouteUpdate(to, from, next) {
            if (to.path === '/dashboard') {
                this.fetchDashboardData();
            }
            next();
        },
        
        computed:{
            //format current date
            currentDate(){
                const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
                this.currentDate = new Date().toLocaleDateString('en-US', options);
                return this.currentDate;
            },
            //If deadline is past today, it wont be displayed in notification center
            upcomingNotifications() {
                const currentDate = new Date();
                //const currentDate = new Date('2024-03-03'); test case
                const upcomingNotifications = this.notifications
                    .filter(notification => new Date(notification.date) > currentDate)
                    .sort((a, b) => new Date(a.date) - new Date(b.date));
                return upcomingNotifications.length > 0 ? upcomingNotifications : null;
            },

            //Next two functions retrieves todays and tomorrows classes
            retrieveSchedule(){
                const currentDayIndex = new Date().getDay();
                const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                const currentDay = daysOfWeek[currentDayIndex];

                return this.schedule.filter(course => {
                    return course.days.some(day => day.trim() === currentDay);
                }).sort((a, b) => {
                    const getTime = time => {
                        const [timeVar, ampm] = time.split(' ');
                        let [hours, minutes] = timeVar.split(':').map(Number);

                        if (ampm.trim() === 'PM' && hours !== 12) {
                            hours += 12; 
                        } else if (ampm.trim() === 'AM' && hours === 12) {
                            hours = 0;
                        }

                        return hours * 60 + minutes; 
                        };

                        const startOne = getTime(a.start);
                        const startTwo = getTime(b.start);

                        if (startOne < startTwo) {
                            return -1;
                        } else if (startOne > startTwo) {
                            return 1;
                        }
                });
            },

            retrieveScheduleTomorrow(){
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1); //Tomorrow

                const nextDayIndex = tomorrow.getDay();
                const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
                const nextDay = daysOfWeek[nextDayIndex];

                return this.schedule.filter(course => {
                    return course.days.some(day => day.trim() === nextDay);
                }).sort((a, b) => {
                    const getTime = time => {
                        const [timeVar, ampm] = time.split(' ');
                        let [hours, minutes] = timeVar.split(':').map(Number);

                        if (ampm.trim() === 'PM' && hours !== 12) {
                            hours += 12; 
                        } else if (ampm.trim() === 'AM' && hours === 12) {
                            hours = 0;
                        }

                        return hours * 60 + minutes; 
                        };

                        const startOne = getTime(a.start);
                        const startTwo = getTime(b.start);

                        if (startOne < startTwo) {
                            return -1;
                        } else if (startOne > startTwo) {
                            return 1;
                        }
                });
            },
        },

        mounted(){
            this.dialog = new Array(this.schedule.length).fill(false);

            if (!localStorage.getItem('access_token')) {
                this.$router.push('/login');
            } else {
                this.fetchDashboardData();
                this.fetchEnrolledCourses(); //enrolled courses data
            }

            //check date for sending deadline email every day
            this.checkDate = setInterval(() => {
                this.deadlineCheck();
            }, 1000*60*60*24);
        },
    }
</script>

<style scoped>
    p{
        font-family: Poppins;
        font-size: 15px;
        margin: 0px;
    }

    .class-rows{
        margin-bottom: 14px;
    }
    .class-block{
        position: relative;
    }

    .class-block-left{
        border-top: 1px solid black;
        border-right: 1px solid black;
        border-bottom: 1px solid black;
    }

    .class-block-left2{
        border-right: 1px solid black;
        border-bottom: 1px solid black;
    }

    .class-block-right{
        border-top: 1px solid black;
        position: relative;
        top: 1px;
    }

    .class-block-right2{
        margin-top: -1px;
        border-top: 1px solid black;
    }
    
    .welcome-text{
        font-family: coolvetica;
        position: relative;
        margin-top: 16px;
        margin-left: 10px;
        font-size: 32px;
        left:1%;
    }

    .top-container{
        top: -1.7px;
        margin: 10px auto;
        position: relative;
        max-width: 90%;
        border-radius: 1px;
        border-top: 1px solid black;
        border-left: 1px solid black;
        border-right: 1px solid black;
    }

    .dashboard-container{
        margin: 10px auto;
        position: relative;
        max-width: 90%;
        border-radius: 1px;
        border-top: 1px solid black;
        border-left: 1px solid black;
    }

    .dashboard-container2{
        margin: 10px auto;
        position: relative;
        max-width: 90%;
        border-radius: 1px;
        border-top: 1px solid black;
        border-right: 1px solid black;
    }

    .dashboard-container3{
        margin: 10px auto;
        position: relative;
        max-width: 90%;
        border-radius: 1px;
        border-top: 1px solid black;
        border-left: 1px solid black;
    }

    .deadlines-container{
        max-height: 500px;
        overflow-y: auto;
        overflow-x: hidden;
    }

    .deadline-title {
        font-family: Poppins;
        display: inline-block;
    }

    .header-text{
        font-family: Coolvetica;
        font-size: 25px;
    }

    .enrolled-cards{
        margin-right: 6px;
        font-family: Poppins;
        background-color: rgb(236, 236, 236);

    }

    .upcoming{
        font-weight: bold;
        background-color: rgba(255, 0, 0, 0.168);
    }

    .inner-container {
        position: relative;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: 96%;
        margin: 0 auto;
    }

    .announcement-btn{
        margin-top: 15px;
        width: 100%;
    }

    .v-date-picker{
        margin-top: -29px;
        margin-bottom: -38px;
    }
</style>