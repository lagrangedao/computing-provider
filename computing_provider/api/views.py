import logging
from flask import render_template, Blueprint, jsonify

from computing_provider.api.node_service import generate_node_id

views_blueprint = Blueprint("views", __name__)


@views_blueprint.get("/")
def home():
    return render_template("index.html")


@views_blueprint.route('/boot', methods=['GET'])
def generate_key():
    node_id = generate_node_id()
    logging.info("Node id: %s" % node_id)
    return jsonify({'node_id': node_id})



