# Created by Lucas Videtto
# Backend functionality for Course Compass

from flask import Flask, jsonify, request, session
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from mysql.connector import connect, Error
from datetime import datetime
from flask_bcrypt import Bcrypt
import logging



# Under construction !!!
app = Flask(__name__)
app.secret_key = '123456789' # Change key to secure value for production environment
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)



# User class to store user information
class User:
    def __init__(self, userID=None, Fname=None, Lname=None, DOB=None, Email=None, majorName=None, majorID=None):
        self.userID = userID
        self.Fname = Fname
        self.Lname = Lname
        self.DOB = DOB
        self.Email = Email
        self.majorName = majorName
        self.majorID = majorID
        
    @staticmethod
    def get_user_by_email(email):
        connection = connectToDB()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""SELECT u.userID, u.Fname, u.Lname, u.DOB, u.Email, s.majorID, m.majorName
            FROM tblUser u LEFT JOIN tblStudents s ON u.userID = s.userID LEFT JOIN tblMajor m ON s.majorID = m.majorID WHERE u.Email = %s""", (email,))
            user_data = cursor.fetchone()
            print("Fetched user data:", user_data)
            if user_data:
                user = User(**user_data)
                return user
            return None
        except Exception as e:
            print(e)
            return None
        finally:
            cursor.close()
            connection.close()
            
    def conv_to_json(self):
        return{
            "userID": self.userID,
            "Fname": self.Fname,
            "Lname": self.Lname,
            "DOB": self.DOB.strftime('%Y-%m-%d') if self.DOB else None,
            "Email": self.Email,
            "majorID" : self.majorID,
            "majorName": self.majorName
        }
        
    def get_major_courses(self):
        connection = connectToDB()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT
                    c.courseID,
                    c.courseCode,
                    c.courseName,
                    c.description,
                    c.Credits,
                    c.Level,
                    c.Requirements
                FROM
                    cs425.tblUser u
                JOIN
                    cs425.tblMajor m ON u.majorID = m.majorID
                JOIN
                    cs425.tblMajorCourses mc ON m.majorID = mc.majorID
                JOIN
                    cs425.tblCourses c ON mc.courseID = c.courseID
                WHERE
                    u.Email = %s
            """, (self.Email,))
            courses = cursor.fetchall()
            return courses
        except Exception as e:
            print(e)
            return []
        finally:
            cursor.close()
            connection.close()
            
    def courses_to_json(self):
        return {
            "courses": self.get_major_courses()
        }
        

# Login functionality for backend
# Check backend development notes (Lucas)
# Included print statements for terminal reference
@app.route('/login', methods=['POST'])
def login(): 
    if request.method == 'POST':
        email = request.json.get('email')
        password = request.json.get('password')
        
        if not email or not password:
            print("MISSING EMAIL OR PASSWORD")
            return jsonify({"message": "Missing email or password"}), 400
        
        try:
            connection = connectToDB()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tblUser WHERE Email = %s", (email,))
            user = cursor.fetchone()
            
            if user and bcrypt.check_password_hash(user['Passwd'], password):
                session['email'] = email
                
                print("LOGIN SUCCESSFUL")
                
                access_token = create_access_token(identity={"email": user['Email'], "userID": user['userID']})
                return jsonify({"message": "Login successful", "access_token": access_token}), 200
            else:
                print("INVALID EMAIL OR PASSWORD")
                return jsonify({"message": "Invalid email or password"}), 401
        except Error as err:
            print(err)
            return jsonify({"message": "An error occurred"}), 500
        
        finally:
            cursor.close()
            connection.close()
    else:
        print("INVALID REQUEST")
        return jsonify({"message": "Invalid request"}), 400
            

# Signup functionality for backend
# Check backend development notes (Lucas)
# Included print statements for terminal reference
@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        fname = request.json.get('firstname')
        lname = request.json.get('lastname')
        dob = request.json.get('dateOfBirth')
        email = request.json.get('email')
        pw = request.json.get('password')
        userType = request.json.get('userType')
        majorID = request.json.get('majorID') if userType == 'Student' else None
        majorName = request.json.get('majorName')

        print("Received userType:", userType)

        if userType not in ['Student', 'Instructor']:
            print("INVALID USER TYPE")
            return jsonify({"message": "Invalid user type"}), 400

        if not fname or not lname or not dob or not email or not pw:
            print("MISSING REQUIRED FIELDS")
            return jsonify({"message": "Missing required fields"}), 400

        birthdate = datetime.strptime(dob, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        if age < 17:
            print("MUST BE AT LEAST 17 YEARS OLD TO REGISTER")
            return jsonify({"message": "Must be at least 17 years old to sign up"}), 400

        try:
            connection = connectToDB()
            cursor = connection.cursor(dictionary=True)

            connection.start_transaction() #handle insertion into both tables as one transaction
            
            cursor.execute("SELECT * FROM tblUser WHERE Email = %s", (email,))
            if cursor.fetchone():
                print("EMAIL ALREADY IN USE")
                return jsonify({"message": "Email already exists"}), 409
            
            #insert into user table
            hashed_pw = bcrypt.generate_password_hash(pw).decode('utf-8')
            cursor.execute("INSERT INTO tblUser (Fname, Lname, DOB, Email, Passwd) VALUES (%s, %s, %s, %s, %s)", (fname, lname, dob, email, hashed_pw))
            
            #retrieve the new userID
            cursor.execute("SELECT userID FROM tblUser WHERE Email = %s", (email,))
            new_user = cursor.fetchone()

            if userType == 'Student':
                cursor.execute("SELECT majorID, majorName FROM tblMajor WHERE majorName = %s", (majorID,))
                major = cursor.fetchone()
                if not major:
                    print("INVALID MAJOR")
                    connection.rollback()
                    return jsonify({"message": "Invalid major selected"}), 400
                majorID = major['majorID']
                majorName = major['majorName']

                cursor.execute("INSERT INTO tblStudents (userID, Email, majorName, majorID) VALUES (%s, %s, %s, %s)", (new_user['userID'], email,majorName, majorID))
                connection.commit()
            elif userType == 'Instructor':
                cursor.execute("INSERT INTO tblInstructor (userID, Email) VALUES (%s, %s)", (new_user['userID'], email))
                connection.commit()
            
            session['email'] = email
            access_token = create_access_token(identity={"email": email, "userID": new_user['userID']})
            
            print("SIGN UP SUCCESSFUL")
            return jsonify({"message": "Signup successful", "access_token": access_token}), 200
        except Error as err:
            print(err)
            connection.rollback()
            return jsonify({"message": "An error occurred"}), 500
        
        finally:
            cursor.close()
            connection.close()
            
    print("INVALID REQUEST")
    return jsonify({"message": "Invalid request"}), 400


# Fetch user information
@app.route('/getUserInfo', methods=['GET'])
def getUserInfo():
    if 'user_id' in session and 'email' in session:
        userid = session['user_id']
        useremail = session['email']
        connection = connectToDB()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT Fname, Lname, Email, majorName FROM cs425.tblUser WHERE userID = %s AND Email = %s", (userid, useremail))
                user_info = cursor.fetchone()
                if user_info:
                    return jsonify(user_info), 200
                else:
                    return jsonify({"error": "User not found"}), 404
            except Error as err:
                return jsonify({"error": "Error while fetching data: " + str(err)}), 500
            finally:
                cursor.close()
                connection.close()
        else:
            return jsonify({"error": "DB connection failed"}), 500
    else:
        return jsonify({"error": "User not logged in"}), 401
    

#retrive user schedule
@app.route('/getUserSchedule', methods=['GET'])
@jwt_required()
def user_schedule():
    try:
        identity = get_jwt_identity()
        current_user_email = identity.get('email')

        if not current_user_email:
            logging.warning("JWT identity does not contain email.")
            return jsonify({"error": "Authentication information is incomplete."}), 400

        logging.info(f"Current user email: {current_user_email}") 

        return fetch_user_schedule(current_user_email)
    except Exception as e:
        logging.error(f"An unexpected error occurred while fetching the user schedule: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

def fetch_user_schedule(email):
    try:
        with connectToDB() as connection:
            with connection.cursor() as cursor:
                user_schedule = user_schedule_stored_procedure(cursor, email)
                if user_schedule is not None:
                    return jsonify({"user_schedule": user_schedule}), 200
                else:
                    logging.warning(f"Failed to fetch schedule for {email}")
                    return jsonify({"error": "Failed to fetch user schedule"}), 500
    except Exception as e:
        logging.error(f"Error fetching user schedule for {email}: {e}", exc_info=True)
        return jsonify({"error": "An error occurred while fetching the user schedule"}), 500
    

def user_schedule_stored_procedure(cursor, email):
    try:
        cursor.callproc('GetUserSchedule', [email])

        user_schedule = []
        for result in cursor.stored_results():
            user_schedule = result.fetchall()

        schedule_list = []
        for schedule in user_schedule:
            schedule_dict = {
                "courseCode": schedule[0],
                "meetingDays": schedule[1],
                "meetingTimes": schedule[2],
                "startTime": schedule[3],
                "endTime": schedule[4],
                "Location": schedule[5],
                "Term": schedule[6],
            }
            schedule_list.append(schedule_dict)

        return schedule_list
    except Error as err:
        print("Error while fetching user schedule:", err)
        return None
    


#mark a course as completed
@app.route('/markCourseCompleted', methods=['POST'])
@jwt_required()
def mark_course_completed_endpoint():
    identity = get_jwt_identity()
    user_email = identity['email']  
    data = request.get_json()
    course_code = data.get('courseCode')
    
    success, message = mark_course_completed(user_email, course_code)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500

def mark_course_completed(user_email, course_code):
    connection = connectToDB()
    if not connection:
        return False, "DB connection failed"
    
    try:
        cursor = connection.cursor()
        cursor.callproc('MarkCourseCompleted', [user_email, course_code])
        connection.commit()
        return True, "Course marked as completed successfully"
    except Error as err:
        connection.rollback()
        return False, f"Error marking course as completed: {err}"
    finally:
        cursor.close()
        connection.close()




# Retrieve majors
@app.route('/majors', methods=['GET'])
def get_majors():
    connection = connectToDB()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT majorName FROM cs425.tblMajor")
            majors = [row[0] for row in cursor.fetchall()]
            return jsonify({"majors": sorted(majors)}), 200  
        except Error as err:
            return jsonify({"error": "Error while fetching majors: " + str(err)}), 500
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify({"error": "DB connection failed"}), 500
    

#logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()  
    print('Logut Successful')
    return jsonify({"message": "Logout successful"}), 200


#Developed by John
#tests to see if the user is logged in for front end usability
@app.route('/check_login', methods=['GET'])
def check_login():
    if 'email' in session:
        return jsonify({'logged_in': True, 'user_id': session['user_id'], 'email': session['email']}), 200
    else:
        return jsonify({'logged_in': False}), 401
    

# User session for dashboard
@app.route('/dashboard', methods=['GET'])
@jwt_required()
def user_dashboard():
    identity = get_jwt_identity()
    current_user_email = identity['email']
    print(f"Extracted email: {current_user_email}")
    user = User.get_user_by_email(current_user_email)
    if user:
        print("STILL LOGGED IN SUCCESS")
        return jsonify(user.conv_to_json()), 200    
    else:
        return jsonify({"message": "User not found"}), 404
    
    
# Load courses page with user-specific course list
@app.route('/courses', methods=['GET'])
@jwt_required()
def loadCourses():
    identity = get_jwt_identity()
    current_user_email = identity['email']
    print(f"Extracted email: {current_user_email}")
    user = User.get_user_by_email(current_user_email)
    if user:
        print("STILL LOGGED IN SUCCESS")
        test = user.courses_to_json()
        print(test)
        return jsonify(user.courses_to_json()), 200
    else:
        return jsonify({"message": "User not found"}), 404
    
    
@app.route('/myaccount', methods=['GET'])
@jwt_required()
def myAccount():
    identity = get_jwt_identity()
    current_user_email = identity['email']
    print(f"Extracted email: {current_user_email}")
    user = User.get_user_by_email(current_user_email)
    if user:
        print("STILL LOGGED IN MY ACCOUNT")
        return jsonify(user.conv_to_json()), 200
    else:
        return jsonify({"message": "User not found"}), 404
    
    
@app.route('/editprofile', methods=['GET'])
@jwt_required()
def editProfile():
    identity = get_jwt_identity()
    current_user_email = identity['email']
    print(f"Extracted email: {current_user_email}")
    user = User.get_user_by_email(current_user_email)
    if user:
        print("STILL LOGGED IN MY ACCOUNT")
        return jsonify(user.conv_to_json()), 200
    else:
        return jsonify({"message": "User not found"}), 404
    
    
@app.route('/changepassword', methods=['GET'])
@jwt_required()
def changePassword():
    identity = get_jwt_identity()
    current_user_email = identity['email']
    print(f"Extracted email: {current_user_email}")
    user = User.get_user_by_email(current_user_email)
    if user:
        print("STILL LOGGED IN MY ACCOUNT")
        return jsonify(user.conv_to_json()), 200
    else:
        return jsonify({"message": "User not found"}), 404


#retrieve courses with completion status
@app.route('/getCourseProgress', methods=['GET'])
@jwt_required()
def courses_for_progress_page():
    identity = get_jwt_identity()
    current_user_email = identity['email']
    user = User.get_user_by_email(current_user_email)
    if not user:
        return jsonify({"error": "User not found"}), 404

    connection = connectToDB()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT creditsReq FROM tblMajor WHERE majorName = %s", (user.majorName,))
            total_credits_req = cursor.fetchone()[0]

            cursor.callproc('GetCoursesForProgress', [current_user_email])
            user_courses = []
            for result in cursor.stored_results():
                user_courses = result.fetchall()

            course_list = []
            for courses in user_courses:
                course_dict = {
                    "courseName": courses[1],
                    "courseCode": courses[2],
                    "credits": courses[3],
                    "isCompleted": courses[4],
                }
                course_list.append(course_dict)


            return jsonify({
                "majorName": user.majorName,
                "totalCreditsReq": total_credits_req,
                "user_courses": course_list
            }), 200
        except Error as err:
            return jsonify({"error": "Error while fetching user's courses: " + str(err)}), 500
        finally:
            cursor.close()
            connection.close()
    else:
        return jsonify({"error": "DB connection failed"}), 500
    
    
# Retrieve courses related to user input at department search
@app.route('/search-departments', methods=['GET'])
@jwt_required()
def search_departments():
    query_param = request.args.get('query', '')
    connection = connectToDB()
    if connection:
        cursor = connection.cursor()
        try:
            query = "SELECT DISTINCT courseName, courseCode, courseMajor, department, professor, term, format, units, meetingTime FROM tblCourseNames WHERE courseMajor LIKE %s"
            search_term = f"%{query_param}%"
            cursor.execute(query, (search_term,))
            result = cursor.fetchall()
            departments = [{'professor': dept[4], 'courseName': dept[0], 'courseCode': dept[1], 'courseMajor': dept[2], 'department': dept[3], 'term': dept[5], 'format': dept[6], 'units': dept[7], 'meetingTime': dept[8]} for dept in result]
        finally:
            cursor.close()
            connection.close()
        return jsonify(departments), 200
    else:
        return jsonify({"message": "Failed to connect to database"}), 500
    
    
# Add courses to user schedule
@app.route('/enrollCourses', methods=['POST'])
@jwt_required()
def enroll_courses():
    try:
        current_user_email = get_jwt_identity()['email']
        courses = request.json.get('courses', [])
        if not courses:
            return jsonify({"message": "No courses to add"}), 400
        connection = connectToDB()
        cursor = connection.cursor()
        print(courses)
        for course_code in courses:
            cursor.execute("INSERT INTO tblTempUserSchedule (Email, courseCode) VALUES (%s, %s)", (current_user_email, course_code))
        connection.commit()
        print("COURSES ADDED")
        return jsonify({"message": "Courses successfully added"}), 200
    except Error as e:
        print(e)
        return jsonify({"message": "Error adding courses"}), 500
    finally:
        cursor.close()
        connection.close()


#retrieve notification for banner
@app.route('/notifications', methods=['GET'])
def get_today_notification():
    notification, error = get_formatted_notification()
    if error:
        if error == "No notifications retrieved":
            return jsonify({"message": error}), 404
        return jsonify({"error": error}), 500

    return jsonify(notification), 200

def get_formatted_notification():
    notification, error = fetch_todays_notification()
    if error:
        return None, error

    if notification:
        announce_date = notification['announceDate']
        formatted_date = announce_date.strftime("%B %d, %Y")
        notification['announceDate'] = formatted_date
        return notification, None
    return None, "No notifications retrieved" 

def fetch_todays_notification():
    connection = connectToDB()
    if not connection:
        return None, "Failed to connect to the database"
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT announceDate, source, message FROM cs425.tblNotifications WHERE announceDate >= CURDATE() ORDER BY announceDate ASC LIMIT 1")
        return cursor.fetchone(), None
    except Error as err:
        return None, str(err)
    finally:
        cursor.close()
        connection.close()

# Connect to database
def connectToDB():
    try:
        connection = connect(
            host= "coursecompass-db-instance.c74q40ekci79.us-east-2.rds.amazonaws.com",
            user = "admin",
            passwd = "CourseCompT38!",
            database = "cs425"
        )
        return connection
    except Error as err:
        print("Error while connecting to database", err)
        return None


# Launch backend development server
if __name__ == '__main__':
    app.run(debug=True)
