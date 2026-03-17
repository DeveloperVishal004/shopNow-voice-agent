from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from sqlalchemy.sql import func
from backend.db.database import Base

class Order(Base):
    __tablename__ = "orders"

    id              = Column(String, primary_key=True)
    customer_id     = Column(String, nullable=False)
    customer_name   = Column(String)
    customer_phone  = Column(String)
    status          = Column(String)      # pending, shipped, delivered, cancelled
    item_name       = Column(String)
    order_date      = Column(String)
    delivery_date   = Column(String)
    return_eligible = Column(String)      # yes / no
    refund_status   = Column(String)      # none, initiated, processed

class CallLog(Base):
    __tablename__ = "call_logs"

    id            = Column(String, primary_key=True)
    customer_id   = Column(String)
    language      = Column(String)        # en, hi, hinglish
    intent        = Column(String)        # order_status, return_refund etc
    outcome       = Column(String)        # resolved / escalated
    duration_secs = Column(Integer)
    sentiment_avg = Column(Float)
    transcript    = Column(Text)          # full conversation stored as JSON
    created_at    = Column(DateTime, server_default=func.now())

class EscalationLog(Base):
    __tablename__ = "escalation_logs"

    id                = Column(String, primary_key=True)
    call_id           = Column(String)
    customer_name     = Column(String)
    issue_summary     = Column(Text)
    sentiment_history = Column(Text)      # JSON string of scores per turn
    recommended_tone  = Column(String)    # empathetic, firm, apologetic
    resolved          = Column(String)    # yes / no
    created_at        = Column(DateTime, server_default=func.now())

class DailyReport(Base):
    __tablename__ = "daily_reports"

    id                  = Column(String, primary_key=True)
    report_date         = Column(String)
    total_calls         = Column(Integer)
    resolved_calls      = Column(Integer)
    escalated_calls     = Column(Integer)
    avg_sentiment       = Column(Float)
    top_intent          = Column(String)
    unresolved_patterns = Column(Text)    # JSON string of top unresolved queries
    created_at          = Column(DateTime, server_default=func.now())