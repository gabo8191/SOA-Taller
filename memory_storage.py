from datetime import datetime
from typing import Dict, List, Optional, Any

class InMemoryStorage:

    def __init__(self):
        self.data: Dict[int, Dict] = {}
        self.next_id = 1

    def create(self, item_data: Dict) -> Dict:
        item_data['id'] = self.next_id
        item_data['created_at'] = datetime.utcnow().isoformat()
        self.data[self.next_id] = item_data.copy()
        self.next_id += 1
        return item_data

    def get_all(self) -> List[Dict]:
        return list(self.data.values())

    def get_by_id(self, item_id: int) -> Optional[Dict]:
        return self.data.get(item_id)

    def update(self, item_id: int, update_data: Dict) -> Optional[Dict]:
        if item_id not in self.data:
            return None

        self.data[item_id].update(update_data)
        return self.data[item_id]

    def delete(self, item_id: int) -> bool:
        if item_id in self.data:
            del self.data[item_id]
            return True
        return False

    def find_by_field(self, field: str, value: Any) -> Optional[Dict]:
        for item in self.data.values():
            if item.get(field) == value:
                return item
        return None

    def find_all_by_field(self, field: str, value: Any) -> List[Dict]:
        return [item for item in self.data.values() if item.get(field) == value]

class StudentsStorage(InMemoryStorage):

    def create_student(self, name: str, identification: str, program: str, email: Optional[str] = None) -> Dict:
        if self.find_by_field('identification', identification):
            raise ValueError("Student with this identification already exists")

        student_data = {
            'name': name,
            'identification': identification,
            'program': program,
            'email': email
        }
        return self.create(student_data)

    def get_by_identification(self, identification: str) -> Optional[Dict]:
        return self.find_by_field('identification', identification)

class CoursesStorage(InMemoryStorage):

    def create_course(self, code: str, name: str, credits: int, instructor: str,
                     schedule: str, total_slots: int = 30) -> Dict:
        if self.find_by_field('code', code):
            raise ValueError("Course with this code already exists")

        course_data = {
            'code': code,
            'name': name,
            'credits': credits,
            'instructor': instructor,
            'schedule': schedule,
            'total_slots': total_slots,
            'available_slots': total_slots
        }
        return self.create(course_data)

    def get_by_code(self, code: str) -> Optional[Dict]:
        return self.find_by_field('code', code)

    def update_available_slots(self, course_code: str, change: int) -> bool:
        course = self.get_by_code(course_code)
        if course:
            new_slots = course['available_slots'] + change
            if 0 <= new_slots <= course['total_slots']:
                course['available_slots'] = new_slots
                return True
        return False

class EnrollmentsStorage(InMemoryStorage):

    def create_enrollment(self, student_id: int, course_code: str) -> Dict:
        existing = self.find_active_enrollment(student_id, course_code)
        if existing:
            raise ValueError("Student is already enrolled in this course")

        enrollment_data = {
            'student_id': student_id,
            'course_code': course_code,
            'status': 'ACTIVE',
            'enrollment_date': datetime.utcnow().isoformat(),
            'cancellation_date': None
        }
        return self.create(enrollment_data)

    def find_active_enrollment(self, student_id: int, course_code: str) -> Optional[Dict]:
        for enrollment in self.data.values():
            if (enrollment['student_id'] == student_id and
                enrollment['course_code'] == course_code and
                enrollment['status'] == 'ACTIVE'):
                return enrollment
        return None

    def get_enrollments_by_student(self, student_id: int) -> List[Dict]:
        return self.find_all_by_field('student_id', student_id)

    def get_enrollments_by_course(self, course_code: str) -> List[Dict]:
        return self.find_all_by_field('course_code', course_code)

    def cancel_enrollment(self, enrollment_id: int) -> bool:
        enrollment = self.get_by_id(enrollment_id)
        if enrollment and enrollment['status'] == 'ACTIVE':
            enrollment['status'] = 'CANCELLED'
            enrollment['cancellation_date'] = datetime.utcnow().isoformat()
            return True
        return False

students_storage = StudentsStorage()
courses_storage = CoursesStorage()
enrollments_storage = EnrollmentsStorage()

def recalculate_course_slots():
    try:
        all_courses = courses_storage.get_all()
        all_courses = courses_storage.get_all()

        active_enrollments = [
            e for e in enrollments_storage.get_all()
            if e['status'] == 'ACTIVE'
        ]

        enrollment_counts = {}
        for enrollment in active_enrollments:
            course_code = enrollment['course_code']
            enrollment_counts[course_code] = enrollment_counts.get(course_code, 0) + 1

        for course in all_courses:
            course_code = course['code']
            total_slots = course['total_slots']
            enrolled_count = enrollment_counts.get(course_code, 0)
            available_slots = total_slots - enrolled_count

            course['available_slots'] = max(0, available_slots)

        print(f"Course slots recalculated. Enrollment counts: {enrollment_counts}")

    except Exception as e:
        print(f"Error recalculating course slots: {e}")

def initialize_sample_data():
    try:

        students_storage.create_student("Juan Carlos Pérez", "12345678", "Ingeniería de Sistemas", "juan.perez@universidad.edu")
        students_storage.create_student("María Fernanda García", "87654321", "Ingeniería Industrial", "maria.garcia@universidad.edu")
        students_storage.create_student("Carlos Andrés López", "11223344", "Administración de Empresas", "carlos.lopez@universidad.edu")
        students_storage.create_student("Ana Sofía Rodríguez", "55667788", "Ingeniería de Sistemas", "ana.rodriguez@universidad.edu")

        courses_storage.create_course("IS101", "Programación I", 3, "Dr. Ana María Castillo", "Lun-Mie-Vie 8:00-10:00", 25)
        courses_storage.create_course("IS102", "Base de Datos I", 4, "Dra. Carmen Mendieta", "Mar-Jue 10:00-12:00", 30)
        courses_storage.create_course("IS103", "Algoritmos y Estructuras de Datos", 3, "Dr. Roberto Castellano", "Lun-Mie 14:00-16:00", 20)
        courses_storage.create_course("MATH101", "Cálculo Diferencial", 4, "Dra. Patricia Castro", "Mar-Jue 8:00-10:00", 35)
        courses_storage.create_course("PHYS101", "Física I", 3, "Dr. Luis Hernández", "Lun-Mie-Vie 10:00-11:30", 30)

        enrollments_storage.create_enrollment(1, "IS101")
        courses_storage.update_available_slots("IS101", -1)

        enrollments_storage.create_enrollment(2, "IS102")
        courses_storage.update_available_slots("IS102", -1)

        enrollments_storage.create_enrollment(3, "MATH101")
        courses_storage.update_available_slots("MATH101", -1)

        enrollments_storage.create_enrollment(1, "PHYS101")
        courses_storage.update_available_slots("PHYS101", -1)

        print("Sample data initialized successfully")
    except ValueError as e:
        print(f"Sample data already exists: {e}")
        pass

    recalculate_course_slots()

initialize_sample_data()
