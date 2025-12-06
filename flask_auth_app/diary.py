# diary.py → ULTIMATE FINAL VERSION (100% WORKING)

from flask import Blueprint, request, jsonify
from utils import get_db_connection
from flask_jwt_extended import decode_token as jwt_decode_token

diary_bp = Blueprint('diary', __name__, url_prefix='/api/diary')

def get_user_id_from_token():
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return None
    token = auth.split(" ")[1]
    try:
        payload = jwt_decode_token(token)
        return int(payload['sub'])
    except:
        return None

@diary_bp.route('/', methods=['GET'])
def get_notes():
    user_id = get_user_id_from_token()
    if not user_id: return jsonify({"error": "Invalid token"}), 401
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, content, created_at FROM diary WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
    notes = cur.fetchall()
    for n in notes:
        n['created_at'] = n['created_at'].isoformat()
    cur.close()
    conn.close()
    return jsonify(notes)

@diary_bp.route('/', methods=['POST'])
def create_note():
    user_id = get_user_id_from_token()
    if not user_id: return jsonify({"error": "Invalid token"}), 401
    data = request.get_json()
    title = (data.get('title') or '').strip() or None
    content = (data.get('content') or '').strip()
    if not content: return jsonify({"error": "Content required"}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO diary (user_id, title, content) VALUES (%s, %s, %s)", (user_id, title, content))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Note saved"}), 201

@diary_bp.route('/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    user_id = get_user_id_from_token()
    if not user_id: return jsonify({"error": "Invalid token"}), 401
    data = request.get_json()
    title = (data.get('title') or '').strip() or None
    content = (data.get('content') or '').strip()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE diary SET title=%s, content=%s WHERE id=%s AND user_id=%s", (title, content, note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Updated"})

@diary_bp.route('/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    user_id = get_user_id_from_token()
    if not user_id: return jsonify({"error": "Invalid token"}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM diary WHERE id=%s AND user_id=%s", (note_id, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Deleted"})