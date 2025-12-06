from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_db_connection
import json

questionnaire_route = Blueprint('questionnaire', __name__)

@questionnaire_route.route('/questionnaire', methods=['POST'])
@jwt_required()
def submit_questionnaire():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        # Validate required fields
        if not data or 'category' not in data or 'questions' not in data or 'answers' not in data:
            return jsonify({'error': 'Missing required fields: category, questions or answers'}), 400

        category = data['category']
        questions = data['questions']
        answers = data['answers']
        total_score = data.get('total_score', 0)
        max_score = data.get('max_score', 0)
        result_message = data.get('result_message', '')

        # Validate answers length
        if len(answers) != len(questions):
            return jsonify({'error': 'Number of answers must match number of questions'}), 400

        num_questions = len(questions)  # Automatically calculate

        # DB Connection
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor()

        questions_json = json.dumps(questions)
        answers_json = json.dumps(answers)

        # Fixed Query – created_at auto handle hoga (table mein DEFAULT CURRENT_TIMESTAMP hona chahiye)
        query = """
            INSERT INTO questionnaire_responses (
                user_id, category, num_questions,
                questions_json, answers_json,
                total_score, max_score, result_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            user_id,
            category,
            num_questions,
            questions_json,
            answers_json,
            total_score,
            max_score,
            result_message
        )

        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({
            'message': 'Questionnaire responses saved successfully',
            'total_score': total_score,
            'max_score': max_score,
            'num_questions': num_questions
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Baaki dono routes bilkul sahi hain – bas chhote improvements
@questionnaire_route.route('/questionnaire/history', methods=['GET'])
@jwt_required()
def get_questionnaire_history():
    try:
        user_id = get_jwt_identity()
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, category, num_questions, questions_json, answers_json,
                   total_score, max_score, result_message, created_at
            FROM questionnaire_responses
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        results = cursor.fetchall()

        history = []
        for r in results:
            history.append({
                'id': r['id'],
                'category': r['category'],
                'num_questions': r['num_questions'],
                'questions': json.loads(r['questions_json']),
                'answers': json.loads(r['answers_json']),
                'total_score': r['total_score'],
                'max_score': r['max_score'],
                'result_message': r['result_message'],
                'created_at': r['created_at'].isoformat() if r['created_at'] else None
            })

        cursor.close()
        connection.close()
        return jsonify({'history': history}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@questionnaire_route.route('/questionnaire/<int:questionnaire_id>', methods=['GET'])
@jwt_required()
def get_questionnaire_detail(questionnaire_id):
    try:
        user_id = get_jwt_identity()
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, category, num_questions, questions_json, answers_json,
                   total_score, max_score, result_message, created_at
            FROM questionnaire_responses
            WHERE id = %s AND user_id = %s
        """, (questionnaire_id, user_id))
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if not result:
            return jsonify({'error': 'Questionnaire not found or access denied'}), 404

        return jsonify({
            'id': result['id'],
            'category': result['category'],
            'num_questions': result['num_questions'],
            'questions': json.loads(result['questions_json']),
            'answers': json.loads(result['answers_json']),
            'total_score': result['total_score'],
            'max_score': result['max_score'],
            'result_message': result['result_message'],
            'created_at': result['created_at'].isoformat() if result['created_at'] else None
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500