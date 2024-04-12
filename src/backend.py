# Created by Lucas Videtto
# Backend functionality for Course Compass

from flask import Flask, jsonify, request, session
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from mysql.connector import connect, Error
from datetime import datetime
from flask_bcrypt import Bcrypt
import logging, json
from urllib.parse import unquote


app = Flask(__name__)
app.secret_key = '123456789' # Change key to secure value for production environment
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
CORS(app, supports_credentials=True)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)


# User class to store user information
class User:
    def __init__(self, userID=None, Fname=None, Lname=None, DOB=None, Email=None, majorName=None, majorID=None, studentID=None):
        self.userID = userID
        self.Fname = Fname
        self.Lname = Lname
        self.DOB = DOB
        self.Email = Email
        self.majorName = majorName
        self.majorID = majorID
        self.studentID = studentID

    @staticmethod
    def get_user_by_email(email):
        connection = connectToDB()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT u.userID, u.Fname, u.Lname, u.DOB, u.Email, s.majorID, m.majorName, s.studentID
                FROM tblUser u
                LEFT JOIN tblStudents s ON u.userID = s.userID
                LEFT JOIN tblMajor m ON s.majorID = m.majorID
                WHERE u.Email = %s
            """, (email,))
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
        return {
            "userID": self.userID,
            "Fname": self.Fname,
            "Lname": self.Lname,
            "DOB": self.DOB.strftime('%Y-%m-%d') if self.DOB else None,
            "Email": self.Email,
            "majorID": self.majorID,
            "majorName": self.majorName,
            "studentID": self.studentID
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
            cursor.execute("SELECT userID, Email, Passwd, role FROM tblUser WHERE Email = %s", (email,))
            user = cursor.fetchone()
            
            if user and bcrypt.check_password_hash(user['Passwd'], password):
                session['email'] = email
                
                print("LOGIN SUCCESSFUL")

                role = user['role']
                
                access_token = create_access_token(identity={"email": user['Email'], "userID": user['userID'], "role": role})
                return jsonify({"message": "Login successful", "access_token": access_token, "role": role}), 200
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
            cursor.execute("INSERT INTO tblUser (Fname, Lname, DOB, Email, Passwd, role) VALUES (%s, %s, %s, %s, %s, %s)", (fname, lname, dob, email, hashed_pw, userType))
            
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
    

# Retrive user schedule
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
                "startTime": str(schedule[3]),
                "endTime": str(schedule[4]),
                "Location": schedule[5],
                "Term": schedule[6],
                "Credits": schedule[7]
            }
            schedule_list.append(schedule_dict)

        return schedule_list
    except Error as err:
        print("Error while fetching user schedule:", err)
        return None
    

#get user enrolled courses
@app.route('/getEnrolledCourses', methods=['GET'])
@jwt_required()
def get_enrolled_courses():
    try:
        current_user_email = get_jwt_identity()['email']
        user = User.get_user_by_email(current_user_email)
        if not user or not user.studentID:
            return jsonify({"message": "User not found or not a student"}), 400

        connection = connectToDB()
        cursor = connection.cursor()

        query = """
        SELECT 
            cs.scheduleID,
            cs.courseCode AS course,
            c.courseName,
            cs.meetingDays AS days,
            cs.meetingTimes AS time,
            TIME_FORMAT(cs.startTime, '%l:%i %p') AS start,
            TIME_FORMAT(cs.endTime, '%l:%i %p') AS end,
            cs.Location AS location,
            cs.Instructor AS instructor,
            cs.Section,
            c.Credits
        FROM
            tblUserSchedule us
        JOIN
            tblcourseSchedule cs ON us.scheduleID = cs.scheduleID
        JOIN
            tblCourses c ON cs.courseID = c.courseID
        WHERE
            us.studentID = %s
            AND cs.startDate <= CURDATE()
            AND cs.endDate >= CURDATE();
            );
        """
        cursor.execute(query, (user.studentID,))
        result = cursor.fetchall()
        enrolled_courses = [
            {
                'scheduleID': course[0],
                'course': course[1],
                'courseName': course[2],
                'days': course[3].split(',') if course[3] else [],
                'time': course[4],
                'start': course[5],
                'end': course[6],
                'location': course[7],
                'instructor': course[8],
                'Credits': course[10],
                'Section': course[9],
            }
            for course in result
        ]

        return jsonify({"enrolledCourses": enrolled_courses}), 200
    except Error as e:
        print(e)
        return jsonify({"message": "Error fetching enrolled courses"}), 500
    finally:
        cursor.close()
        connection.close()


#  unenroll from course
@app.route('/unenrollCourse', methods=['POST'])
@jwt_required()
def unenroll_course():
    try:
        current_user_email = get_jwt_identity()['email']
        user = User.get_user_by_email(current_user_email)
        
        if not user or not user.studentID:
            return jsonify({"message": "User not found or not a student"}), 400
        
        schedule_id = request.json.get('scheduleID')
        if not schedule_id:
            return jsonify({"message": "Schedule ID is required"}), 400
        
        connection = connectToDB()
        cursor = connection.cursor()
        
        cursor.callproc('UnenrollCourse', [user.studentID, schedule_id])
        connection.commit()
        
        return jsonify({"message": "Course unenrolled successfully"}), 200
    except Error as e:
        print(e)
        return jsonify({"message": "Error unenrolling course"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
            

#get review tags
@app.route('/getTags', methods=['GET'])
def get_tags():
    connection = connectToDB()
    if not connection:
        return jsonify({"error": "DB connection failed"}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT tagID, tagName FROM tblTags")
        tags = cursor.fetchall()
        
        tag_list = [{"id": tag[0], "name": tag[1]} for tag in tags]
        
        return jsonify({"tags": tag_list}), 200
    except Error as err:
        return jsonify({"error": f"Error retrieving tags: {err}"}), 500
    finally:
        cursor.close()
        connection.close()


#mark a course as completed
@app.route('/markCourseCompleted', methods=['POST'])
@jwt_required()
def mark_course_completed_endpoint():
    try:
        identity = get_jwt_identity()
        user_email = identity['email']
        data = request.get_json()
        course_code = data.get('courseCode')
        completed = data.get('completed')
        review = data.get('review')
        student_rating = data.get('studentRating')
        tags = data.get('tags')

        app.logger.info(f"Received tags from frontend: {tags}")  #log the received tags

        success, message = mark_course_completed(user_email, course_code, completed, review, tags, student_rating)
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        app.logger.error(f"Error in mark_course_completed_endpoint: {str(e)}")
        return jsonify({"error": "An internal server error occurred"}), 500
    

def mark_course_completed(user_email, course_code, completed, review, tags, student_rating):
    try:
        connection = connectToDB()
        if not connection:
            return False, "DB connection failed"

        cursor = connection.cursor()
        cursor.callproc('MarkCourseCompleted', [user_email, course_code, completed, review, json.dumps(tags), student_rating])
        connection.commit()
        return True, "Course marked as completed successfully"
    except Error as err:
        app.logger.error(f"Error in mark_course_completed: {str(err)}")
        connection.rollback()
        return False, f"Error marking course as completed: {str(err)}"
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
                #"majorName": user.majorName,
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
    

#get career variables for progress page (left hand side of page)
@app.route('/getCareerProgress', methods=['GET'])
@jwt_required()
def get_career_progress():
    identity = get_jwt_identity()
    current_user_email = identity['email']
    user = User.get_user_by_email(current_user_email)

    if not user or not user.studentID:
        return jsonify({"error": "User not found or not a student"}), 404

    connection = connectToDB()
    if connection:
        cursor = connection.cursor()
        try:
            query = """
            SELECT 
                SUM(c.Credits) as TotalCredits,
                cs.Term,
                g.cumulativeGPA
            FROM 
                tblUserSchedule us
            JOIN
                tblcourseSchedule cs ON us.scheduleID = cs.scheduleID
            JOIN
                tblCourses c ON cs.courseID = c.courseID
            LEFT JOIN
                (
                    SELECT
                        studentID,
                        cumulativeGPA
                    FROM
                        tblGPA
                    WHERE
                        (studentID, semesterID) IN (
                            SELECT
                                studentID,
                                MAX(semesterID)
                            FROM
                                tblGPA
                            GROUP BY
                                studentID
                        )
                ) g ON us.studentID = g.studentID
            WHERE
                us.studentID = %s
                AND cs.startDate <= CURDATE()
                AND cs.endDate >= CURDATE()
            GROUP BY
                cs.Term, g.cumulativeGPA;
            """
            cursor.execute(query, (user.studentID,))
            result = cursor.fetchone()

            if result:
                total_credits, term, cumulative_gpa = result
                return jsonify({
                    "majorName": user.majorName,
                    "totalCredits": total_credits,
                    "Term": term,
                    "cumulativeGPA": cumulative_gpa if cumulative_gpa is not None else 0.00
                }), 200
            else:
                return jsonify({"error": "No career progress found for the current term"}), 404
        except Error as err:
            return jsonify({"error": "Error while fetching career progress: " + str(err)}), 500
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
    level_param = request.args.get('level', None)
    start_time_param = request.args.get('startTime', None)
    format_param = request.args.get('format', None)
    location_param = request.args.get('location', None)
    term_param = request.args.get('term', None)
    default_param = request.args.get('default', None)
    
    connection = connectToDB()
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            query = """
            SELECT DISTINCT 
                scheduleID,
                courseName,
                courseCode,
                courseMajor,
                department,
                professor,
                term,
                format,
                units,
                meetingTime,
                Location,
                days,
                classCapacity,
                enrollmentTotal,
                availableSeats
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER(PARTITION BY courseName ORDER BY courseCode) AS rn,
                    CAST(SUBSTRING(courseCode, LOCATE(' ', courseCode) + 1) AS UNSIGNED) AS numericCourseLevel
                FROM vwCourseDetails
                WHERE 1=1
            ) AS courses
            WHERE 1=1
            """
            
            params = []
            filters_applied = False
            applied_filters = {}
            
            if 'query' in request.args and query_param:
                applied_filters['query'] = query_param
                query += " AND courseMajor LIKE %s"
                params.append(f"{query_param}%")
                filters_applied = True
            
            if 'level' in request.args and level_param:
                applied_filters['query'] = query_param
                level = level_param.rstrip('+')
                numeric_level = int(level)
                query += " AND numericCourseLevel >= %s"
                params.append(numeric_level)
                filters_applied = True
            
            if 'startTime' in request.args and start_time_param:
                applied_filters['query'] = query_param
                start_time_param = unquote(request.args.get('startTime', ''))
                start_time_range = start_time_param.split('-')
                start_time_lower = datetime.strptime(start_time_range[0].strip(), '%I').time()
                end_time_value = start_time_range[1].strip().split(' ')[0]  # Extract the end time value
                start_time_upper = datetime.strptime(end_time_value, '%I').time()
                query += " AND TIME_FORMAT(LEFT(meetingTime, LOCATE('-', meetingTime) - 1), '%H:%i') BETWEEN TIME_FORMAT(%s, '%H:%i') AND TIME_FORMAT(%s, '%H:%i')"
                params.extend([start_time_lower, start_time_upper])
                filters_applied = True
            
            if 'format' in request.args and format_param:
                applied_filters['query'] = query_param
                query += " AND format = %s"
                params.append(format_param)
                filters_applied = True
            
            if 'location' in request.args and location_param:
                applied_filters['query'] = query_param
                query += " AND LEFT(Location, LOCATE(' ', Location) - 1) = %s"
                params.append(location_param)
                filters_applied = True

            if 'term' in request.args and term_param:
                applied_filters['query'] = query_param
                query += " AND term = %s"
                params.append(term_param)
                filters_applied = True
            
            if not filters_applied:
                query += " AND rn = 1"
            
            query += """
            ORDER BY
                CAST(SUBSTRING(courseCode, LOCATE(' ', courseCode) + 1) AS UNSIGNED),
                SUBSTRING(courseCode, 1, LOCATE(' ', courseCode) - 1);
            """
            
            print("Query Parameters:", params)

            cursor.execute(query, tuple(params))
            result = cursor.fetchall()       
            departments = [{
                'scheduleID': dept['scheduleID'],
                'professor': dept['professor'],
                'courseName': dept['courseName'],
                'courseCode': dept['courseCode'],
                'courseMajor': dept['courseMajor'],
                'department': dept['department'],
                'term': dept['term'],
                'format': dept['format'],
                'units': dept['units'],
                'meetingTime': dept['meetingTime'],
                'Location': dept['Location'],
                'days': dept['days'],
                'classCapacity': dept['classCapacity'],
                'enrollmentTotal': dept['enrollmentTotal'],
                'availableSeats': dept['availableSeats']
            } for dept in result]
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
        user = User.get_user_by_email(current_user_email)

        if not user or not user.studentID:
            return jsonify({"message": "User not found or not a student"}), 400

        schedule_ids = request.json.get('scheduleIDs', [])
        if not schedule_ids:
            return jsonify({"message": "No scheduleIDs provided"}), 400

        connection = connectToDB()
        cursor = connection.cursor()

        print(schedule_ids)

        added_schedule_ids = []

        try:
            cursor.execute("START TRANSACTION")

            for schedule_id in schedule_ids:
                cursor.execute("""
                    SELECT availableSeats, courseCode
                    FROM tblcourseSchedule
                    WHERE scheduleID = %s
                    FOR UPDATE
                """, (schedule_id,))

                result = cursor.fetchone()

                if result:
                    availableSeats, course_code = result

                    if availableSeats <= 0:
                        raise Exception(f"Course {course_code} has no available seats")

                    cursor.execute("""
                        INSERT INTO tblUserSchedule (studentID, scheduleID)
                        VALUES (%s, %s)
                    """, (user.studentID, schedule_id))

                    cursor.execute("""
                        UPDATE tblcourseSchedule
                        SET enrollmentTotal = enrollmentTotal + 1,
                            availableSeats = availableSeats - 1
                        WHERE scheduleID = %s
                    """, (schedule_id,))

                    print(f"Course with scheduleID {schedule_id} added to user schedule")
                    added_schedule_ids.append(schedule_id)
                else:
                    print(f"Course with scheduleID {schedule_id} not found in tblcourseSchedule")

            cursor.execute("COMMIT")
            return jsonify({
                "message": "Courses enrollment processed",
                "added_schedule_ids": added_schedule_ids
            }), 200
        except Exception as e:
            cursor.execute("ROLLBACK")
            print(e)
            return jsonify({"message": str(e)}), 400
    except Error as e:
        print(e)
        return jsonify({"message": "Error adding courses"}), 500
    finally:
        cursor.close()
        connection.close()


#retrieve notifications for banner
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
