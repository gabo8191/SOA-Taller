from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from datetime import datetime
from memory_storage import enrollments_storage, students_storage, courses_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


STUDENTS_SERVICE_URL = 'http://localhost:5001'
COURSES_SERVICE_URL = 'http://localhost:5002'

def verify_student_exists(student_id):
    try:
        student = students_storage.get_by_id(student_id)
        return student is not None
    except Exception as e:
        logger.error(f"Error verifying student: {str(e)}")
        return False

def verify_course_exists(course_code):
    try:
        course = courses_storage.get_by_code(course_code)
        return course is not None
    except Exception as e:
        logger.error(f"Error verifying course: {str(e)}")
        return False

def reserve_course_slot(course_code):
    try:
        return courses_storage.update_available_slots(course_code, -1)
    except Exception as e:
        logger.error(f"Error reserving slot: {str(e)}")
        return False

def release_course_slot(course_code):
    try:
        return courses_storage.update_available_slots(course_code, 1)
    except Exception as e:
        logger.error(f"Error releasing slot: {str(e)}")
        return False

def get_student_data(student_id):
    try:
        return students_storage.get_by_id(student_id)
    except Exception as e:
        logger.error(f"Error getting student data: {str(e)}")
        return None

def get_course_data(course_code):
    try:
        return courses_storage.get_by_code(course_code)
    except Exception as e:
        logger.error(f"Error getting course data: {str(e)}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'service': 'Enrollments Service'}), 200

@app.route('/enrollments/available-combinations', methods=['GET'])
def get_available_combinations():
    try:
        all_students = students_storage.get_all()
        all_courses = courses_storage.get_all()

        existing_enrollments = [
            (e['student_id'], e['course_code'])
            for e in enrollments_storage.get_all()
            if e['status'] == 'ACTIVE'
        ]

        available_combinations = []
        for student in all_students:
            for course in all_courses:
                combination = (student['id'], course['code'])
                if combination not in existing_enrollments and course['available_slots'] > 0:
                    available_combinations.append({
                        'student_id': student['id'],
                        'student_name': student['name'],
                        'course_code': course['code'],
                        'course_name': course['name'],
                        'available_slots': course['available_slots']
                    })

        return jsonify({
            'available_combinations': available_combinations,
            'total': len(available_combinations),
            'existing_enrollments': len(existing_enrollments)
        }), 200

    except Exception as e:
        logger.error(f"Error getting available combinations: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/enrollments', methods=['POST'])
def enroll_in_course():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400

        required_fields = ['student_id', 'course_code']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'El campo {field} es requerido'}), 400

        student_id = data['student_id']
        course_code = data['course_code'].upper()

        if not verify_student_exists(student_id):
            return jsonify({'error': 'El estudiante no existe'}), 404

        if not verify_course_exists(course_code):
            return jsonify({'error': 'El curso no existe'}), 404

        if not reserve_course_slot(course_code):
            return jsonify({'error': 'No hay cupos disponibles para este curso'}), 409

        try:
            enrollment = enrollments_storage.create_enrollment(student_id, course_code)
        except ValueError as e:
            release_course_slot(course_code)

            student_data = get_student_data(student_id)
            course_data = get_course_data(course_code)

            student_name = student_data['name'] if student_data else f"ID {student_id}"
            course_name = course_data['name'] if course_data else course_code

            return jsonify({
                'error': f'El estudiante {student_name} ya está matriculado en el curso {course_name}',
                'details': str(e),
                'student_id': student_id,
                'course_code': course_code
            }), 409

        student_data = get_student_data(student_id)
        course_data = get_course_data(course_code)

        logger.info(f"Enrollment created: Student {student_id} in course {course_code}")

        response_data = {
            'message': 'Matrícula realizada exitosamente',
            'enrollment': enrollment
        }

        if student_data:
            response_data['student'] = student_data
        if course_data:
            response_data['course'] = course_data

        return jsonify(response_data), 201

    except Exception as e:
        logger.error(f"Error enrolling in course: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/enrollments/<int:student_id>', methods=['GET'])
def get_student_enrollments(student_id):
    try:
        if not verify_student_exists(student_id):
            return jsonify({'error': 'El estudiante no existe'}), 404

        student_enrollments = enrollments_storage.get_enrollments_by_student(student_id)

        enriched_enrollments = []
        for enrollment in student_enrollments:
            course_data = get_course_data(enrollment['course_code'])
            if course_data:
                enrollment['course'] = course_data
            enriched_enrollments.append(enrollment)

        student_data = get_student_data(student_id)

        logger.info(f"Enrollments query for student {student_id}: {len(enriched_enrollments)} enrollments")

        response_data = {
            'enrollments': enriched_enrollments,
            'total': len(enriched_enrollments)
        }

        if student_data:
            response_data['student'] = student_data

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error getting student enrollments: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/enrollments', methods=['GET'])
def list_all_enrollments():
    try:
        enrollments = enrollments_storage.get_all()
        enrollments_list = []

        for enrollment in enrollments:
            student_data = get_student_data(enrollment['student_id'])
            course_data = get_course_data(enrollment['course_code'])

            if student_data:
                enrollment['student'] = student_data
            if course_data:
                enrollment['course'] = course_data

            enrollments_list.append(enrollment)

        logger.info(f"All enrollments query: {len(enrollments_list)} records")

        return jsonify({
            'enrollments': enrollments_list,
            'total': len(enrollments_list)
        }), 200

    except Exception as e:
        logger.error(f"Error listing enrollments: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/enrollments/<int:enrollment_id>/cancel', methods=['PUT'])
def cancel_enrollment(enrollment_id):
    try:
        enrollment = enrollments_storage.get_by_id(enrollment_id)

        if not enrollment:
            return jsonify({'error': 'Matrícula no encontrada'}), 404

        if enrollment['status'] == 'CANCELLED':
            return jsonify({'error': 'La matrícula ya está cancelada'}), 409

        release_course_slot(enrollment['course_code'])

        if enrollments_storage.cancel_enrollment(enrollment_id):
            logger.info(f"Enrollment cancelled: ID {enrollment_id}")

            return jsonify({
                'message': 'Matrícula cancelada exitosamente',
                'enrollment': enrollments_storage.get_by_id(enrollment_id)
            }), 200
        else:
            return jsonify({'error': 'Error al cancelar la matrícula'}), 500

    except Exception as e:
        logger.error(f"Error cancelling enrollment: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/enrollments/course/<string:course_code>', methods=['GET'])
def get_course_enrollments(course_code):
    try:
        course_code = course_code.upper()

        if not verify_course_exists(course_code):
            return jsonify({'error': 'El curso no existe'}), 404

        course_enrollments = enrollments_storage.get_enrollments_by_course(course_code)

        enriched_enrollments = []
        for enrollment in course_enrollments:
            student_data = get_student_data(enrollment['student_id'])
            if student_data:
                enrollment['student'] = student_data
            enriched_enrollments.append(enrollment)

        course_data = get_course_data(course_code)

        logger.info(f"Course enrollments query for {course_code}: {len(enriched_enrollments)} students")

        response_data = {
            'enrollments': enriched_enrollments,
            'total': len(enriched_enrollments),
            'message': f'Matrículas del curso {course_code} obtenidas exitosamente'
        }

        if course_data:
            response_data['course'] = course_data

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error getting course enrollments: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    logger.info("Starting Enrollments Service on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=True)
