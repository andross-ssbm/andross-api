from flask import Flask, render_template
from flask_migrate import Migrate

from custom_logging import CustomFormatter

logger = CustomFormatter().get_logger()

# Ignore unused imports needed for migrations
from models import db, create_character_list, Seasons, User, Elo, EntryDate, CharacterList, CharactersEntry, DRP, DGP, Leaderboard
from database.routes import database_blueprint
from graphs.routes import graphs_blueprint

app = Flask(__name__)

app.config.from_object('config.Config')

def create_app():
    db.init_app(app)
    create_character_list()
    migrate = Migrate(app, db)
    migrate.init_app(app)


with app.app_context():
    db.init_app(app)
    create_character_list()
    migrate = Migrate(app, db)
    migrate.init_app(app)

app.register_blueprint(database_blueprint)
app.register_blueprint(graphs_blueprint)


@app.route("/")
def hello_world():
    return render_template('index.html')


@app.teardown_request
def teardown_request(exception=None):
    db.session.remove()
    if exception and db.session.is_active:
        print('Experienced error')
        print(exception)
        db.session.rollback()


if __name__ == '__main__':
    with app.app_context():
        app.run(host='0.0.0.0')
