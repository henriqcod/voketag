"""
God Mode routes - super_admin only.
Kill switch, investigation mode, block country, risk limit, max alert, invalidate JWT.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from admin_service.core.auth.jwt import require_super_admin
from admin_service.domain.god_mode.service import GodModeService

router = APIRouter()


class KillSwitchBody(BaseModel):
    active: bool


class InvestigationBody(BaseModel):
    active: bool


class MaxAlertBody(BaseModel):
    active: bool


class RiskLimitBody(BaseModel):
    limit: int = Field(..., ge=0, le=100)


class BlockCountryBody(BaseModel):
    country: str = Field(..., min_length=2, max_length=2)


@router.get("/god-mode/state")
async def get_god_mode_state(current_user: dict = Depends(require_super_admin)):
    """Get current God Mode state."""
    svc = GodModeService()
    return await svc.get_state()


@router.post("/god-mode/kill-switch")
async def set_kill_switch(body: KillSwitchBody, current_user: dict = Depends(require_super_admin)):
    """Activate or deactivate kill switch."""
    svc = GodModeService()
    await svc.set_kill_switch(body.active)
    return {"message": "Kill switch " + ("activated" if body.active else "deactivated"), "active": body.active}


@router.post("/god-mode/investigation")
async def set_investigation_mode(body: InvestigationBody, current_user: dict = Depends(require_super_admin)):
    """Enable or disable investigation mode."""
    svc = GodModeService()
    await svc.set_investigation_mode(body.active)
    return {"message": "Investigation mode " + ("enabled" if body.active else "disabled"), "active": body.active}


@router.post("/god-mode/max-alert")
async def set_max_alert_mode(body: MaxAlertBody, current_user: dict = Depends(require_super_admin)):
    """Enable or disable maximum alert mode."""
    svc = GodModeService()
    await svc.set_max_alert_mode(body.active)
    return {"message": "Max alert mode " + ("enabled" if body.active else "disabled"), "active": body.active}


@router.get("/god-mode/risk-limit")
async def get_risk_limit(current_user: dict = Depends(require_super_admin)):
    svc = GodModeService()
    return {"risk_limit": await svc.get_risk_limit()}


@router.post("/god-mode/risk-limit")
async def set_risk_limit(body: RiskLimitBody, current_user: dict = Depends(require_super_admin)):
    svc = GodModeService()
    await svc.set_risk_limit(body.limit)
    return {"message": "Risk limit updated", "risk_limit": body.limit}


@router.get("/god-mode/blocked-countries")
async def get_blocked_countries(current_user: dict = Depends(require_super_admin)):
    svc = GodModeService()
    return {"blocked_countries": await svc.get_blocked_countries()}


@router.post("/god-mode/block-country")
async def block_country(body: BlockCountryBody, current_user: dict = Depends(require_super_admin)):
    svc = GodModeService()
    await svc.block_country(body.country)
    return {"message": f"Country {body.country} blocked", "blocked": body.country.upper()}


@router.post("/god-mode/unblock-country")
async def unblock_country(body: BlockCountryBody, current_user: dict = Depends(require_super_admin)):
    svc = GodModeService()
    await svc.unblock_country(body.country)
    return {"message": f"Country {body.country} unblocked"}


@router.post("/god-mode/invalidate-all-jwt")
async def invalidate_all_jwt(current_user: dict = Depends(require_super_admin)):
    """Invalidate all JWT refresh tokens. All users will need to log in again."""
    svc = GodModeService()
    await svc.invalidate_all_jwt()
    return {"message": "All JWT sessions invalidated"}
