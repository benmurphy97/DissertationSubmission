from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class SearchMovieForm(FlaskForm):
    search_input = StringField('Title')
    search_button = SubmitField('Search')

class AlgorithmForm(FlaskForm):

    movie_id1 = HiddenField(validators=[DataRequired()])
    movie_rating1 = SelectField(u'Movie Rating 1', 
                                choices=[('First', 'Haven\'t seen it'), ('Second', '1'), ('Third', '5')],
                                default='First',
                                coerce=str) #default must match value

    movie_id2 = HiddenField(validators=[DataRequired()])
    movie_rating2 = SelectField(u'Movie Rating 2',  
                                choices=[('First', 'Haven\'t seen it'), ('Second', '1'), ('Third', '5')],
                                default='First',
                                coerce=str
                                ) #default must match value

    NextPage = SubmitField('Next')
