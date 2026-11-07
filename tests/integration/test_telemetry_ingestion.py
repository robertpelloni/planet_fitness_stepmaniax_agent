import pytest
import os
from app import app, db
from models import EquipmentMetric, TelemetryHistory, ServiceDispatch
from ingest_telemetry_packet import ingest_packet

@pytest.fixture
def clean_equipment_setup():
    """Sets up a clean test unit for telemetry ingestion tests."""
    with app.app_context():
        # Clean existing test equipment or dispatches
        unit = EquipmentMetric.query.filter_by(equipment_name="CI-Telemetry-Unit").first()
        if unit:
            ServiceDispatch.query.filter_by(equipment_id=unit.id).delete()
            TelemetryHistory.query.filter_by(equipment_id=unit.id).delete()
            db.session.delete(unit)
            db.session.commit()

        new_unit = EquipmentMetric(
            equipment_name="CI-Telemetry-Unit",
            location="PF-Automated-Test-Lab",
            franchise_id="EPIC-TEST",
            uptime_percent=99.5,
            total_scans=100,
            avg_session_duration=10.0,
            total_sessions=10,
            maintenance_status="Operational"
        )
        db.session.add(new_unit)
        db.session.commit()
        unit_id = new_unit.id

    yield unit_id

    with app.app_context():
        u = db.session.get(EquipmentMetric, unit_id)
        if u:
            ServiceDispatch.query.filter_by(equipment_id=unit_id).delete()
            TelemetryHistory.query.filter_by(equipment_id=unit_id).delete()
            db.session.delete(u)
            db.session.commit()


def test_telemetry_normal_ingestion(clean_equipment_setup):
    """Verifies standard telemetry packet ingestion updates sessions, scans, and average duration."""
    unit_id = clean_equipment_setup
    result = ingest_packet(
        equipment_id=unit_id,
        session_duration=12.0,
        scans_count=15,
        uptime_percent=99.2
    )

    assert result["status"] == "success"
    assert result["equipment_id"] == unit_id
    assert result["uptime_percent"] == 99.2
    assert result["total_scans"] == 115
    assert result["total_sessions"] == 11
    assert result["dispatched_ticket"] is None

    with app.app_context():
        history = TelemetryHistory.query.filter_by(equipment_id=unit_id).first()
        assert history is not None
        assert history.duration_minutes == 12.0
        assert history.scans_count == 15


def test_telemetry_low_uptime_triggers_service_dispatch(clean_equipment_setup):
    """Verifies that an anomaly (uptime < 95%) triggers an autonomous ServiceDispatch."""
    unit_id = clean_equipment_setup
    result = ingest_packet(
        equipment_id=unit_id,
        session_duration=2.5,
        scans_count=5,
        uptime_percent=92.0
    )

    assert result["status"] == "success"
    assert result["uptime_percent"] == 92.0
    assert result["dispatched_ticket"] is not None
    assert result["dispatched_ticket"].startswith("AUTO-DISP-")

    with app.app_context():
        unit = db.session.get(EquipmentMetric, unit_id)
        assert unit.maintenance_status == "Service Dispatched"

        dispatch = ServiceDispatch.query.filter_by(equipment_id=unit_id, status='Pending').first()
        assert dispatch is not None
        assert "Predictive health anomaly" in dispatch.notes
