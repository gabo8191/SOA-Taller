"""
Students Service - SOA Implementation
Independent service for managing student information
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from memory_storage import students_storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

@app.route('/init-data', methods=['POST'])
def init_sample_data():
    """Initialize sample data manually"""
    try:
        # Sample data is automatically initialized in memory_storage module
        return jsonify({'message': 'Sample data initialized'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'service': 'Students Service'}), 200

@app.route('/students', methods=['POST'])
def register_student():
    """
    Register a new student
    Expected JSON: {
        "name": "string",
        "identification": "string",
        "program": "string",
        "email": "string" (optional)
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400

        required_fields = ['name', 'identification', 'program']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'El campo {field} es requerido'}), 400

        # Create new student using in-memory storage
        email_value = data.get('email')
        email = email_value.strip() if email_value else None
        
        student = students_storage.create_student(
            name=data['name'].strip(),
            identification=data['identification'].strip(),
            program=data['program'].strip(),
            email=email
        )

        logger.info(f"Student registered: {student['name']} (ID: {student['id']})")

        return jsonify({
            'message': 'Estudiante registrado exitosamente',
            'student': student
        }), 201

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        logger.error(f"Error registering student: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Get student information by ID"""
    try:
        student = students_storage.get_by_id(student_id)
        if not student:
            return jsonify({'error': 'Estudiante no encontrado'}), 404

        logger.info(f"Student query: {student['name']} (ID: {student_id})")

        return jsonify({'student': student}), 200

    except Exception as e:
        logger.error(f"Error getting student: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/students', methods=['GET'])
def list_students():
    """List all students"""
    try:
        students_list = students_storage.get_all()

        return jsonify({
            'students': students_list,
            'total': len(students_list)
        }), 200

    except Exception as e:
        logger.error(f"Error listing students: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/students/identification/<string:identification>', methods=['GET'])
def get_student_by_identification(identification):
    """Get student by identification number"""
    try:
        student = students_storage.get_by_identification(identification)
        if not student:
            return jsonify({'error': 'Estudiante no encontrado'}), 404

        logger.info(f"Student query by identification: {student['name']}")
        return jsonify({'student': student}), 200

    except Exception as e:
        logger.error(f"Error getting student by identification: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    logger.info("Starting Students Service on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
