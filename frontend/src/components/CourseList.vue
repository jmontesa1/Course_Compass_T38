<!-- Created by: John Montesa -->
<!-- This component creates the courses list that the user will interact with -->
<!-- Classes are displayed in a list matter, where the background color alternates from each course to provide better readability -->
<!-- Each item is shown as their course department, course number, and name of course -->


<template>
    <!-- Display the courses in a list -->
    <div class="course-list">
        <div v-for="(course, index) in courses" :key="index" class="course-item" @click="handleCourseClick(course)">
        {{ course.name }}
        </div>
        <CourseDetailsPopup v-if="selectedCourse" :course="selectedCourse" @close="closePopup" @addToSchedule="addToSchedule" /> 
    </div>


    <!-- This is a schedule array test, I would need to find a way to store this globally and so that it persists-->
    <div class="schedule">
    <h2>Schedule</h2>
        <div v-for="(course, index) in schedule" :key="index" class="schedule-item">
            {{ course.name }}
        </div>
    </div>

    <!-- Duplicate Courses in Schedule Check -->
    <div v-if="notification" class="full-screen-notification">
        <div class="notification-content">
            <span>{{ notification }}</span>
            <button class ="close-btn" @click="clearNotification">
                <img src="../assets/X.png" alt="Close Button">
            </button>
        </div>
    </div>


</template>

<script>
    import CourseDetailsPopup from '@/components/CourseDetailsPopup.vue';

    export default {
        //the courses are passed in as a prop array
        props: {
            courses: Array,
        },
        data() {
            return {
                selectedCourse: null,
                schedule: [],
                notification: null,
            };
        },
        methods: {
            handleCourseClick(course) {
                this.selectedCourse = course;
            },
            closePopup() {
                this.selectedCourse = null;
                this.notification = null;
            },
            addToSchedule(course) {
                if (!this.schedule.some((c) => c.name === course.name)) {
                    this.schedule.push(course);
                    this.selectedCourse = null; // Close the popup after adding to the schedule
                    this.notification = null; // Clear any existing notifications
                }
                else {
                    this.notification = `${course.name} is already added to your schedule.`;
                }
            },
            showNotification(message, isError = false) {
                this.notification = {
                    message,
                    isError,
                };
            },
            clearNotification() {
                this.notification = null;
            },
        },
        components: {
            CourseDetailsPopup,
            },
        };
</script>

<style scoped>
    .course-list {
        width: 100%;
        flex-direction: column;
    }

    .course-item {
        font-family: akira;
        padding: 8px;
        box-sizing: border-box;
        /*margin-bottom: 1px;
        /*border-radius: 0px;
        /*border: 1px solid #000000;*/
        color: #000000;
        cursor: pointer;
    }
    .course-item:nth-child(even) {
        background: #dddddd;
    }

    .course-item:nth-child(odd) {
        background: #aaaaaa; 
    }

    .full-screen-notification {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .notification-content {
        font-family: Popins, sans-serif;
        font-size: 20px;
        font-style: bold;
        color: #ffffff;
        background: rgb(130, 0, 0.7);
        padding: 20px;
        border: solid 1px #000000;
        border-radius: 5px;
        text-align: center;

    }

    .close-btn {
        margin-top: 10px;
        padding: 10px;
        border: transparent;
        background: transparent;
        cursor: pointer;
        width: 50px;
        height: 50px;
    }

    img {
        width: 100%;
        height: auto;
    }

    h2{
        font-family: 'akira', akira;
        color:#000000;
    }
</style>
