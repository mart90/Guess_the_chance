import jwt
import os
import random
from datetime import datetime
from datetime import timedelta
from flask import Flask, request, Response, make_response, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from mysql import *
from decorators import token_required
from config import config
from functions import *
from werkzeug.middleware.proxy_fix import ProxyFix
from user import User


# python -m flask run

app = Flask(__name__, template_folder="../templates")
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_prefix=1
)
if os.name == "nt":
    from flask_cors import CORS
    cors = CORS(app)


@app.route("/backend/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('Missing credentials', 400, {'Authentication': 'login required'})

    mysql = MySQL().connect(mysql_ip, mysql_db)
    mysql.query("SELECT id, password_hash, name, rating, kfactor, is_admin FROM user WHERE name = %s", (auth.username))
    result = mysql.cursor.fetchone()

    if result is None:
        mysql.commit_and_close()
        return make_response('Invalid credentials', 401, {'Authentication': 'login required'})

    user = User(result[0], result[2], result[3], result[4], result[5])
    mysql.commit_and_close()

    if check_password_hash(result[1], auth.password):
        expires_at = datetime.now(datetime.UTC) + timedelta(days=7)
        token = jwt.encode({
            'user_id': user.id,
            'exp': expires_at
        }, config["secret"], "HS256")

        return jsonify({
            'token': token,
            'expires_at': expires_at
        })

    return make_response('Invalid credentials', 401, {'Authentication': 'login required'})


@app.route("/backend/register", methods=["POST"])
def register():
    mysql = MySQL().connect(mysql_ip, mysql_db)
    body = request.json

    values = (
        body["username"],
        generate_password_hash(body["password"]),
        body["email"]
    )

    mysql.query("INSERT INTO user (name, password_hash, email) values (%s, %s, %s)", values)
    mysql.commit_and_close()
    return Response("", 200)


@app.route("/backend/refresh_token", methods=["GET"])
@token_required
def refresh_token(current_user):
    expires_at = datetime.now((datetime.UTC)) + timedelta(days=7)
    token = jwt.encode({
        'user_id': current_user.id,
        'exp': expires_at
    }, config["secret"], "HS256")

    return jsonify({
        'token': token,
        'expires_at': expires_at
    })


@app.route("/backend/events", methods=["GET"])
@token_required
def get_events(current_user):
    mysql = MySQL().connect(mysql_ip, mysql_db)
    mysql.query("""
        SELECT
            ec.name as category,
            e.description,
            e.date_start,
            e.date_close,
            e.date_resolve,
            e.result,
            (SELECT COUNT(*) FROM prediction p WHERE p.event_id = e.id) as prediction_count,
            (SELECT AVG(predicted_probability) FROM prediction p WHERE p.event_id = e.id) as average_prediction,
            (SELECT predicted_probability FROM prediction p WHERE p.event_id = e.id AND user_id = %s) as my_prediction,
            e.id,
            e.date_resolved,
            e.approved,
            pa.user_id as uid_passed
        FROM event e
        JOIN event_category ec ON ec.id = e.category_id
        LEFT JOIN pass pa ON pa.user_id = %s AND pa.event_id = e.id
        WHERE
            (e.approved = 1 OR e.suggested_by = %s OR 1 = %s)
            AND e.result IS NULL""", (current_user.id, current_user.id, current_user.id, current_user.is_admin))
    
    result = [list(row) for row in mysql.cursor.fetchall()]

    for row in result:
        if row[8] is None and row[5] is None and row[12] is None:
            row[7] = None
        del row[-1]      

    mysql.commit_and_close()
    return jsonify(result)


@app.route("/backend/resolved_events", methods=["GET"])
@token_required
def get_resolved_events(current_user):
    mysql = MySQL().connect(mysql_ip, mysql_db)
    mysql.query("""
        SELECT
            ec.name as category,
            e.description,
            e.date_start,
            e.date_close,
            e.date_resolve,
            e.result,
            (SELECT COUNT(*) FROM prediction p WHERE p.event_id = e.id) as prediction_count,
            (SELECT AVG(predicted_probability) FROM prediction p WHERE p.event_id = e.id) as average_prediction,
            (SELECT predicted_probability FROM prediction p WHERE p.event_id = e.id AND user_id = %s) as my_prediction,
            e.id,
            e.date_resolved
        FROM event e
        JOIN event_category ec on ec.id = e.category_id
        WHERE
            e.result IS NOT NULL""", (current_user.id))
    
    result = [list(row) for row in mysql.cursor.fetchall()]   

    mysql.commit_and_close()
    return jsonify(result)


@app.route("/events/<id>", methods=["GET"])
def get_event_view(id):
    return render_template("event.html", eventId=id)


@app.route("/backend/events/<id>", methods=["GET"])
@token_required
def get_event(current_user, id):
    mysql = MySQL().connect(mysql_ip, mysql_db)    
    mysql.query("""
        SELECT
            ec.name as category,
            e.description,
            e.date_start,
            e.date_close,
            e.date_resolve,
            e.resolution,
            e.result,
            (SELECT COUNT(*) FROM prediction p WHERE p.event_id = e.id) as prediction_count,
            (SELECT AVG(predicted_probability) FROM prediction p WHERE p.event_id = e.id) as average_prediction,
            (SELECT predicted_probability FROM prediction p WHERE p.event_id = e.id AND user_id = %s) as my_prediction,
            e.date_resolved,
            e.approved,
            (SELECT user_id FROM pass WHERE user_id = %s AND event_id = %s) as uid_passed
        FROM event e
        JOIN event_category ec on ec.id = e.category_id
        WHERE
            e.id = %s""", (current_user.id, current_user.id, id, id))
    
    event_result = list(mysql.cursor.fetchone())

    mysql.query("SELECT id, name FROM event_category")
    categories = list(mysql.cursor.fetchall())

    avg_prediction = round(event_result[8], 4) if \
        event_result[8] is not None and (
            event_result[9] is not None 
            or event_result[6] is not None 
            or event_result[12] is not None) \
        else None

    event = {
        "category": event_result[0],
        "description": event_result[1],
        "date_start": event_result[2],
        "date_close": event_result[3],
        "date_resolve": event_result[4],
        "date_resolved": event_result[10],
        "resolution": event_result[5],
        "result": event_result[6],
        "prediction_count": event_result[7],
        "average_prediction": avg_prediction,
        "my_prediction": event_result[9],
        "editable": True if current_user.is_admin else False,
        "selectable_categories": categories,
        "approved": event_result[11],
        "passed": True if event_result[12] is not None else False
    }
    
    mysql.commit_and_close()
    return jsonify(event)


@app.route("/backend/events/<id>", methods=["PATCH"])
@token_required
def update_event(current_user, id):
    if not current_user.is_admin:
        return ("Forbidden", 403)
        
    body = request.json

    mysql = MySQL().connect(mysql_ip, mysql_db)

    mysql.query("SELECT result FROM event WHERE id = %s", (id))
    result = mysql.cursor.fetchone()
    if result[0] is not None:
        mysql.commit_and_close()
        return ("Forbidden", 403)

    mysql.query("""
        UPDATE event SET
            description = %s,
            category_id = %s,
            date_start = %s,
            date_close = %s,
            date_resolve = %s,
            resolution = %s
        WHERE id = %s""", (
            body["description"],
            body["category"],
            body["date_start"],
            body["date_close"],
            body["date_resolve"],
            body["resolution"],
            id
        ))

    mysql.commit_and_close()
    return ("", 204)


@app.route("/backend/submitPrediction", methods=["POST"])
@token_required
def submit_prediction(current_user):
    body = request.json
    mysql = MySQL().connect(mysql_ip, mysql_db)

    mysql.query("SELECT date_close FROM event WHERE id = %s", (body["event_id"]))
    result = mysql.cursor.fetchone()
    if result[0] < datetime.now(datetime.UTC):
        mysql.commit_and_close()
        return ("Guessing for this event is closed", 403)
    
    mysql.query("SELECT user_id FROM pass WHERE user_id = %s AND event_id = %s", (current_user.id, body["event_id"]))
    result = mysql.cursor.fetchone()
    if result is not None:
        mysql.commit_and_close()
        return ("You can't guess for this event after passing", 403)
    
    mysql.query("SELECT predicted_probability FROM prediction WHERE event_id = %s AND user_id = %s",
                (body["event_id"], current_user.id))
    result = mysql.cursor.fetchone()
    if result is not None:
        mysql.commit_and_close()
        return ("You can only guess once per event", 403)
    
    prediction = body["my_prediction"]

    if not prediction.replace('.', '').isnumeric() or float(prediction) < 0 or float(prediction) > 100:
        mysql.commit_and_close()
        return ("Invalid guess", 400)

    mysql.query("""
        INSERT INTO prediction (event_id, user_id, predicted_probability)
        VALUES (%s, %s, %s)""", (body["event_id"], current_user.id, round(float(prediction) / 100, 2)))

    mysql.commit_and_close()
    return ("", 204)


@app.route("/backend/resolveEvent", methods=["POST"])
@token_required
def resolve_event(current_user):
    if not current_user.is_admin:
        return ("Forbidden", 403)
    
    body = request.json
    mysql = MySQL().connect(mysql_ip, mysql_db)
        
    mysql.query("SELECT date_close FROM event WHERE id = %s", (body["event_id"]))
    result = mysql.cursor.fetchone()
    if result[0] > datetime.now(datetime.UTC):
        mysql.commit_and_close()
        return ("Predictions for this event are not yet closed", 403)
    
    mysql.query("""
        SELECT 
            p.user_id, 
            p.predicted_probability,
            u.rating,
            u.kfactor
        FROM prediction p
        JOIN user u on u.id = p.user_id
        WHERE p.event_id = %s""", (body["event_id"]))

    result = mysql.cursor.fetchall()

    users = [] 
    for row in result:
        user = User(row[0], None, row[2], row[3], None)
        user.prediction = row[1]
        users.append(user)

    set_new_ratings(users, body["result"])

    for user in users:
        user.update_rating(mysql)
        mysql.query("UPDATE prediction SET new_rating = %s, rating_gained = %s WHERE user_id = %s AND event_id = %s",
                    (user.new_rating, user.rating_gained, user.id, body["event_id"]))
    
    mysql.query("UPDATE event SET result = %s, date_resolved = CURRENT_TIMESTAMP WHERE id = %s",
                (body["result"], body["event_id"]))

    mysql.commit_and_close()
    return ("", 204)


@app.route("/backend/events/<id>/guesses", methods=["GET"])
@token_required
def get_event_guesses(current_user, id):
    mysql = MySQL().connect(mysql_ip, mysql_db)

    mysql.query("""
        SELECT e.result, p.predicted_probability, pa.user_id 
        FROM event e
        LEFT JOIN prediction p ON e.id = p.event_id AND p.user_id = %s
        LEFT JOIN pass pa on pa.event_id = e.id AND pa.user_id = %s
        WHERE e.id = %s""", (current_user.id, current_user.id, id))
    
    result = mysql.cursor.fetchone()
    if result[0] is None and result[1] is None and result[2] is None:
        mysql.commit_and_close()
        return ("Forbidden", 403)

    mysql.query("""
        SELECT 
            u.name, 
            u.rating,
            p.date_added, 
            p.predicted_probability,
            p.rating_gained
        FROM prediction p
        JOIN user u on u.id = p.user_id
        WHERE p.event_id = %s""", (id))
    
    result = mysql.cursor.fetchall()
    
    mysql.commit_and_close()
    return jsonify(result)


@app.route("/backend/categories", methods=["GET"])
@token_required
def get_categories(current_user):
    mysql = MySQL().connect(mysql_ip, mysql_db)

    mysql.query("SELECT id, name FROM event_category")

    result = mysql.cursor.fetchall()

    mysql.commit_and_close()
    return jsonify(result)


@app.route("/backend/events", methods=["POST"])
@token_required
def create_event(current_user):
    body = request.json
    mysql = MySQL().connect(mysql_ip, mysql_db)

    approved = 1 if current_user.is_admin else 0

    mysql.query("""
        INSERT INTO event (
            description, 
            suggested_by, 
            category_id,
            approved,
            resolution,
            date_start,
            date_close,
            date_resolve) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (
            body["description"],
            current_user.id,
            body["category_id"],
            approved,
            body["resolution"],
            body["date_start"],
            body["date_close"],
            body["date_resolve"]
        ))

    id = mysql.cursor.lastrowid

    mysql.commit_and_close()
    return jsonify(id)


@app.route("/backend/events/<id>/approve", methods=["POST"])
@token_required
def approve_event(current_user, id):
    if not current_user.is_admin:
        return ("Forbidden", 403)
    
    mysql = MySQL().connect(mysql_ip, mysql_db)
    mysql.query("UPDATE event SET approved = 1 WHERE id = %s", (id))
    
    mysql.commit_and_close()
    return ("", 204)


@app.route("/backend/leaderboard", methods=["GET"])
@token_required
def get_leaderboard(current_user):    
    mysql = MySQL().connect(mysql_ip, mysql_db)
    mysql.query("""
        SELECT u.name, u.rating, COUNT(*)
        FROM user u
        JOIN prediction p ON p.user_id = u.id
        GROUP BY u.id
        ORDER BY rating DESC, COUNT(*) DESC""")
    
    result = mysql.cursor.fetchall()

    users = []
    for i in range(len(result)):
        users.append({
            "position": i + 1,
            "username": result[i][0],
            "rating": result[i][1],
            "guesses": result[i][2]
        })
    
    mysql.commit_and_close()
    return jsonify(users)


@app.route("/backend/events/<id>/pass", methods=["POST"])
@token_required
def pass_on_event(current_user, id):    
    mysql = MySQL().connect(mysql_ip, mysql_db)

    mysql.query("INSERT INTO pass (user_id, event_id) VALUES (%s, %s)", (current_user.id, id))

    mysql.commit_and_close()
    return ("", 204)
