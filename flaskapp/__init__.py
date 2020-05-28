from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from collections import Counter
from statistics import mean
from flask_login import current_user

def best_emotion(data):
    max_key = max(data['faceAttributes']['emotion'], key=data['faceAttributes']['emotion'].get)
    return max_key

def emotion(blocks,hour=404):
    blks=[]
    for block in blocks:
        if block.author == current_user:
            if hour == 404:
                blks.append(block.output['faceAttributes']['emotion'])
            elif hour == int(block.date_posted.strftime('%H')):
                blks.append(block.output['faceAttributes']['emotion'])
    sums = Counter()
    counters = Counter()
    for blk in blks:
        sums.update(blk)
        counters.update(blk.keys())
    val = {x: f'{round(float((sums[x])/counters[x])*100,2)}%' for x in sums.keys()}
    if val:
        return val
    else:
        return 'No info'

def avg_session(data):
    vals=[]
    for session in data:
        if session.author == current_user:
            vals.append(session.session)
    try:
        new_avg=int(round(mean(vals),0))
    except:
        new_avg = ''
    return new_avg

def avg_session_emotion(data,emotion):
    vals=[]
    for session in data:
        if session.author == current_user:
            max_key = max(session.output['faceAttributes']['emotion'], key=session.output['faceAttributes']['emotion'].get)
            if emotion == max_key:
                vals.append(session.session)
    try:
        new_avg=mean(vals)
    except:
        new_avg = 0
    return new_avg


app = Flask(__name__)
app.config['SECRET_KEY'] = 'a2abb971eb53ec8be5d89a87ef967829'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
db=SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager=LoginManager(app)
login_manager.login_view='login'
login_manager.login_message_category = 'info'
app.jinja_env.globals.update(best_emotion=best_emotion)
app.jinja_env.globals.update(emotion=emotion)
app.jinja_env.globals.update(avg_session=avg_session)
app.jinja_env.globals.update(avg_session_emotion=avg_session_emotion)



from flaskapp import routes