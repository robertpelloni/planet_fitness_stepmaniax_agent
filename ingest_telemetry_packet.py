#!/usr/bin/env python3
"""
Telemetry Ingestion Engine & Predictive Maintenance Dispatcher (v9.4.0)

Ingests real-time hardware telemetry packets from 9-panel StepManiaX/Andamiro units,
updating EquipmentMetric stats, logging raw telemetry sessions in TelemetryHistory,
re-calculating predictive health scores via analytics, and triggering automated
service dispatches when critical anomalies occur.
"""

import os
import sys
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

if not os.path.exists('logs'):
    os.makedirs('logs', exist_ok=True)

logger = logging.getLogger('telemetry_ingest')
handler = RotatingFileHandler('logs/telemetry_ingest.log', maxBytes=1048576, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def ingest_packet(equipment_id, session_duration=None, scans_count=1, uptime_percent=None, member_id=None):
    """
    Ingests a single hardware telemetry packet.

    Args:
        equipment_id (int): Primary key of the EquipmentMetric unit.
        session_duration (float, optional): Duration of the session in minutes.
        scans_count (int): Scans/steps recorded in this packet.
        uptime_percent (float, optional): Current calculated uptime percentage.
        member_id (int, optional): Associated member ID if identified.

    Returns:
        dict: Ingestion summary including health score and generated dispatches.
    """
    os.environ.setdefault('SECRET_KEY', 'dev-key')
    from app import app, db
    from models import EquipmentMetric, TelemetryHistory, ServiceDispatch
    import analytics

    with app.app_context():
        unit = db.session.get(EquipmentMetric, equipment_id)
        if not unit:
            logger.error(f"Ingestion failed: EquipmentMetric unit {equipment_id} not found.")
            return {"status": "error", "message": f"Unit {equipment_id} not found"}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        unit.last_heartbeat = now_str

        if uptime_percent is not None:
            unit.uptime_percent = float(uptime_percent)

        if scans_count:
            unit.total_scans = (unit.total_scans or 0) + int(scans_count)

        if session_duration is not None and float(session_duration) > 0:
            duration = float(session_duration)
            total_sessions = (unit.total_sessions or 0) + 1
            old_avg = unit.avg_session_duration or 0.0
            # Cumulative moving average
            new_avg = ((old_avg * (total_sessions - 1)) + duration) / total_sessions
            unit.total_sessions = total_sessions
            unit.avg_session_duration = round(new_avg, 2)

            history = TelemetryHistory(
                equipment_id=unit.id,
                member_id=member_id,
                timestamp=now_str,
                scans_count=scans_count,
                duration_minutes=duration
            )
            db.session.add(history)

        # Recalculate predictive health score
        unit_data = {
            'total_sessions': unit.total_sessions,
            'uptime_percent': unit.uptime_percent,
            'total_scans': unit.total_scans,
            'avg_session_duration': unit.avg_session_duration
        }
        unit.predictive_health_score = analytics.calculate_predictive_health_score(unit_data)

        # Autonomous Maintenance Dispatch Check
        dispatched_ticket = None
        if unit.uptime_percent < 95.0 or (unit.predictive_health_score and unit.predictive_health_score < 70.0):
            import secrets
            unit.maintenance_status = "Needs Maintenance"
            existing_dispatch = ServiceDispatch.query.filter_by(equipment_id=unit.id, status='Pending').first()
            if not existing_dispatch:
                ticket_id = f"AUTO-DISP-{secrets.token_hex(4).upper()}"
                dispatch = ServiceDispatch(
                    ticket_id=ticket_id,
                    equipment_id=unit.id,
                    provider="Andamiro Field Service SLA",
                    notes=f"Predictive health anomaly: Health Score {unit.predictive_health_score}, Uptime {unit.uptime_percent}%",
                    status="Pending",
                    created_at=now_str
                )
                db.session.add(dispatch)
                unit.maintenance_status = "Service Dispatched"
                dispatched_ticket = ticket_id
                logger.info(f"Triggered autonomous SLA dispatch {ticket_id} for unit {unit.id}")

        db.session.commit()
        logger.info(f"Successfully ingested packet for Unit {unit.id} ({unit.equipment_name}). Health Score: {unit.predictive_health_score}")

        return {
            "status": "success",
            "equipment_id": unit.id,
            "equipment_name": unit.equipment_name,
            "uptime_percent": unit.uptime_percent,
            "total_scans": unit.total_scans,
            "total_sessions": unit.total_sessions,
            "avg_session_duration": unit.avg_session_duration,
            "predictive_health_score": unit.predictive_health_score,
            "dispatched_ticket": dispatched_ticket
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Ingest StepManiaX Hardware Telemetry Packet")
    parser.add_argument("--equipment-id", type=int, required=True, help="Equipment ID")
    parser.add_argument("--duration", type=float, default=None, help="Session duration in minutes")
    parser.add_argument("--scans", type=int, default=1, help="Scans or steps count")
    parser.add_argument("--uptime", type=float, default=None, help="Uptime percentage")
    parser.add_argument("--member-id", type=int, default=None, help="Member ID")

    args = parser.parse_args()
    result = ingest_packet(
        equipment_id=args.equipment_id,
        session_duration=args.duration,
        scans_count=args.scans,
        uptime_percent=args.uptime,
        member_id=args.member_id
    )
    print(result)


if __name__ == "__main__":
    main()
