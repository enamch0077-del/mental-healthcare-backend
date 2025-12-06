# backend/add_values.py
from flask import Blueprint, request, jsonify
from utils import get_db_connection
from flask_cors import cross_origin


add_route = Blueprint('add_route', __name__)
from flask_cors import CORS

@add_route.route('/add-values', methods=['POST'])
def add_values():
    data = request.get_json()
    value1 = data.get("value1")
    value2 = data.get("value2")


    if value1 is None or value2 is None:
        return jsonify({"error": "Both value1 and value2 are required!"}), 400

    result = value1 + value2

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO calculations (value1, value2, result) VALUES (%s, %s, %s)",
            (value1, value2, result)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Values added successfully!",
            "value1": value1,
            "value2": value2,
            "result": result
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
