from flask import Blueprint
from database.queries import get_users, get_users_by_id, get_users_by_cc, \
    get_elo_by_user_id, get_elo, get_latest_elo, get_latest_characters, \
    get_leaderboard, get_leaderboard_website, create_user, create_elo, create_win_loss, create_drp, create_entry_date, \
    get_user, get_latest_leaderboard_entry, update_user
from database.database_updater import update_database

database_blueprint = Blueprint('database_blueprint', __name__)

database_blueprint.route("/user", methods=['POST'])(create_user)
database_blueprint.route("/update_user", methods=['POST'])(update_user)
database_blueprint.route("/get_user/", methods=['GET'])(get_user)
database_blueprint.route("/users", methods=['GET'])(get_users)
database_blueprint.route("/user_id/", methods=['GET'])(get_users_by_id)
database_blueprint.route("/user_cc/", methods=['GET'])(get_users_by_cc)
database_blueprint.route("/elo_user_id/", methods=['GET'])(get_elo_by_user_id)
database_blueprint.route("/elo/", methods=['POST'])(create_elo)
database_blueprint.route("/elo/", methods=['GET'])(get_elo)
database_blueprint.route("/latest_elo/", methods=['GET'])(get_latest_elo)
database_blueprint.route("/latest_characters/", methods=['GET'])(get_latest_characters)
database_blueprint.route("/entry_date/", methods=['POST'])(create_entry_date)
database_blueprint.route("/win_loss/", methods=['POST'])(create_win_loss)
database_blueprint.route("/drp/", methods=['POST'])(create_drp)
database_blueprint.route("/update/", methods=['POST'])(update_database)
database_blueprint.route("/get_lbe/", methods=['GET'])(get_latest_leaderboard_entry)
database_blueprint.route("/get_leaderboard/", methods=['GET'])(get_leaderboard)
database_blueprint.route("/leaderboard")(get_leaderboard_website)
