from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'soa_academic_system_2024'
CORS(app)

SERVICES = {
    'students': 'http://localhost:5001',
    'courses': 'http://localhost:5002',
    'enrollments': 'http://localhost:5003'
}

def check_services():
    services_status = {}
    for name, url in SERVICES.items():
        try:
            response = requests.get(f"{url}/health", timeout=3)
            services_status[name] = response.status_code == 200
        except requests.exceptions.RequestException:
            services_status[name] = False
    return services_status

def make_service_request(service, endpoint, method='GET', data=None):
    try:
        url = f"{SERVICES[service]}{endpoint}"

        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=10)

        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Service request failed to {service}: {str(e)}")
        return None


@app.route('/')
def index():
    services_status = check_services()
    return render_template('index.html', services=services_status)

@app.route('/estudiantes')
def estudiantes():
    response = make_service_request('students', '/students')
    students_data = []

    if response and response.status_code == 200:
        students_data = response.json().get('students', [])

    return render_template('students.html', students=students_data)

@app.route('/cursos')
def cursos():
    response = make_service_request('courses', '/courses')
    courses_data = []

    if response and response.status_code == 200:
        courses_data = response.json().get('courses', [])

    return render_template('courses.html', courses=courses_data)

@app.route('/matriculas')
def matriculas():
    response = make_service_request('enrollments', '/enrollments')
    enrollments_data = []
    if response and response.status_code == 200:
        enrollments_data = response.json().get('enrollments', [])

    response_students = make_service_request('students', '/students')
    students_data = []
    if response_students and response_students.status_code == 200:
        students_data = response_students.json().get('students', [])

    response_courses = make_service_request('courses', '/courses/available')
    courses_data = []
    if response_courses and response_courses.status_code == 200:
        courses_data = response_courses.json().get('courses', [])

    return render_template('enrollments.html',
                         enrollments=enrollments_data,
                         students=students_data,
                         courses=courses_data)


@app.route('/api/students', methods=['GET', 'POST'])
def api_students():
    if request.method == 'GET':
        response = make_service_request('students', '/students')
    else:  # POST
        data = request.get_json()
        response = make_service_request('students', '/students', 'POST', data)

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/students/<int:student_id>', methods=['GET'])
def api_get_student(student_id):
    response = make_service_request('students', f'/students/{student_id}')

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/courses', methods=['GET'])
def api_courses():
    response = make_service_request('courses', '/courses')

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/courses/<string:course_code>', methods=['GET'])
def api_get_course(course_code):
    response = make_service_request('courses', f'/courses/{course_code}')

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/enrollments', methods=['GET', 'POST'])
def api_enrollments():
    if request.method == 'GET':
        response = make_service_request('enrollments', '/enrollments')
    else:  # POST
        data = request.get_json()
        response = make_service_request('enrollments', '/enrollments', 'POST', data)

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/enrollments/<int:student_id>', methods=['GET'])
def api_get_student_enrollments(student_id):
    response = make_service_request('enrollments', f'/enrollments/{student_id}')

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/enrollments/<int:enrollment_id>/cancel', methods=['PUT'])
def api_cancel_enrollment(enrollment_id):
    response = make_service_request('enrollments', f'/enrollments/{enrollment_id}/cancel', 'PUT')

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/enrollments/available-combinations', methods=['GET'])
def api_available_combinations():
    response = make_service_request('enrollments', '/enrollments/available-combinations')

    if response:
        return jsonify(response.json()), response.status_code
    else:
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/services/status')
def api_services_status():
    return jsonify(check_services())


@app.route('/api/student-profile/<int:student_id>')
def api_student_profile(student_id):
    try:
        student_response = make_service_request('students', f'/students/{student_id}')
        if not student_response or student_response.status_code != 200:
            return jsonify({'error': 'Student not found'}), 404

        student_data = student_response.json().get('student')

        enrollments_response = make_service_request('enrollments', f'/enrollments/{student_id}')
        enrollments_data = []
        if enrollments_response and enrollments_response.status_code == 200:
            enrollments_data = enrollments_response.json().get('enrollments', [])

        profile = {
            'student': student_data,
            'enrollments': enrollments_data,
            'total_enrollments': len(enrollments_data),
            'active_enrollments': len([e for e in enrollments_data if e.get('status') == 'ACTIVE'])
        }

        return jsonify(profile), 200

    except Exception as e:
        logger.error(f"Error getting student profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/course-details/<string:course_code>')
def api_course_details(course_code):
    try:
        course_response = make_service_request('courses', f'/courses/{course_code}')
        if not course_response or course_response.status_code != 200:
            return jsonify({'error': 'Course not found'}), 404

        course_data = course_response.json().get('course')

        enrollments_response = make_service_request('enrollments', f'/enrollments/course/{course_code}')
        enrollments_data = []
        if enrollments_response and enrollments_response.status_code == 200:
            enrollments_data = enrollments_response.json().get('enrollments', [])

        details = {
            'course': course_data,
            'enrollments': enrollments_data,
            'total_enrolled': len([e for e in enrollments_data if e.get('status') == 'ACTIVE']),
            'enrollment_list': enrollments_data
        }

        return jsonify(details), 200

    except Exception as e:
        logger.error(f"Error getting course details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html',
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error"), 500

if __name__ == '__main__':
    logger.info("Starting API Gateway / Orchestrator on port 5000")
    logger.info("Make sure all services are running:")
    logger.info("- Students Service: port 5001")
    logger.info("- Courses Service: port 5002")
    logger.info("- Enrollments Service: port 5003")

    app.run(host='0.0.0.0', port=5000, debug=True)
