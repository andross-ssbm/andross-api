from flask import Blueprint
from database.queries import get_users, get_users_by_id, get_users_by_cc, \
    get_elo_by_user_id, get_elo, get_latest_elo, get_latest_characters, \
    get_leaderboard, create_elo, create_win_loss, create_drp, create_entry_date, \
    get_latest_leaderboard_entry, update_user, get_leaderboard_website_fast
from database.database_updater import update_database, update_leaderboard

database_blueprint = Blueprint('database_blueprint', __name__)

database_blueprint.route("/rest/user/<int:user_id>", methods=['POST'])(update_user)
database_blueprint.route("/rest/users/", methods=['GET'])(get_users)
database_blueprint.route("/rest/user/<int:user_id>", methods=['GET'])(get_users_by_id)
database_blueprint.route("/rest/user/<string:user_cc>", methods=['GET'])(get_users_by_cc)
database_blueprint.route("/rest/elo/user/<int:user_id>", methods=['GET'])(get_elo_by_user_id)
database_blueprint.route("/rest/elo/", methods=['POST'])(create_elo)
database_blueprint.route("/rest/elo/", methods=['GET'])(get_elo)
database_blueprint.route("/rest/elo/user/<int:user_id>/latest", methods=['GET'])(get_latest_elo)
database_blueprint.route("/rest/characters/user/<int:user_id>/latest", methods=['GET'])(get_latest_characters)
database_blueprint.route("/rest/entry_date/", methods=['POST'])(create_entry_date)
database_blueprint.route("/rest/win_loss/", methods=['POST'])(create_win_loss)
database_blueprint.route("/rest/drp/", methods=['POST'])(create_drp)
database_blueprint.route("/rest/update/", methods=['POST'])(update_database)
database_blueprint.route("/rest/update_leaderboard/", methods=['POST'])(update_leaderboard)
database_blueprint.route("/rest/get_lbe/", methods=['GET'])(get_latest_leaderboard_entry)
database_blueprint.route("/rest/get_leaderboard/", methods=['GET'])(get_leaderboard)
database_blueprint.route("/leaderboard")(get_leaderboard_website_fast)
