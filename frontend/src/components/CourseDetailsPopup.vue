<!-- Created by: John Montesa -->
<!-- This component details a specific course a user has interacted with -->
<!-- It will popup a screen for the user to see more indepth information about the course and student's opinions on it -->
<!-- The user faces two buttons where they can either close the popup screen or add it to their schedule -->
<!-- If the user adds it to their schedule, it will add it to a schedule array -->

<template>
    <div class="popup" @click="closePopup">
        <!--Pop up Screen with details of course-->
        <div class="popup-content" @click.stop>
            <button class="close-btn" @click="closePopup">
                <span class="material-icons" style="color:black">close</span>
            </button>
            <h2>Course Details</h2>
            <div class="container" v-if="course">
                <div class="row">
                    <!--Left Side of Popup Page, Reveals Course Details-->
                    <div class="col-lg left-column">
                        <p><strong>Department:</strong> {{ course.department || 'N/A' }}</p>
                        <p><strong>Name:</strong> {{ course.name || 'N/A' }}</p>
                        <p><strong>Code:</strong> {{ course.code || 'N/A' }}</p>
                        <p><strong>Professor:</strong> {{ course.professor || 'N/A' }}</p>
                        <p><strong>Format:</strong> {{ course.format || 'N/A' }}</p>
                        <br>
                        <p><strong>Term:</strong> {{ course.term || 'N/A' }}</p>
                        <p><strong>Units:</strong> {{ course.units || 'N/A' }}</p>
                        <br>
                        <p><strong>Meeting Details:</strong></p>
                        <p><strong>Location:</strong> {{ course.location || 'N/A' }}</p>
                        <p><strong>Days:</strong> {{ course.days && course.days.length > 0 ? course.days.join(' | ') : 'Information not available' }}</p>
                        <p><strong>Meeting Time:</strong> {{ course.meetingTime || 'N/A' }}</p>
                    </div>
                    
                    <!--Right Side of Popup Page, Shows User Thoughts-->
                    <div class="col-lg">
                        <p><strong>What Students Think:</strong></p>
                        <p>{{ course.keywords && course.keywords.length > 0 ? course.keywords.join(', ') : 'Information not available' }}</p>
                        <p><strong>Student Rating:</strong> {{ course.rating || '0' }}/5</p>
                        <hr>
                        <p><strong>What Students Say:</strong></p>
                        <p>{{ course.keywords && course.keywords.length > 0 ? course.keywords.join(', ') : 'Information not available' }}</p>
                    </div>
                    <div class="w-100"></div>
                </div>
            </div>
            <div v-else>
                <p>Course information unavailable.</p>
            </div>
            <br>
            <div class="button-container">
                    <button class="schedule-button" @click="addToSchedule">Add Course to Cart</button>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        props: {
            course: Object,
        },
        methods: {
            closePopup() {
                this.$emit('close');
                },
            addToSchedule() {
                this.$emit('addToSchedule', this.course);
                },
            },
        };
    </script>

<style scoped>
    .popup {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index:2;
    }

    .popup-content {
        background: #ffffff;
        padding: 20px;
        border-radius: 8px;
    }

    .left-column {
        border-right: 1px solid #000000;
    }

    .close-btn {
        margin-left: auto;
    }

    img {
        width: 100%;
        height: auto;
    }

    h2{
        font-family: 'coolvetica', coolvetica;
        text-align: center;
        color:#000000;
    }
    p{
        font-family: Poppins, sans-serif;
    }

    .button-container {
        margin: 0;
        padding: 0;
        overflow: hidden;
        display: flex;
        justify-content: center;
    }

    .schedule-button {
        font-family: coolvetica;
        background-color: #000000;
        color: #ffffff;
        padding: 10px 30px;
        font-size: 20px;
        border: none;
        cursor: pointer;
        display: inline-block;
        transition: background-color 0.3s linear, color 0.3s linear;
        text-decoration: none;
    }

    .schedule-button:hover {
        background-color: #ffffff;
        color: #000000;
    }
</style>