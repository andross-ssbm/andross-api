from flask import Blueprint

from graphs.graphs import get_basic_elo_graph, get_character_usage_pie

graphs_blueprint = Blueprint('graphs_blueprint', __name__)

graphs_blueprint.route("/get_elo_graph", methods=['GET'])(get_basic_elo_graph)
graphs_blueprint.route("/get_character_graph", methods=['GET'])(get_character_usage_pie)
