"""Populate the database with realistic demo data.

Run with:  python -m app.seed

Idempotent: if the super-admin already exists the script reports the
credentials and exits without duplicating data.

Demo roster (kept intentionally small): 1 admin, 1 trainer, 2 employees.
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

ADMIN_EMAIL = "admin@tapms.com"
ADMIN_PASSWORD = "Admin@123"
TRAINER_PASSWORD = "Trainer@123"
EMPLOYEE_PASSWORD = "Employee@123"


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
        ]
        db.add_all(departments)
        db.flush()
        eng, sales = departments

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

        # --- Trainer (single) ---
        trainer = User(
            employee_code="EMP0002",
            name="Tom Trainer",
            email="trainer1@tapms.com",
            password_hash=hash_password(TRAINER_PASSWORD),
            role=UserRole.trainer,
            department_id=eng.id,
            designation="Senior Engineering Coach",
            joining_date=date(2021, 6, 15),
        )
        db.add(trainer)

        # --- Employees (two) ---
        employees = [
            User(
                employee_code="EMP0003",
                name="Erin Employee",
                email="employee1@tapms.com",
                password_hash=hash_password(EMPLOYEE_PASSWORD),
                role=UserRole.employee,
                department_id=eng.id,
                designation="Associate Engineer",
                joining_date=date(2023, 1, 20),
            ),
            User(
                employee_code="EMP0004",
                name="Evan Employee",
                email="employee2@tapms.com",
                password_hash=hash_password(EMPLOYEE_PASSWORD),
                role=UserRole.employee,
                department_id=eng.id,
                designation="Associate Engineer",
                joining_date=date(2023, 2, 10),
            ),
        ]
        db.add_all(employees)
        db.flush()

        # --- Trainings (all run by the single trainer) ---
        today = date.today()
        python_training = Training(
            title="Python Fundamentals",
            description="Core Python for new engineers.",
            category="Technical",
            trainer_id=trainer.id,
            department_id=eng.id,
            start_date=today - timedelta(days=14),
            end_date=today + timedelta(days=14),
            capacity=20,
            total_sessions=2,
            status=TrainingStatus.active,
            created_by=admin.id,
        )
        compliance_training = Training(
            title="Workplace Compliance 101",
            description="Mandatory compliance and ethics training.",
            category="Compliance",
            trainer_id=trainer.id,
            department_id=None,  # open to all
            start_date=today + timedelta(days=7),
            end_date=today + timedelta(days=21),
            capacity=50,
            total_sessions=1,
            status=TrainingStatus.scheduled,
            created_by=admin.id,
        )
        db.add_all([python_training, compliance_training])
        db.flush()

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
        ]
        db.add_all(sessions)
        db.flush()

        # --- Enrollments: both employees in Python Fundamentals ---
        for emp in employees:
            db.add(
                Enrollment(
                    user_id=emp.id,
                    training_id=python_training.id,
                    status=EnrollmentStatus.enrolled,
                )
            )
        db.flush()

        # --- Sample attendance (first Python session) ---
        first_session = sessions[0]
        db.add(
            Attendance(
                session_id=first_session.id,
                user_id=employees[0].id,
                status=AttendanceStatus.present,
                marked_by=trainer.id,
            )
        )
        db.add(
            Attendance(
                session_id=first_session.id,
                user_id=employees[1].id,
                status=AttendanceStatus.late,
                marked_by=trainer.id,
            )
        )

        # --- One assessment with questions + a completed result ---
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

        db.add(
            AssessmentResult(
                assessment_id=assessment.id,
                user_id=employees[0].id,
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
    print(f"  Trainer     : trainer1@tapms.com / {TRAINER_PASSWORD}")
    print(f"  Employee 1  : employee1@tapms.com / {EMPLOYEE_PASSWORD}")
    print(f"  Employee 2  : employee2@tapms.com / {EMPLOYEE_PASSWORD}")
    print("=" * 56)


if __name__ == "__main__":
    seed()
