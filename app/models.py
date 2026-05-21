import enum
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Priority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EligibilityStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    internal_id = Column(String, unique=True, nullable=False)  # practice's own patient ID
    payer_id = Column(String, nullable=False)
    payer_name = Column(String, nullable=False)
    insurance_member_id = Column(String, nullable=False)  # encrypted at rest in production
    created_at = Column(DateTime, default=datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    provider_npi = Column(String, nullable=False)
    service_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    verification = relationship("VerificationResult", back_populates="appointment", uselist=False)
    action_items = relationship("ActionQueueItem", back_populates="appointment")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, unique=True)
    verified_at = Column(DateTime, default=datetime.utcnow)
    eligibility_status = Column(Enum(EligibilityStatus), nullable=False)
    deductible_individual = Column(Float)
    deductible_met = Column(Float)
    copay = Column(Float)
    coinsurance = Column(Float)
    out_of_pocket_max = Column(Float)
    out_of_pocket_met = Column(Float)
    prior_auth_required = Column(Boolean, default=False)
    in_network = Column(Boolean, default=True)
    payer_response_id = Column(String)  # reference token — never store full payer response

    appointment = relationship("Appointment", back_populates="verification")


class ActionQueueItem(Base):
    __tablename__ = "action_queue"

    id = Column(Integer, primary_key=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    priority = Column(Enum(Priority), nullable=False)
    flag_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolved_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointment = relationship("Appointment", back_populates="action_items")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    event_type = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String)
    performed_by = Column(String, default="system")
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)  # JSON string — must contain no PHI
