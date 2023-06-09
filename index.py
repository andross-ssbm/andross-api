from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import db, create_character_list, \
    User, CharacterList, EntryDate, Elo, WinLoss, DRP, DGP, Leaderboard, CharactersEntry
from database.routes import database_blueprint
from graphs.routes import graphs_blueprint

app = Flask(__name__)

app.config.from_object('config.Config')

with app.app_context():
    db.init_app(app)
    db.create_all()
    create_character_list()

app.register_blueprint(database_blueprint)
app.register_blueprint(graphs_blueprint)


@app.route("/")
def hello_world():
    return 'hello world'


if __name__ == '__main__':
    with app.app_context():
        app.run(host='0.0.0.0')
