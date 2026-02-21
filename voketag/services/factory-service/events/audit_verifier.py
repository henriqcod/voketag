"""
Audit Chain Integrity Verifier

Verifies the integrity of the audit event chain.
Used for compliance audits and forensic analysis.
"""

import json
import logging
from typing import List

logger = logging.getLogger(__name__)


def verify_chain_integrity(events: List[dict]) -> tuple[bool, List[str]]:
    """
    Verify the integrity of an audit event chain.

    Args:
        events: List of audit events in chronological order

    Returns:
        (is_valid, errors) - True if chain is valid, list of error messages
    """
    errors = []

    if not events:
        return True, []

    # First event should have genesis hash (all zeros)
    first_event = events[0]
    if first_event.get("previous_hash") != "0" * 64:
        errors.append("First event does not have genesis hash")

    # Verify each event in sequence
    for i, event in enumerate(events):
        event_num = i + 1

        # Verify hash chain
        if i > 0:
            expected_prev_hash = events[i - 1].get("current_hash")
            actual_prev_hash = event.get("previous_hash")

            if expected_prev_hash != actual_prev_hash:
                errors.append(
                    f"Event {event_num}: Hash chain broken. "
                    f"Expected previous_hash={expected_prev_hash}, "
                    f"got {actual_prev_hash}"
                )

        # Verify current hash computation
        if not _verify_event_hash(event):
            errors.append(
                f"Event {event_num}: Current hash verification failed. "
                f"Event may have been tampered with."
            )

        # Log verification progress
        if event_num % 100 == 0:
            logger.info(f"Verified {event_num} events...")

    is_valid = len(errors) == 0

    if is_valid:
        logger.info(f"Chain integrity verification passed: {len(events)} events")
    else:
        logger.error(
            f"Chain integrity verification FAILED: {len(errors)} errors in {len(events)} events"
        )

    return is_valid, errors


def _verify_event_hash(event: dict) -> bool:
    """Verify that event's current_hash is correctly computed."""
    import hashlib

    try:
        # Reconstruct event data for hashing
        event_data = {
            "user_id": event.get("user_id"),
            "action": event.get("action"),
            "resource_type": event.get("resource_type"),
            "resource_id": event.get("resource_id"),
            "payload_hash": event.get("payload_hash"),
            "request_id": event.get("request_id"),
            "ip_address": event.get("ip_address"),
            "timestamp": event.get("timestamp"),
        }

        event_str = json.dumps(event_data, sort_keys=True)
        combined = event.get("previous_hash", "") + event_str
        computed_hash = hashlib.sha256(combined.encode()).hexdigest()

        return computed_hash == event.get("current_hash")
    except Exception as e:
        logger.error(f"Error verifying event hash: {e}")
        return False


def export_audit_chain(events: List[dict], output_file: str) -> bool:
    """
    Export audit chain to file for compliance/forensics.

    Args:
        events: List of audit events
        output_file: Path to output JSON file

    Returns:
        True if successful
    """
    try:
        # Verify chain before export
        is_valid, errors = verify_chain_integrity(events)

        export_data = {
            "chain_valid": is_valid,
            "total_events": len(events),
            "errors": errors,
            "events": events,
        }

        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Audit chain exported to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to export audit chain: {e}")
        return False


def detect_tampering(events: List[dict]) -> List[int]:
    """
    Detect potentially tampered events in the chain.

    Args:
        events: List of audit events

    Returns:
        List of event indices that appear tampered
    """
    tampered = []

    for i, event in enumerate(events):
        if not _verify_event_hash(event):
            tampered.append(i)

    return tampered
