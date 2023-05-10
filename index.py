from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from models import db, create_character_list, \
    User, CharacterList, EntryDate, Elo, WinLoss, DRP, DGP, Leaderboard, CharactersEntry
from database.routes import database_blueprint

app = Flask(__name__)

app.config.from_object('config.Config')

db.init_app(app)

with app.app_context():
    db.create_all()
    create_character_list()

app.register_blueprint(database_blueprint)


@app.route("/")
def hello_world():
    return 'hello world'


if __name__ == '__main__':
    app.run()
