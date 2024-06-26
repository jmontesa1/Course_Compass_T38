/*Search by department*/
delimiter //
create procedure SearchDepartments(in search_term varchar(255))
beign
    select distinct 
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
    from 
        vwCourseDetails
    where 
        courseMajor like concat(search_term, '%')
        and term = '2024 Fall'
    order by
        cast(substring(courseCode, locate(' ', courseCode) + 1) as unsigned),
        substring(courseCode, 1, locate(' ', courseCode) - 1);
end//
delimiter ;

/*Use case*/
call SearchDepartments('math')
call SearchDepartments('computer')

-----------------------------------------------------------------------------------------------------------------------------------------------------

/*query for student enrolled courses*/
delimiter //
create procedure GetEnrolledCourses(
    in p_studentID int
)
begin
    select 
		cs.scheduleID,
        cs.courseCode as course,
        cs.meetingDays as days,
        cs.meetingTimes as time,
        TIME_FORMAT(cs.startTime, '%l:%i %p') as start,
        TIME_FORMAT(cs.endTime, '%l:%i %p') as end,
        cs.Location as location
    from 
        tblUserSchedule us
    join 
        tblcourseSchedule cs ON us.scheduleID = cs.scheduleID
    where 
        us.studentID = p_studentID
        and cs.semesterID = (
            select semesterID 
            from tblSemesters
            where startDate > CURDATE()--courses for next semester, use '<' for current semester
            order by startDate asc
            limit 1
        );
end //
delimiter ;

/*use case*/
call GetEnrolledCourses(1)--studentID as argument
-----------------------------------------------------------------------------------------------------------


/*student unenrolls from a course*/
delimiter //
create procedure UnenrollCourse(
    in p_studentID int,
    in p_scheduleID int
)
begin
    declare v_enrollmentTotal int;
    declare v_availableSeats int;
    
    --Delete the enrollment record from tblUserSchedule
    delete from tblUserSchedule
    where studentID = p_studentID and scheduleID = p_scheduleID;
    
    --Get the current enrollment total and available seats for the course
    select enrollmentTotal, availableSeats
    into v_enrollmentTotal, v_availableSeats
    from tblcourseSchedule
    where scheduleID = p_scheduleID;
    
    --Update the enrollment total and available seats in tblCourseSchedule
    update tblcourseSchedule
    set enrollmentTotal = v_enrollmentTotal - 1,
        availableSeats = v_availableSeats + 1
    where scheduleID = p_scheduleID;

    commit;
end //
delimiter ;

/*use case*/
call UnenrollCourse(1, 508)--studentID 1 drops course with scheduleID 508 in tblcourseSchedule
-------------------------------------------------------------------------------------------------------------------



/*Get users courses with their email for their Major progress*/
delimiter //
create procedure GetCoursesForProgress(
    in userEmail varchar(255)
)
begin
    select c.courseID, c.courseName, c.courseCode, c.Credits, c.Level, m.majorName, m.creditsReq, 
           coalesce(ucc.isCompleted, 0) as isCompleted --coalesce returns completed as 1 or 0 if null
    from tblCourses c
    join tblMajor m on c.majorID = m.majorID
    left join tblUserCompletedCourses ucc on c.courseID = ucc.courseID and m.majorID = ucc.majorID and ucc.Email = userEmail
    where m.majorID = (
        select majorID
        from tblUser
        where Email = userEmail
    );
end //
delimiter ;


/*use case*/
call GetCoursesForProgress('jose@gmail.com');

---------------------------------------------------------------------------------------------------------------------------------------------------
/*Post a course as completed takes in 5 arguments*/
delimiter $$
create procedure `MarkCourseCompleted`(
    in userEmail varchar(150),
    in courseCode varchar(25),
    in isCompleted boolean,
    in reviewText text,
    in selectedTags json,
    in ratingValue int --added ratingValue 
)
begin
    declare v_courseID int;
    declare v_majorID int;
    declare v_studentID int;
    declare v_ratingID int;

    --Find courseID based on courseCode
    select c.courseID into v_courseID
    from cs425.tblCourses c
    where c.courseCode = courseCode
    limit 1;

    --Find studentID and majorID based on userEmail
    select s.studentID, s.majorID into v_studentID, v_majorID
    from cs425.tblStudents s
    join cs425.tblUser u on s.userID = u.userID
    where u.Email = userEmail
    limit 1;

    --Update or insert the course completion record
    insert into cs425.tblUserCompletedCourses (Email, courseID, courseCode, isCompleted, completionDate, majorID, studentID)
    values (userEmail, v_courseID, courseCode, isCompleted, curdate(), v_majorID, v_studentID)
    on duplicate key update
        isCompleted = values(isCompleted),
        completionDate = values(completionDate);

    --Insert or update the rating record including the rating column
    insert into cs425.tblRatings (courseID, studentID, rating, ratingText, ratingDate)
    values (v_courseID, v_studentID, ratingValue, reviewText, curdate())
    on duplicate key update
        rating = values(rating),
        ratingText = values(ratingText),
        ratingDate = values(ratingDate);

    --Get the ratingID of the inserted or updated rating
    set v_ratingID = last_insert_id();

    --delete existing tags for the rating
    delete from cs425.tblRatingTags where ratingID = v_ratingID;

    --insert the selected tags for the rating
    insert into cs425.tblRatingTags (ratingID, tagID)
    select v_ratingID, tagID
    from json_table(selectedTags, '$[*]' columns (tagID int path '$')) as selectedTags
    where exists (
        select 1
        from cs425.tblTags
        where tagID = selectedTags.tagID
    );
end$$
delimiter ;



---------------------------------------------------------------------------------------------------------------------------------------------------
delimiter //
create procedure `GetMajorCompletionStatus`(
    in userEmail varchar(150)
)
begin
    select 
        c.courseID, 
        c.courseName, 
        c.courseCode,
        c.Credits,
        (ucc.courseID is not null) as isCompleted -- 1 (true) if completed, 0 (false) if not
    from 
        tblCourses c
    join 
        tblMajor m on c.majorID = m.majorID
    left join 
        tblUserCompletedCourses ucc on c.courseID = ucc.courseID and ucc.Email = userEmail
    where 
        m.majorID = (
            select majorID 
            from tblUser 
            where Email = userEmail
        );
end//
delimiter ;


/*use case*/

call GetMajorCompletionStatus('jose@gmail.com')

---------------------------------------------------------------------------------------------------------------------------------------------------

/*Retrives a user's current courses witht their email as argument*/
delimiter //
create procedure `GetUserSchedule`(
    in userEmail varchar(150)
)
begin
    select 
        u.Email, 
        u.Fname, 
        u.Lname, 
        cs.courseCode, 
        cs.Section, 
        cs.Credits, 
        cs.Term, 
        cs.startDate, 
        cs.endDate, 
        cs.meetingDays, 
        cs.meetingTimes, 
        cs.Location, 
        cs.Instructor, 
        cs.meetingFormat
    from 
        cs425.tblUserSchedule us
    join 
        cs425.tblcourseSchedule cs on us.scheduleID = cs.scheduleID
    join 
        cs425.tblUser u on us.Email = u.Email
    where 
        u.Email = userEmail
    and 
        cs.startDate <= curdate() 
    and 
        cs.endDate >= curdate();
end //
delimiter ;


/*use case*/
call GetUserSchedule('jose@gmail.com')
---------------------------------------------------------------------------------------------------------------------------------------------------









/*Get users by major*/
delimiter //
create procedure GetUsersByMajor (
    in p_majorName varchar(50)
)
begin
    select U.userID, U.Fname, U.Lname, S.username, S.majorName
    from cs425.tblUser U
    join cs425.tblStudents S on U.userID = S.userID
    where S.majorName = p_majorName;
end //
delimiter ;

/*Use case*/
call GetUsersByMajor('Computer Science')

/*Get users by role*/
delimiter //
create procedure GetUsersByRole (
    in p_roleTitle varchar(50)
)
begin
    select U.userID, U.Fname, U.Lname, R.title
    from cs425.tblUser U
    join cs425.tblRoles R on U.userID = R.userID
    where R.title = p_roleTitle;
end //
delimiter ;

/*Use case*/
call GetUsersByRole('Student')

/*Get students major*/
delimiter //
create procedure GetStudentsMajor (
    in p_Fname varchar(100),
    in p_Lname varchar(100)
)
begin
    select U.Fname, U.Lname, S.majorName
    from cs425.tblUser U
    join cs425.tblStudents S on U.userID = S.userID
    where U.Fname = p_Fname and U.Lname = p_Lname;
end //
delimiter ;

/*Use case*/
call GetStudentsMajor('Jose', 'Urrutia')

/*Update user email*/
delimiter //
create procedure UpdateUserEmail (
    in p_userID int,
    in p_newEmail varchar(150)
)
begin
    update cs425.tblUser
    set Email = p_newEmail
    where userID = p_userID;
end //
delimiter ;

/*Use case*/
call UpdateUserEmail(1, 'newemail@gmail.com');

--------------------------------------------------------------------------------------------------------------------------------------------------------
/*stored procedure for searching departments*/
delimiter //
create procedure SearchDepartments(in search_term varchar(255))
begin
    select distinct courseName, courseCode, courseMajor, department, professor, term, format, units, meetingTime, Location, days
    from vwCourseDetails
    where courseMajor LIKE concat(search_term, '%')
    order by 
        cast(substring(courseCode, locate(' ', courseCode) + 1) AS unsigned),
        substring(courseCode, 1, locate(' ', courseCode) - 1);
end //
delimiter ;
---------------------------------------------------------------------------------------------------------------------------------------------------------