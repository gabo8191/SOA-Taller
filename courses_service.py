"""
Courses Service - SOA Implementation
Independent service for managing course information
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from memory_storage import courses_storage, recalculate_course_slots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Sample data is automatically initialized in memory_storage module

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'OK', 'service': 'Courses Service'}), 200

@app.route('/courses', methods=['GET'])
def list_courses():
    """List all available courses"""
    try:
        # Recalculate slots to ensure accuracy
        recalculate_course_slots()
        
        courses_list = courses_storage.get_all()

        logger.info(f"Courses query - {len(courses_list)} courses available")

        return jsonify({
            'courses': courses_list,
            'total': len(courses_list),
            'message': 'Oferta académica obtenida exitosamente'
        }), 200

    except Exception as e:
        logger.error(f"Error listing courses: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/courses/<string:course_code>', methods=['GET'])
def get_course(course_code):
    """Get detailed course information by code"""
    try:
        course_code = course_code.upper()
        course = courses_storage.get_by_code(course_code)

        if not course:
            return jsonify({'error': 'Curso no encontrado'}), 404

        logger.info(f"Course query: {course['name']} ({course_code})")

        return jsonify({'course': course}), 200

    except Exception as e:
        logger.error(f"Error getting course: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/courses/available', methods=['GET'])
def list_available_courses():
    """List only courses with available slots"""
    try:
        all_courses = courses_storage.get_all()
        available_courses = [course for course in all_courses if course['available_slots'] > 0]

        logger.info(f"Available courses query - {len(available_courses)} courses with slots")

        return jsonify({
            'courses': available_courses,
            'total': len(available_courses),
            'message': 'Cursos disponibles obtenidos exitosamente'
        }), 200

    except Exception as e:
        logger.error(f"Error listing available courses: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/courses/<string:course_code>/reserve-slot', methods=['PUT'])
def reserve_slot(course_code):
    """Reserve a slot in a course (used by enrollment service)"""
    try:
        course_code = course_code.upper()

        if courses_storage.update_available_slots(course_code, -1):
            course = courses_storage.get_by_code(course_code)
            if course:
                logger.info(f"Slot reserved for {course['name']}: {course['available_slots']} remaining")

            return jsonify({
                'message': 'Cupo reservado exitosamente',
                'course': course
            }), 200
        else:
            return jsonify({'error': 'No hay cupos disponibles o curso no encontrado'}), 409

    except Exception as e:
        logger.error(f"Error reserving slot: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/courses/<string:course_code>/release-slot', methods=['PUT'])
def release_slot(course_code):
    """Release a slot in a course (used when enrollment is cancelled)"""
    try:
        course_code = course_code.upper()

        if courses_storage.update_available_slots(course_code, 1):
            course = courses_storage.get_by_code(course_code)
            if course:
                logger.info(f"Slot released for {course['name']}: {course['available_slots']} available")

            return jsonify({
                'message': 'Cupo liberado exitosamente',
                'course': course
            }), 200
        else:
            return jsonify({'error': 'No se pueden liberar más cupos o curso no encontrado'}), 409

    except Exception as e:
        logger.error(f"Error releasing slot: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/courses/instructor/<string:instructor>', methods=['GET'])
def get_courses_by_instructor(instructor):
    """List courses by instructor"""
    try:
        all_courses = courses_storage.get_all()
        # Filter courses by instructor (case insensitive)
        instructor_courses = [
            course for course in all_courses
            if instructor.lower() in course['instructor'].lower()
        ]

        logger.info(f"Courses by instructor query: {instructor} - {len(instructor_courses)} courses found")

        return jsonify({
            'courses': instructor_courses,
            'total': len(instructor_courses),
            'instructor': instructor,
            'message': f'Cursos del instructor {instructor} obtenidos exitosamente'
        }), 200

    except Exception as e:
        logger.error(f"Error getting courses by instructor: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    logger.info("Starting Courses Service on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=True)
