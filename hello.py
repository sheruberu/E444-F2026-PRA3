import re
from datetime import datetime, timezone

from flask import (Flask, render_template, session, redirect, url_for, flash,
                   request, jsonify)
from flask_bootstrap import Bootstrap5
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, ValidationError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ece444-pra3-secret-key'
bootstrap = Bootstrap5(app)
moment = Moment(app)


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    email = StringField('What is your UofT email?',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')

    def validate_email(self, field):
        if 'utoronto' not in field.data.lower():
            raise ValidationError(
                'Please fill in a UofT email address (it must contain "utoronto").')


def generate_reply(message):
    """Produce a reply and update what the bot remembers.

    Everything the bot "knows" lives in session['memory'], which Flask stores
    in a signed cookie in the user's browser.
    """
    text = message.strip()
    lower = text.lower()
    memory = session.get('memory', {})
    reply = None

    # remember: "my name is X"
    match = re.search(r"my name is\s+([A-Za-z][\w'-]*)", text, re.I)
    if match:
        memory['name'] = match.group(1)
        reply = 'Nice to meet you, ' + match.group(1) + '!'

    # remember: "my favourite X is Y"
    if reply is None:
        match = re.search(r"my favou?rite\s+(.+?)\s+is\s+(.+)", text, re.I)
        if match:
            key = match.group(1).strip().lower()
            value = match.group(2).strip().rstrip('.!')
            memory[key] = value
            reply = 'Got it, your favourite ' + key + ' is ' + value + '.'

    # recall: "what is my name"
    if reply is None and re.search(r"what(?:'s| is) my name", lower):
        if 'name' in memory:
            reply = 'Your name is ' + memory['name'] + '.'
        else:
            reply = 'I do not know your name yet. Tell me "My name is ...".'

    # recall: "what is my favourite X"
    if reply is None:
        match = re.search(r"what(?:'s| is) my favou?rite\s+(.+?)\s*\??$", lower)
        if match:
            key = match.group(1).strip()
            if key in memory:
                reply = 'Your favourite ' + key + ' is ' + memory[key] + '.'
            else:
                reply = 'I do not know your favourite ' + key + ' yet.'

    # fallbacks - the starter endpoint's original behaviour
    if reply is None:
        if 'hello' in lower or 'hi' in lower:
            reply = 'Hello!'
        else:
            reply = "I don't understand."

    # Reassigning (not just mutating) is what marks the session as changed.
    session['memory'] = memory

    history = session.get('history', [])
    history.append({'role': 'user', 'text': text})
    history.append({'role': 'bot', 'text': reply})
    session['history'] = history[-20:]   # cookies cap at ~4KB, so bound it

    return reply


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        session['email'] = form.email.data
        return redirect(url_for('chat'))
    return render_template('index.html', form=form,
                           name=session.get('name'),
                           email=session.get('email'),
                           current_time=datetime.now(timezone.utc))


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        if 'email' not in session:
            return jsonify({'reply': 'Please sign in from the home page first.'}), 401
        message = request.json['message']
        return jsonify({'reply': generate_reply(message)})

    if 'email' not in session:
        return redirect(url_for('index'))
    return render_template('chat.html',
                           name=session.get('name'),
                           email=session.get('email'),
                           history=session.get('history', []))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name,
                           current_time=datetime.now(timezone.utc))


if __name__ == '__main__':
    app.run(debug=True)
