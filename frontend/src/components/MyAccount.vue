<!--Created by: John Montesa-->
<!-- This is the Account page for Course Compass -->

<template>
    <div class="settings-container">
        <div class="container-fluid mt-3">
            <div class="row">
                <!--LEFT SIDE OF PAGE-->
                <div class="col-md-1 d-flex flex-column">
                    <img class="gear" src="../assets/gear.png" alt="Settings Icon">
                </div>


                <!--RIGHT SIDE OF PAGE-->
                <div class="col d-flex flex-column">
                    <h2>My Account</h2>

                    <div>
                        <br>
                        <br>
                        <p><strong>First Name:</strong> {{ user.firstname }}</p>
                        <p><strong>Last Name:</strong> {{ user.lastname }}</p>
                        <p><strong>Email:</strong> {{ user.email }}</p>
                        <p><strong>Birthdate:</strong> {{ user.dob }}</p>
                        <p><strong>Major:</strong> {{ user.major }}</p>

                        <v-dialog v-model="dialog" max-width="500" style="font-family: Poppins;">
                            <template v-slot:activator="{ props: activatorProps }">
                                <btn class="account-button" v-bind="activatorProps">Edit Profile</btn>
                            </template>
                            <!--Pop up -->
                            <v-card title="Edit Profile Information">
                                <v-card-text>
                                    <v-form>
                                        <v-text-field v-model="firstName" label="First Name"></v-text-field>
                                        <v-text-field v-model="lastName" label="Last Name"></v-text-field>
                                        <v-text-field v-model="email" label="Email"></v-text-field>
                                        <v-menu offset-y>
                                            <template v-slot:activator="{ on, attrs }">
                                                <v-text-field v-model="birthdate" label="Birthdate" v-bind="attrs" v-on="on" readonly></v-text-field>
                                            </template>
                                            <v-date-picker v-model="birthdate" @input="$refs.menu.save(birthdate)"></v-date-picker>
                                        </v-menu>
                                        <v-select v-model="major" :items="majorOptions" label="Major"></v-select>
                                    </v-form>
                                </v-card-text>
                                <v-card-actions>

                                    <v-spacer></v-spacer>
                                    <v-btn text="Cancel" variant="plain" @click="dialog = false"></v-btn>
                                    <v-btn color="primary" text="Confirm Changes" variant="tonal"></v-btn>
                                </v-card-actions>
                            </v-card>
                        </v-dialog>

                        <btn class="account-button" @click="navigateToChangePassword">Change Password</btn>
                    </div>
                </div>

                <div class="col-md-2 d-flex flex-column">
                    <br>
                    <br>
                    <img class="profile-picture" :src="user.profilePicture" alt="Profile Picture">
                    <p style="text-align:center;"><i>Profile Picture</i></p>
                    <br>
                </div>

            </div>
        </div>
    </div>
</template>

<script>
    import axios from 'axios';
    
    export default {
        data() {
            return {
                user: {
                    firstname: '',
                    lastname: '',
                    email: '',
                    dob: '',
                    major: '',
                    profilePicture: require('../assets/profile-picture.jpg'),
                },
                dialog: false,
                error: null,
            };
        },
        created() {
            this.fetchUserInfo();
        },
        methods: {
            fetchUserInfo() {
                axios.get('http://127.0.0.1:5000/myaccount', { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }})
                .then(response => {
                    this.user.firstname = response.data.Fname;
                    this.user.lastname = response.data.Lname;
                    this.user.email = response.data.Email;
                    this.user.dob = response.data.DOB;
                    this.user.major = response.data.majorName;
                    console.log('My Account page loaded successfully', response.data);
                })
                .catch(error => {
                    console.error("Error loading My Account page", error);
                });        
            },
            navigateToChangePassword() {
                this.$router.push('/changepassword');
            }
        }
    }
</script>

<style scoped>
    h2 {
        text-align: left;
        font-family:coolvetica;
    }

    p{
        font-family: Poppins, sans-serif;
    }

    .settings-container {
        background-color: #e1e1e1;
        margin: 3% auto;
        padding: 20px;
        width: 80%;
        height: auto;
        border-radius: 8px;
        box-shadow: 0 0 px rgba(232, 0, 0, 0.1);
    }
    
    .col{
        border-left: 2px solid #000000;
    }

    .gear {
        min-width: 30px;
        max-width: 60px;
    }

    .profile-picture {
        margin-left:auto;
        margin-right:auto;
        max-width: 100px;
        border-radius: 50%; 
        margin-bottom: 10px;
    }

    .account-button {
        font-family: coolvetica, sans-serif;
        font-size: 25px;
        background-color: #000000;
        color: #ffffff;
        padding: 5px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s linear, color 0.3s linear;
        margin-right: 40px;
    }

    button:hover {
        background-color: #555555;
    }

</style>