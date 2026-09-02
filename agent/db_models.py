"""
Database models for Razorpay Recovery Agent.
Implements multi-tenancy groundwork with merchant_id foreign keys across all entities.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    audit_entries = relationship("AuditTrailEntry", back_populates="merchant", cascade="all, delete-orphan")
    proposals = relationship("PolicyChangeProposal", back_populates="merchant", cascade="all, delete-orphan")
    threshold_configs = relationship("ThresholdConfig", back_populates="merchant", cascade="all, delete-orphan")


class AuditTrailEntry(Base):
    __tablename__ = "audit_trail_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False, default=1)
    timestamp = Column(String(64), nullable=False)
    payment_id = Column(String(128), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    error_code = Column(String(128), index=True, nullable=False)
    category = Column(String(128), index=True, nullable=False)
    action = Column(String(128), index=True, nullable=False)
    attempted = Column(Boolean, nullable=False, default=False)
    predicted_success_prob = Column(Float, nullable=False)
    estimated_uplift = Column(Float, nullable=True)
    reason = Column(Text, nullable=False)
    outcome_succeeded = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="audit_entries")

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "payment_id": self.payment_id,
            "amount": self.amount,
            "error_code": self.error_code,
            "category": self.category,
            "action": self.action,
            "attempted": self.attempted,
            "predicted_success_prob": self.predicted_success_prob,
            "estimated_uplift": self.estimated_uplift,
            "reason": self.reason,
            "outcome": {"succeeded": self.outcome_succeeded} if self.outcome_succeeded is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PolicyChangeProposal(Base):
    __tablename__ = "policy_change_proposals"

    id = Column(String(128), primary_key=True)  # proposal_id string
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False, default=1)
    timestamp = Column(String(64), nullable=False)
    drift_detected = Column(Boolean, nullable=False, default=False)
    evaluated_on = Column(String(128), nullable=False)
    old_model_performance = Column(JSON, nullable=True)
    original_performance = Column(JSON, nullable=True)
    current_threshold = Column(Float, nullable=False)
    proposed_threshold = Column(Float, nullable=False)
    net_value_current_threshold = Column(Float, nullable=False)
    net_value_proposed_threshold = Column(Float, nullable=False)
    status = Column(String(64), nullable=False, default="pending_human_approval")
    note = Column(Text, nullable=True)
    resolved_at = Column(String(64), nullable=True)

    merchant = relationship("Merchant", back_populates="proposals")

    def to_dict(self):
        return {
            "proposal_id": self.id,
            "timestamp": self.timestamp,
            "drift_detected": self.drift_detected,
            "evaluated_on": self.evaluated_on,
            "drift_batch_performance": self.old_model_performance,
            "old_model_performance": self.old_model_performance,
            "original_performance": self.original_performance,
            "current_threshold": self.current_threshold,
            "proposed_threshold": self.proposed_threshold,
            "net_value_current_threshold": self.net_value_current_threshold,
            "net_value_proposed_threshold": self.net_value_proposed_threshold,
            "estimated_net_value_gain": self.net_value_proposed_threshold - self.net_value_current_threshold,
            "status": self.status,
            "note": self.note,
            "resolved_at": self.resolved_at,
        }


class ThresholdConfig(Base):
    __tablename__ = "threshold_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(Integer, ForeignKey("merchants.id"), nullable=False, default=1)
    success_threshold = Column(Float, nullable=False, default=0.47)
    uplift_gate_threshold = Column(Float, nullable=False, default=0.05)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="threshold_configs")
