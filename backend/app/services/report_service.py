from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentResult,
    AssessmentResultStatus,
    Attendance,
    AttendanceStatus,
    Department,
    Enrollment,
    EnrollmentStatus,
    Training,
    TrainingSession,
    TrainingStatus,
    User,
    UserRole,
)
from app.schemas.report import (
    EmployeeReport,
    EmployeeResultRow,
    LabelCount,
    OrgReport,
    TrainerReport,
    TrainerTrainingRow,
)
from app.services.attendance_service import ATTENDED, attendance_percentage


def _count(db: Session, stmt) -> int:
    return db.scalar(select(func.count()).select_from(stmt.subquery())) or 0


def _attendance_rate(db: Session, conditions=None) -> float:
    stmt = select(Attendance.status)
    if conditions is not None:
        stmt = stmt.where(*conditions)
    statuses = list(db.scalars(stmt))
    if not statuses:
        return 0.0
    attended = sum(1 for s in statuses if s in ATTENDED)
    return round(attended / len(statuses) * 100, 1)


def org_report(db: Session) -> OrgReport:
    total_users = _count(db, select(User.id))
    total_trainers = _count(db, select(User.id).where(User.role == UserRole.trainer))
    total_employees = _count(db, select(User.id).where(User.role == UserRole.employee))

    total_trainings = _count(db, select(Training.id))
    active = _count(db, select(Training.id).where(Training.status == TrainingStatus.active))
    completed = _count(
        db, select(Training.id).where(Training.status == TrainingStatus.completed)
    )
    total_enrollments = _count(db, select(Enrollment.id))

    results = list(db.scalars(select(AssessmentResult.result)))
    pass_rate = (
        round(
            sum(1 for r in results if r == AssessmentResultStatus.pass_)
            / len(results)
            * 100,
            1,
        )
        if results
        else 0.0
    )

    trainings_by_status = [
        LabelCount(label=status.value, count=_count(db, select(Training.id).where(Training.status == status)))
        for status in TrainingStatus
    ]

    dept_rows = db.execute(
        select(Department.name, func.count(Enrollment.id))
        .join(User, User.department_id == Department.id)
        .join(Enrollment, Enrollment.user_id == User.id)
        .group_by(Department.name)
    ).all()
    enrollments_by_department = [LabelCount(label=name, count=cnt) for name, cnt in dept_rows]

    attendance_by_status = [
        LabelCount(label=st.value, count=_count(db, select(Attendance.id).where(Attendance.status == st)))
        for st in AttendanceStatus
    ]

    return OrgReport(
        total_users=total_users,
        total_trainers=total_trainers,
        total_employees=total_employees,
        total_trainings=total_trainings,
        active_trainings=active,
        completed_trainings=completed,
        total_enrollments=total_enrollments,
        overall_attendance_rate=_attendance_rate(db),
        assessment_pass_rate=pass_rate,
        trainings_by_status=trainings_by_status,
        enrollments_by_department=enrollments_by_department,
        attendance_by_status=attendance_by_status,
    )


def trainer_report(db: Session, trainer_id: int) -> TrainerReport:
    trainer = db.get(User, trainer_id)
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")

    trainings = list(db.scalars(select(Training).where(Training.trainer_id == trainer_id)))
    training_ids = [t.id for t in trainings]

    sessions_count = (
        _count(db, select(TrainingSession.id).where(TrainingSession.training_id.in_(training_ids)))
        if training_ids
        else 0
    )
    total_enrollments = (
        _count(db, select(Enrollment.id).where(Enrollment.training_id.in_(training_ids)))
        if training_ids
        else 0
    )
    assessments_count = (
        _count(db, select(Assessment.id).where(Assessment.training_id.in_(training_ids)))
        if training_ids
        else 0
    )

    # Avg attendance across the trainer's sessions.
    avg_attendance = (
        _attendance_rate(
            db,
            [Attendance.session_id.in_(select(TrainingSession.id).where(TrainingSession.training_id.in_(training_ids)))],
        )
        if training_ids
        else 0.0
    )

    # Avg assessment score (%) across the trainer's assessments.
    score_rows = (
        list(
            db.execute(
                select(AssessmentResult.score, AssessmentResult.max_score)
                .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
                .where(Assessment.training_id.in_(training_ids))
            ).all()
        )
        if training_ids
        else []
    )
    pcts = [round(float(s) / float(m) * 100, 1) for s, m in score_rows if m]
    avg_score = round(sum(pcts) / len(pcts), 1) if pcts else 0.0

    training_rows = [
        TrainerTrainingRow(
            id=t.id,
            title=t.title,
            status=t.status.value,
            enrollment_count=_count(db, select(Enrollment.id).where(Enrollment.training_id == t.id)),
        )
        for t in trainings
    ]

    return TrainerReport(
        trainer_id=trainer_id,
        name=trainer.name,
        trainings_count=len(trainings),
        sessions_count=sessions_count,
        total_enrollments=total_enrollments,
        avg_attendance_rate=avg_attendance,
        assessments_count=assessments_count,
        avg_assessment_score=avg_score,
        trainings=training_rows,
    )


def employee_report(db: Session, user_id: int) -> EmployeeReport:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    enrolled = _count(db, select(Enrollment.id).where(Enrollment.user_id == user_id))
    completed = _count(
        db,
        select(Enrollment.id).where(
            Enrollment.user_id == user_id, Enrollment.status == EnrollmentStatus.completed
        ),
    )

    result_rows = list(
        db.execute(
            select(AssessmentResult, Assessment.title)
            .join(Assessment, AssessmentResult.assessment_id == Assessment.id)
            .where(AssessmentResult.user_id == user_id)
            .order_by(AssessmentResult.attempt_date.desc())
        ).all()
    )
    pcts = [round(float(r.score) / float(r.max_score) * 100, 1) for r, _ in result_rows if r.max_score]
    avg_score = round(sum(pcts) / len(pcts), 1) if pcts else 0.0
    passes = sum(1 for r, _ in result_rows if r.result == AssessmentResultStatus.pass_)
    pass_rate = round(passes / len(result_rows) * 100, 1) if result_rows else 0.0

    results = [
        EmployeeResultRow(
            assessment_title=title,
            score=float(r.score),
            max_score=float(r.max_score),
            result=r.result,
            attempt_date=r.attempt_date,
        )
        for r, title in result_rows
    ]

    return EmployeeReport(
        user_id=user_id,
        name=user.name,
        attendance_pct=attendance_percentage(db, user_id),
        enrolled_trainings=enrolled,
        completed_trainings=completed,
        assessments_taken=len(result_rows),
        avg_score=avg_score,
        pass_rate=pass_rate,
        results=results,
    )
