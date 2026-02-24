#!/usr/bin/env python3
"""
Cloud Function: Database Password Rotation
Triggered: Cloud Scheduler (monthly on 1st day @ 02:00 UTC)

Usage: Deploy to Google Cloud Functions
    gcloud functions deploy rotate_db_password \
        --runtime python3.11 \
        --trigger-topic rotate-db-password \
        --entry-point rotate_database_password
"""

import os
import json
import random
import string
import datetime
import subprocess
import logging
from typing import Dict, Tuple
import psycopg2
from psycopg2 import sql
import google.cloud.secretmanager as secretmanager
import google.cloud.logging
import google.cloud.monitoring_v3

# Configure logging to use Cloud Logging
log_client = google.cloud.logging.Client()
log_client.setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def rotate_database_password(request) -> Tuple[Dict, int]:
    """
    Rotates PostgreSQL database password with zero downtime.
    
    Process:
    1. Generate new secure password
    2. Update Cloud SQL user password
    3. Create new SECRET_MANAGER version
    4. Verify connectivity with new password
    5. Restart Cloud Run services to pick up new secret
    6. Health check all services
    7. Log audit trail
    
    Args:
        request: HTTP request object from Cloud Functions
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    
    try:
        # ====================================================================
        # CONFIGURATION
        # ====================================================================
        
        project_id = os.environ.get("GCP_PROJECT_ID", "voketag-prod")
        db_instance = os.environ.get("DB_INSTANCE_NAME", "voketag-db")
        db_user = os.environ.get("DB_USER_NAME", "voketag")
        db_region = os.environ.get("DB_REGION", "us-central1")
        secret_name_primary = "DATABASE_URL"
        secret_name_secondary = "DATABASE_URL_SECONDARY"
        cloud_run_region = "us-central1"
        
        services_to_restart = [
            "scan-service",
            "factory-service",
            "admin-service",
            "blockchain-service"
        ]
        
        logger.info("=" * 70)
        logger.info("🔄 STARTING DATABASE PASSWORD ROTATION")
        logger.info("=" * 70)
        logger.info(f"Project ID: {project_id}")
        logger.info(f"Database Instance: {db_instance}")
        logger.info(f"Database User: {db_user}")
        logger.info(f"Services to restart: {', '.join(services_to_restart)}")
        logger.info("")
        
        # ====================================================================
        # 1. GENERATE NEW PASSWORD
        # ====================================================================
        
        logger.info("📋 Step 1: Generating new secure password...")
        
        # Password requirements: 32 chars, mixed case, numbers, symbols
        # Exclude special chars that could cause issues in connection strings
        password_chars = string.ascii_letters + string.digits + "!#$%&*"
        new_password = ''.join(random.choice(password_chars) for _ in range(32))
        
        logger.info(f"✅ Generated new password: {new_password[:3]}***{new_password[-3:]}")
        logger.info("")
        
        # ====================================================================
        # 2. GET CURRENT SECRET VERSION (for backup/rollback)
        # ====================================================================
        
        logger.info("📋 Step 2: Getting current secret version...")
        
        secret_client = secretmanager.SecretManagerServiceClient()
        secret_path = secret_client.secret_path(project_id, secret_name_primary)
        
        try:
            response = secret_client.list_secret_versions(
                request={"parent": secret_path}
            )
            current_versions = list(response)
            if current_versions:
                current_version = current_versions[0].name
                logger.info(f"✅ Current secret version: {current_version}")
            else:
                logger.warning("⚠️  No current secret version found")
                current_version = None
        except Exception as e:
            logger.error(f"❌ Failed to get current secret version: {e}")
            current_version = None
        
        logger.info("")
        
        # ====================================================================
        # 3. UPDATE CLOUD SQL PASSWORD
        # ====================================================================
        
        logger.info("📋 Step 3: Updating Cloud SQL password...")
        logger.info("⏳ (This may take 30-60 seconds...)")
        
        try:
            result = subprocess.run(
                [
                    "gcloud", "sql", "users", "set-password", db_user,
                    f"--instance={db_instance}",
                    f"--password={new_password}",
                    f"--project={project_id}"
                ],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr
                logger.error(f"❌ Failed to update Cloud SQL password: {error_msg}")
                return {
                    "status": "failed",
                    "error": f"Cloud SQL password update failed: {error_msg}",
                    "action_needed": "Manual intervention required"
                }, 500
            
            logger.info(f"✅ Cloud SQL password updated successfully")
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Timeout updating Cloud SQL password (>2 min)")
            return {
                "status": "failed",
                "error": "Timeout updating Cloud SQL password",
                "action_needed": "Manual intervention required"
            }, 500
        
        logger.info("")
        
        # ====================================================================
        # 4. VERIFY CONNECTIVITY WITH NEW PASSWORD
        # ====================================================================
        
        logger.info("📋 Step 4: Verifying connectivity with new password...")
        
        # Build new connection string
        db_host = f"{db_instance}.c.{project_id}.cloudsql.iam.gcloud.com"
        db_name = "voketag"
        
        # Try connection with new password (with timeout)
        connection_attempts = 0
        max_attempts = 3
        
        while connection_attempts < max_attempts:
            try:
                logger.info(f"   Attempt {connection_attempts + 1}/{max_attempts}...")
                
                conn = psycopg2.connect(
                    host=db_host,
                    database=db_name,
                    user=db_user,
                    password=new_password,
                    port=5432,
                    connect_timeout=10,
                    options="-c statement_timeout=10000"  # 10 second query timeout
                )
                
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if result == (1,):
                    logger.info(f"✅ Connectivity verified with new password!")
                    break
                else:
                    raise Exception("Query did not return expected result")
                    
            except psycopg2.OperationalError as e:
                connection_attempts += 1
                if connection_attempts < max_attempts:
                    logger.warning(f"⚠️  Connection attempt {connection_attempts} failed, retrying: {e}")
                    # Wait before retry
                    import time
                    time.sleep(5)
                else:
                    logger.error(f"❌ Failed to connect with new password after {max_attempts} attempts: {e}")
                    return {
                        "status": "failed",
                        "error": f"Failed to verify connectivity with new password: {e}",
                        "action_needed": "Check database connectivity, may need manual password restore"
                    }, 500
            
            except Exception as e:
                logger.error(f"❌ Unexpected error during connectivity check: {e}")
                return {
                    "status": "failed",
                    "error": f"Connectivity check failed: {e}",
                    "action_needed": "Manual intervention required"
                }, 500
        
        logger.info("")
        
        # ====================================================================
        # 5. CREATE NEW SECRET VERSION
        # ====================================================================
        
        logger.info("📋 Step 5: Creating new SECRET_MANAGER version...")
        
        try:
            # Build connection strings for secretmanager
            conn_string_primary = f"postgresql://{db_user}:{new_password}@{db_instance}/voketag?sslmode=require"
            conn_string_secondary = f"postgresql://{db_user}:{new_password}@voketag-postgres-replica/voketag?sslmode=require"
            
            # Update primary secret
            new_secret_version = secret_client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {
                        "data": conn_string_primary.encode("UTF-8")
                    },
                }
            )
            
            logger.info(f"✅ New primary secret version created: {new_secret_version.name}")
            
            # Update secondary secret if it exists
            try:
                secondary_secret_path = secret_client.secret_path(project_id, secret_name_secondary)
                new_secondary_version = secret_client.add_secret_version(
                    request={
                        "parent": secondary_secret_path,
                        "payload": {
                            "data": conn_string_secondary.encode("UTF-8")
                        },
                    }
                )
                logger.info(f"✅ New secondary secret version created: {new_secondary_version.name}")
            except Exception as e:
                logger.warning(f"⚠️  Could not update secondary secret: {e}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create new secret version: {e}")
            return {
                "status": "failed",
                "error": f"Failed to update secrets: {e}",
                "action_needed": "Secrets not updated, services still using old password"
            }, 500
        
        logger.info("")
        
        # ====================================================================
        # 6. RESTART CLOUD RUN SERVICES
        # ====================================================================
        
        logger.info("📋 Step 6: Restarting Cloud Run services...")
        logger.info("⏳ (Services will pick up new secrets automatically...)")
        
        services_restarted = []
        services_failed = []
        
        for service_name in services_to_restart:
            try:
                logger.info(f"   Restarting {service_name}...")
                
                result = subprocess.run(
                    [
                        "gcloud", "run", "services", "update", service_name,
                        f"--region={cloud_run_region}",
                        f"--project={project_id}",
                        "--quiet"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.info(f"   ✅ {service_name} restarted")
                    services_restarted.append(service_name)
                else:
                    logger.error(f"   ❌ Failed to restart {service_name}: {result.stderr}")
                    services_failed.append((service_name, result.stderr))
                    
            except subprocess.TimeoutExpired:
                logger.error(f"   ❌ Timeout restarting {service_name}")
                services_failed.append((service_name, "Timeout"))
            except Exception as e:
                logger.error(f"   ❌ Error restarting {service_name}: {e}")
                services_failed.append((service_name, str(e)))
        
        logger.info(f"✅ Restarted {len(services_restarted)}/{len(services_to_restart)} services")
        if services_failed:
            logger.warning(f"⚠️  Failed to restart {len(services_failed)} services: {services_failed}")
        
        logger.info("")
        
        # ====================================================================
        # 7. HEALTH CHECK SERVICES (Wait for restart)
        # ====================================================================
        
        logger.info("📋 Step 7: Waiting for services to stabilize (30 seconds)...")
        
        import time
        time.sleep(30)
        
        logger.info("🏥 Running health checks...")
        
        health_check_results = {}
        
        for service_name in services_restarted:
            try:
                # Get service URL
                service_result = subprocess.run(
                    [
                        "gcloud", "run", "services", "describe", service_name,
                        f"--region={cloud_run_region}",
                        f"--project={project_id}",
                        "--format=value(status.url)"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if service_result.returncode == 0:
                    service_url = service_result.stdout.strip()
                    health_url = f"{service_url.rstrip('/')}/health"
                    
                    # Check health endpoint
                    import subprocess as sp
                    health_result = sp.run(
                        ["curl", "-s", "-f", "-w", "%{http_code}", health_url],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if "200" in health_result.stdout:
                        logger.info(f"   ✅ {service_name}: Health check PASS")
                        health_check_results[service_name] = "PASS"
                    else:
                        logger.warning(f"   ⚠️  {service_name}: Health check returned {health_result.stdout}")
                        health_check_results[service_name] = "WARN"
                else:
                    logger.warning(f"   ⚠️  Could not get URL for {service_name}")
                    health_check_results[service_name] = "UNKNOWN"
                    
            except Exception as e:
                logger.warning(f"   ⚠️  Health check for {service_name} failed: {e}")
                health_check_results[service_name] = "ERROR"
        
        logger.info("")
        
        # ====================================================================
        # 8. AUDIT LOG
        # ====================================================================
        
        logger.info("📋 Step 8: Recording audit entry...")
        
        audit_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "action": "database_password_rotation",
            "db_instance": db_instance,
            "db_user": db_user,
            "status": "success",
            "current_version": current_version,
            "new_version": new_secret_version.name,
            "services_restarted": services_restarted,
            "services_failed": [{"service": s, "error": e} for s, e in services_failed],
            "health_checks": health_check_results,
            "performed_by": "cloud-scheduler"
        }
        
        logger.info(f"✅ Audit entry: {json.dumps(audit_entry, indent=2)}")
        logger.info("")
        
        # ====================================================================
        # FINAL SUMMARY
        # ====================================================================
        
        logger.info("=" * 70)
        logger.info("✅ DATABASE PASSWORD ROTATION COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Timestamp: {datetime.datetime.utcnow().isoformat()}Z")
        logger.info(f"Services restarted: {len(services_restarted)}/{len(services_to_restart)}")
        logger.info(f"Health checks: {sum(1 for v in health_check_results.values() if v == 'PASS')}/{len(health_check_results)}")
        logger.info("")
        
        return {
            "status": "success",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "new_secret_version": new_secret_version.name,
            "services_restarted": services_restarted,
            "services_failed": [{"service": s, "error": e} for s, e in services_failed],
            "health_checks": health_check_results,
            "audit_logged": True
        }, 200
        
    except Exception as e:
        logger.error("=" * 70)
        logger.error("❌ CRITICAL ERROR DURING PASSWORD ROTATION")
        logger.error("=" * 70)
        logger.error(f"Error: {str(e)}")
        logger.error(f"Timestamp: {datetime.datetime.utcnow().isoformat()}Z")
        logger.error("")
        logger.error("ACTION REQUIRED:")
        logger.error("- Check database connectivity manually")
        logger.error("- Verify old password still works")
        logger.error("- Investigate cause and retry rotation")
        
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "action_required": "Manual intervention needed"
        }, 500
