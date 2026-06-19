"""Populate the database with realistic demo data.

Run with:  python -m app.seed

Idempotent: if the super-admin already exists the script reports the
credentials and exits without duplicating data.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentResult,
    AssessmentResultStatus,
    Attendance,
    AttendanceStatus,
    Department,
    Enrollment,
    EnrollmentStatus,
    QuestionType,
    SessionMode,
    Training,
    TrainingSession,
    TrainingStatus,
    User,
    UserRole,
)

ADMIN_EMAIL = "admin@tapms.local"
ADMIN_PASSWORD = "Admin@123"
TRAINER_PASSWORD = "Trainer@123"
EMPLOYEE_PASSWORD = "Employee@123"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.scalar(select(User).where(User.email == ADMIN_EMAIL)):
            print("Database already seeded. Credentials below.\n")
            _print_credentials()
            return

        # --- Departments ---
        departments = [
            Department(name="Engineering", description="Software engineering teams"),
            Department(name="Sales", description="Revenue and account management"),
            Department(name="Human Resources", description="People operations"),
        ]
        db.add_all(departments)
        db.flush()
        eng, sales, hr = departments

        # --- Super admin ---
        admin = User(
            employee_code="EMP0001",
            name="Ava Administrator",
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.super_admin,
            department_id=None,
            designation="System Administrator",
            joining_date=date(2021, 1, 4),
        )
        db.add(admin)

        # --- Trainers ---
        trainers = [
            User(
                employee_code="EMP0002",
                name="Tom Trainer",
                email="trainer1@tapms.local",
                password_hash=hash_password(TRAINER_PASSWORD),
                role=UserRole.trainer,
                department_id=eng.id,
                designation="Senior Engineering Coach",
                joining_date=date(2021, 6, 15),
            ),
            User(
                employee_code="EMP0003",
                name="Tina Teacher",
                email="trainer2@tapms.local",
                password_hash=hash_password(TRAINER_PASSWORD),
                role=UserRole.trainer,
                department_id=sales.id,
                designation="Sales Enablement Lead",
                joining_date=date(2022, 2, 1),
            ),
        ]
        db.add_all(trainers)

        # --- Employees ---
        dept_cycle = [eng, sales, hr]
        employees = []
        for i in range(1, 11):
            dept = dept_cycle[(i - 1) % len(dept_cycle)]
            employees.append(
                User(
                    employee_code=f"EMP{i + 3:04d}",
                    name=f"Employee {i:02d}",
                    email=f"employee{i}@tapms.local",
                    password_hash=hash_password(EMPLOYEE_PASSWORD),
                    role=UserRole.employee,
                    department_id=dept.id,
                    designation="Associate",
                    joining_date=date(2023, 1, 1) + timedelta(days=i * 20),
                )
            )
        db.add_all(employees)
        db.flush()

        # --- Trainings ---
        today = date.today()
        trainings = [
            Training(
                title="Python Fundamentals",
                description="Core Python for new engineers.",
                category="Technical",
                trainer_id=trainers[0].id,
                department_id=eng.id,
                start_date=today - timedelta(days=14),
                end_date=today + timedelta(days=14),
                capacity=20,
                status=TrainingStatus.active,
                created_by=admin.id,
            ),
            Training(
                title="Consultative Selling",
                description="Modern B2B sales techniques.",
                category="Sales",
                trainer_id=trainers[1].id,
                department_id=sales.id,
                start_date=today - timedelta(days=30),
                end_date=today - timedelta(days=2),
                capacity=15,
                status=TrainingStatus.completed,
                created_by=admin.id,
            ),
            Training(
                title="Workplace Compliance 101",
                description="Mandatory compliance and ethics training.",
                category="Compliance",
                trainer_id=trainers[0].id,
                department_id=None,  # open to all
                start_date=today + timedelta(days=7),
                end_date=today + timedelta(days=21),
                capacity=50,
                status=TrainingStatus.scheduled,
                created_by=admin.id,
            ),
        ]
        db.add_all(trainings)
        db.flush()
        python_training, sales_training, compliance_training = trainings

        # --- Sessions ---
        sessions = [
            TrainingSession(
                training_id=python_training.id,
                title="Variables & Control Flow",
                session_date=today - timedelta(days=10),
                start_time=time(10, 0),
                end_time=time(12, 0),
                location="Room A / Online",
                mode=SessionMode.hybrid,
                meeting_link="https://meet.example.com/python-1",
            ),
            TrainingSession(
                training_id=python_training.id,
                title="Functions & Modules",
                session_date=today - timedelta(days=3),
                start_time=time(10, 0),
                end_time=time(12, 0),
                location="Room A",
                mode=SessionMode.offline,
            ),
            TrainingSession(
                training_id=sales_training.id,
                title="Discovery Calls",
                session_date=today - timedelta(days=20),
                start_time=time(14, 0),
                end_time=time(16, 0),
                location="Online",
                mode=SessionMode.online,
                meeting_link="https://meet.example.com/sales-1",
            ),
        ]
        db.add_all(sessions)
        db.flush()

        # --- Enrollments ---
        # Engineering employees -> Python; Sales employees -> Sales training.
        eng_employees = [e for e in employees if e.department_id == eng.id]
        sales_employees = [e for e in employees if e.department_id == sales.id]

        enrollments = []
        for emp in eng_employees:
            enrollments.append(
                Enrollment(
                    user_id=emp.id,
                    training_id=python_training.id,
                    status=EnrollmentStatus.enrolled,
                )
            )
        for emp in sales_employees:
            enrollments.append(
                Enrollment(
                    user_id=emp.id,
                    training_id=sales_training.id,
                    status=EnrollmentStatus.completed,
                )
            )
        db.add_all(enrollments)
        db.flush()

        # --- Sample attendance (first Python session) ---
        first_session = sessions[0]
        for idx, emp in enumerate(eng_employees):
            status = AttendanceStatus.present if idx % 3 != 0 else AttendanceStatus.late
            db.add(
                Attendance(
                    session_id=first_session.id,
                    user_id=emp.id,
                    status=status,
                    marked_by=trainers[0].id,
                    notes=None,
                )
            )

        # --- One completed assessment with questions + results ---
        assessment = Assessment(
            training_id=python_training.id,
            title="Python Fundamentals Quiz",
            description="Checks understanding of Python basics.",
            total_marks=3,
            passing_marks=2,
            duration_minutes=20,
        )
        db.add(assessment)
        db.flush()

        questions = [
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_text="Which keyword defines a function in Python?",
                question_type=QuestionType.mcq,
                options=["func", "def", "function", "lambda"],
                correct_answer="def",
                marks=1,
                order_index=0,
            ),
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_text="What data type is the result of 3 / 2 in Python 3?",
                question_type=QuestionType.mcq,
                options=["int", "float", "str", "bool"],
                correct_answer="float",
                marks=1,
                order_index=1,
            ),
            AssessmentQuestion(
                assessment_id=assessment.id,
                question_text="Name the built-in function used to get the length of a list.",
                question_type=QuestionType.short,
                options=None,
                correct_answer="len",
                marks=1,
                order_index=2,
            ),
        ]
        db.add_all(questions)
        db.flush()

        # One employee has completed the assessment (2/3 -> pass).
        first_emp = eng_employees[0]
        db.add(
            AssessmentResult(
                assessment_id=assessment.id,
                user_id=first_emp.id,
                score=2,
                max_score=3,
                result=AssessmentResultStatus.pass_,
                answers={
                    str(questions[0].id): "def",
                    str(questions[1].id): "float",
                    str(questions[2].id): "length",
                },
                time_taken_seconds=540,
            )
        )

        db.commit()
        print("Seed complete.\n")
        _print_credentials()
    finally:
        db.close()


def _print_credentials() -> None:
    print("=" * 56)
    print("  TAPMS seeded login credentials")
    print("=" * 56)
    print(f"  Super Admin : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  Trainer 1   : trainer1@tapms.local / {TRAINER_PASSWORD}")
    print(f"  Trainer 2   : trainer2@tapms.local / {TRAINER_PASSWORD}")
    print(f"  Employees   : employee1..10@tapms.local / {EMPLOYEE_PASSWORD}")
    print("=" * 56)


if __name__ == "__main__":
    seed()
