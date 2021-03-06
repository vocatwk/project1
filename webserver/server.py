#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import random
import json
import datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "vtw2108"
DB_PASSWORD = "ujoxd0ik"

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/w4111"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  if 'uni' in session:
    return redirect(url_for('classes'))

  return render_template("index.html")


@app.route('/signup', methods=['POST'])
def signup():
    if 'uni' in session:
        return redirect(url_for('classes'))
  
    uni = request.form.get('InstructorUNI')
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    if uni != None:
        cmd = 'INSERT INTO instructor(UNI, name, email, password) VALUES (%s, %s, %s, %s)'
        g.conn.execute(cmd, (uni, name,email, password));
        print "inserted %s into table instructor" %(name)
        
        #create offered course
        courseName = request.form['courseName']
        unique  = false
        cmd = 'select * from courses_offered where course_id = %d AND instructor_UNI = %s'
        
        courseId = 0;
        #make sure courseID is no taken
        while(unique != false):
          courseId = random.getrandbits(32)
          cursor = g.conn.execute(cmd, (courseId, uni));
          if cursor.fetchone() == None:
            unique = True

        #insert course
        cmd = 'INSERT INTO courses_offered(course_id, course_name, instructor_UNI) VALUES (%s, %s, %s)'
        g.conn.execute(cmd, (courseId, courseName,uni));
        print "inserted course %s into table courses_offered" %(name)

        session['uni'] = uni
        session['is_instructor'] = True

    else:
        uni = request.form['StudentUNI']
        cmd = 'INSERT INTO students(UNI, name, email, password) VALUES (%s, %s, %s, %s)'
        g.conn.execute(cmd, (uni, name,email, password));
        print "inserted %s into table student" %(name)

        #enroll student in course
        courseId = request.form['courseID']
        instructorUNI = request.form['StudentInstructorUNI']

        cmd = 'INSERT INTO enrolled_students(student_UNI, course_id, instructor_UNI) VALUES (%s, %s, %s)'
        g.conn.execute(cmd, (uni, courseId, instructorUNI));

        print "inserted %s into table enrolled_students" %(name)

        session['uni'] = uni
        session['is_instructor'] = False

    return redirect(url_for('classes'))

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print name
  cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)';
  cursor = g.conn.execute(text(cmd), name1 = name, name2 = name);
  return redirect('/')


@app.route('/login',methods=['POST'])
def login():
  if 'uni' in session:
    return redirect(url_for('classes'))
  
  uni = request.form['UNI']
  password = request.form['password']

  if('asInstructor' in request.form):
    cmd = 'select * from instructor where UNI = %s'
    cursor = g.conn.execute(cmd, (uni));
    if cursor.fetchone()['password'] == password:
      session['uni'] = uni
      session['is_instructor'] = True
      return redirect(url_for('classes'))
    else:
      #incorrect password
      return render_template('index.html')

  else:
    cmd = 'select * from students where UNI = %s'
    cursor = g.conn.execute(cmd, (uni));
    if cursor.fetchone()['password'] == password:
      session['uni'] = uni
      session['is_instructor'] = False
      return redirect(url_for('classes'))
    else:
      #incorrect password
      return render_template('index.html')


@app.route('/logout',methods=['GET'])
def logout():
  session.clear()
  return redirect(url_for('index'))



@app.route('/classes', methods=['POST', 'GET'])
def classes():
    if 'uni' not in session:
        return redirect(url_for('index'))
    uni = session['uni']
    is_instructor = session['is_instructor']
    if is_instructor:
        q ="SELECT course_id, course_name, instructor_uni FROM courses_offered where instructor_uni = %s"
        cursor = g.conn.execute(q,(uni))
    else:
        q= "Select courses.course_id,course_name,courses.instructor_uni from (Select course_id, instructor_uni from enrolled_students where student_uni = %s) as courses, courses_offered where courses.course_id = courses_offered.course_id and courses.instructor_uni = courses_offered.instructor_uni"
        cursor = g.conn.execute(q,(uni))
    classes = []
    for result in cursor:
        classes.append([result['course_id'],result['course_name'],result['instructor_uni']])
    cursor.close()
    input= {'classes':classes, 'is_instructor':is_instructor}

    return render_template ("classes.html", input=input)

@app.route('/classes/<instructorUNI>/<courseID>', methods=['GET', 'POST'])
def course(instructorUNI, courseID):

  #make sure user is logged in and has access to the course
  if 'uni' not in session:
        return redirect(url_for('index'))
  if session['is_instructor'] == True:
    #make sure the courseId is the instructor's
    if session['uni'] != instructorUNI:
      return redirect(url_for('index'));

  else:
    #make sure the student is enrolled in the class
    cmd = 'select * from enrolled_students where course_id = %s AND instructor_UNI = %s AND student_uni = %s'
    cursor = g.conn.execute(cmd,(courseID, instructorUNI, session['uni']))
    if cursor.fetchone() == None:
      return redirect(url_for('index'));

    if request.method == 'POST':
      question = request.form['question']
      #generate questionID
      questionId = 0;
      unique = False;
      cmd  = "select * from questions where question_id = %s AND student_UNI = %s AND course_id = %s AND instructor_UNI = %s"

      #make sure questionID is not taken
      while(unique != True):
        questionId = random.getrandbits(16)
        cursor = g.conn.execute(cmd, (questionId, session['uni'], courseID, instructorUNI));
        if cursor.fetchone() == None:
          unique = True

      cmd = 'Insert into questions(question_id, student_UNI, course_id, instructor_UNI, question, answered, timestamp) values(%s, %s, %s, %s, %s, %s, %s)'
      g.conn.execute(cmd,(questionId, session['uni'], courseID, instructorUNI, question, False, datetime.datetime.utcnow()))


  cmd = 'select q.question_id, q.student_UNI, q.question, q.answered, q.timestamp, (count(*) OVER (partition by q.question_id, q.student_UNI, q.instructor_uni, q.course_id) )as upvotes from questions q left join upvoted_questions uq on q.question_id = uq.question_id AND q.student_UNI = uq.student_UNI AND q.course_id = uq.course_id AND q.instructor_uni = uq.instructor_uni where q.course_id = %s AND q.instructor_UNI = %s order by extract(year from q.timestamp) desc, extract(month from q.timestamp) desc, extract(day from q.timestamp) desc, upvotes desc'
  cursor = g.conn.execute(cmd,(courseID, instructorUNI))

  questions = []
  
  temp = {}
  for row in cursor:
    temp = {'question': row['question'], 'student_UNI': row['student_uni'], 'question_ID' : row['question_id'], 'answered' : row['answered'], 'upvotes': row['upvotes']}
    questions.append(temp)

  input = {'course_id': courseID, 'questions':questions, 'instructor_uni': instructorUNI}
  if request.headers.get('purpose') == 'getQuestions':
    return json.dumps(input)
  return render_template("class.html", input=input)
   
@app.route('/classes/<instructorUNI>/<courseID>/<askerID>/<questionID>', methods=['GET', 'POST'])
def doQuestion(instructorUNI, courseID, askerID, questionID):

  #make sure user is logged in and has access to the course
  if 'uni' not in session:
    return redirect(url_for('index'))

  uni = session['uni']

  if session['is_instructor'] == True:
    #make sure the courseId is the instructor's
    if session['uni'] != instructorUNI:
      return redirect(url_for('index'))

  else:
    #make sure the student is enrolled in the class
    cmd = 'select * from enrolled_students where course_id = %s AND instructor_UNI = %s AND student_uni = %s'
    cursor = g.conn.execute(cmd,(courseID, instructorUNI, session['uni']))
    if cursor.fetchone() == None:
      return redirect(url_for('index'))

  if request.method == 'POST':
    purpose = request.headers.get('purpose')
    print purpose
    if purpose == 'upvote':
      #insert into that upvotedquestions
      q = 'insert into upvoted_questions(upvoter_uni,question_id,student_uni,course_id,instructor_uni)values(%s,%s,%s,%s,%s)'
      g.conn.execute(q,(uni,questionID,askerID,courseID,instructorUNI))
      print 'upvoted!'
      return redirect(url_for('course',instructorUNI = instructorUNI, courseID = courseID))
    elif purpose == 'misunderstand':
      print 'misunderstood!'
      #insert into misunderstands
      q = 'insert into misunderstands(misunderstander_uni,question_id,student_uni,course_id,instructor_uni)values(%s,%s,%s,%s,%s)'
      g.conn.execute(q,(uni,questionID,askerID,courseID,instructorUNI))
      return redirect(url_for('course',instructorUNI = instructorUNI, courseID = courseID))
    elif purpose == 'bookmark':
      #insert into bookmarked
      q = 'insert into bookmarks(bookmarker_uni,question_id,student_uni,course_id,instructor_uni)values(%s,%s,%s,%s,%s)'
      g.conn.execute(q,(uni,questionID,askerID,courseID,instructorUNI))
      print 'bookmarked!'
      return redirect(url_for('course',instructorUNI = instructorUNI, courseID = courseID))
    elif purpose == 'Mark as answered':
      #mark question as answered in table
      q ='update questions set answered=true where question_id = %s';
      g.conn.execute(q,(questionID))
      print 'Answered!'
      return redirect(url_for('course',instructorUNI = instructorUNI, courseID = courseID))

  #return answers to a specific question ordered by upvotes and time
  cmd = 'select q.author_uni, q.question_id, q.student_UNI, q.course_id, q.instructor_UNI, q.answer, q.endorsed, q.timestamp, (count(*) OVER (partition by q.author_uni, q.question_id, q.student_UNI, q.course_id, q.instructor_UNI) ) - 1 as upvotes from answers q left join upvoted_answers uq on q.author_uni = uq.author_uni AND q.question_id = uq.question_id AND q.student_UNI = uq.student_UNI AND q.course_id = uq.course_id AND q.instructor_uni = uq.instructor_uni where q.course_id = %s AND q.instructor_UNI = %s AND q.student_uni = %s AND q.question_id = %s order by extract(year from q.timestamp), extract(month from q.timestamp), extract(day from q.timestamp), upvotes'
  cursor = g.conn.execute(cmd,(courseID, instructorUNI, askerID, questionID))

  answers = []
  
  temp = {}
  for row in cursor:
    temp = {'answer': row['answer'], 'author_uni': row['author_uni'], 'student_UNI': row['student_uni'], 'question_ID' : row['question_id'], 'endorsed' : row['endorsed'], 'upvotes': row['upvotes']}
    answers.append(temp)

  input = {'course_id': courseID,'answers':answers, 'instructor_uni': instructorUNI, 'question_id': questionID, 'student_uni': askerID}
  if request.headers.get('purpose') == 'getAnswers':
    return json.dumps(input)
  return render_template("questions.html", input=input)

"""#for the answers page, we just render them.
@app.route('/questions/<courseID>/<instructorUNI>/<askerID>/<questionID>', methods=['GET', 'POST'])
def doAnswer(instructorUNI, courseID, askerID, questionID):
    #make sure user is logged in and has access to the course
    if 'uni' not in session:
        return redirect(url_for('index'))
    if session['is_instructor'] == True:
        #make sure the courseId is the instructor's
        if session['uni'] != instructorUNI:
            return redirect(url_for('index'))

    else:
    #make sure the student is enrolled in the class
    cmd = 'select * from enrolled_students where course_id = %s AND instructor_UNI = %s AND student_uni = %s'
        cursor = g.conn.execute(cmd,(courseID, instructorUNI, session['uni']))
        if cursor.fetchone() == None:
            return redirect(url_for('index'))
    if request.method == 'POST':
        purpose = request.headers.get('purpose')
        print purpose
        if purpose == 'upvote':
            #insert into that upvotedanswers
            print 'upvoted!'
                redirect(url_for('course'))
        elif purpose == 'endorse':
            #mark answer as endordsed in table
            
            print 'Endorsed!'
            redirect(url_for('course'))


    
    
    return render_template("questions.html", input=input)
"""
@app.route('/delete_class', methods =['POST'])
def delete_class():
    if 'uni' not in session:
        return redirect(url_for('index'))
    uni = session['uni']
    is_instructor = session['is_instructor']
    todelete = request.form['course'].split('_')
    if is_instructor:
        #should delete the specific class they displayed
        q = "DELETE FROM courses_offered WHERE course_id = %s and instructor_uni = %s"
        cursor = g.conn.execute(q,(todelete[0],uni))
        #then go back to the list of classes you are still instructing
    else:
    #should unenroll them from the sopecific class they're in
        q = "DELETE FROM enrolled_students WHERE course_id = %s and instructor_uni = %s and student_uni = %s "
        cursor = g.conn.execute(q,(todelete[0],todelete[1],uni))
        #then go back to the list of classes you are enrolled in
    return redirect(url_for('classes'))

#method for adding a class/enrolling in a class
@app.route('/add_class', methods =['GET','POST'])
def add_class():
    if 'uni' not in session:
        return redirect(url_for('index'))
    uni = session['uni']
    is_instructor = session['is_instructor']
    #if they are instructors, add to courses_offered
    try:
        if is_instructor:
            unique  = False
            courseId = 0;
            #make sure courseID is not taken
            while(unique !=True):
                courseId = random.getrandbits(32)
                q = 'select * from courses_offered where course_id = %s AND instructor_UNI = %s'
                cursor = g.conn.execute(q, (courseId, uni))
                if cursor.fetchone() == None:
                    unique = True
            #insert course
            q = 'Insert into courses_offered(course_id, course_name, instructor_uni) values(%s, %s, %s)'
            g.conn.execute(q,(courseId,request.form['course_name'],uni))
            print(request.form['course_name'])
        else:
            #if student, add to enrolled_students
            q = 'Insert into enrolled_students(student_uni,course_id,instructor_uni) values(%s, %s, %s)'
            g.conn.execute(q,(uni, request.form['course_id'],request.form['instructor_uni']))

        return redirect(url_for('classes'))
    except:
        return redirect(url_for('classes'))

#for the stats page
@app.route('/stats', methods =['GET', 'POST'])
def stats():
    if 'uni' not in session:
        return redirect(url_for('index'))
    uni = session['uni']
    is_instructor = session['is_instructor']
    if not is_instructor:
        return redirect(url_for('classes'))

    if request.form.get('search_query') == None:
        #if we haven't asked for anything, show all the student records and their stats
        q = 'select name, uni, questions, answers from students left outer join (Select qs.student_uni,ans.author_uni, qs.count as questions, ans.count as answers from (select student_uni, count(*) from questions group by student_uni) as qs full outer join (select author_uni, count(*) from answers  group by author_uni) as ans on qs.student_uni =ans.author_uni ) as active on uni = student_uni or uni = author_uni;'
        cursor = g.conn.execute(q)
    else:
        #if they ask for a specific student's data using a search string
        q = "select name, uni,questions, answers from (select name, uni, questions, answers from students left outer join (Select qs.student_uni,ans.author_uni, qs.count as questions, ans.count as answers from (select student_uni, count(*) from questions group by student_uni) as qs full outer join (select author_uni, count(*) from answers  group by author_uni) as ans on qs.student_uni =ans.author_uni ) as active on uni = student_uni or uni = author_uni) as all_entries where all_entries.name like %s or all_entries.uni like %s"#query by the search terms
        search_term = request.form['search_query']
        like_pattern = '%{}%'.format(search_term)
        cursor = g.conn.execute(q,(like_pattern,like_pattern))
    input = []
    for result in cursor:
        input.append(result)
    cursor.close()
    return render_template("stats.html", input=input)

#for the bookmarks page
@app.route('/student_bookmarks', methods =['GET', 'POST'])
def student_bookmarks():
    if 'uni' not in session:
        return redirect(url_for('index'))
    uni = session['uni']
    is_instructor = session['is_instructor']
    if is_instructor:
        return redirect(url_for('classes'))

    q = 'select distinct questions.course_id,questions.question_id, question, timestamp from questions, bookmarks where bookmarker_uni = %s and questions.question_id = bookmarks.question_id'
    cursor = g.conn.execute(q,(uni))
    input = []
    for result in cursor:
        input.append(result)
        cursor.close()
    return render_template("student_bookmarks.html", input=input)
#include at top of the page a link to your classes page

                               
if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
