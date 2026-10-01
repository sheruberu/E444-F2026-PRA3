from datetime import datetime, timezone
from wtforms.validators import DataRequired, Email, ValidationError
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

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



@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        session['email'] = form.email.data
        return redirect(url_for('index'))
    return render_template('index.html', form=form,
                           name=session.get('name'),
                           email=session.get('email'),
                           current_time=datetime.now(timezone.utc))



@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name,
                           current_time=datetime.now(timezone.utc))


if __name__ == '__main__':
    app.run(debug=True)

