"""
God Mode service - kill switch, investigation mode, block country, risk limit, etc.
Uses Redis for fast global state.
"""

from typing import List, Optional

from admin_service.config.settings import settings
from admin_service.core.redis_client import get_redis


GOD_KEYS = {
    "kill_switch": "god_mode:kill_switch",
    "investigation": "god_mode:investigation",
    "max_alert": "god_mode:max_alert",
    "risk_limit": "god_mode:risk_limit",
    "blocked_countries": "god_mode:blocked_countries",
    "jwt_invalidated_at": "god_mode:jwt_invalidated_at",
}


class GodModeService:
    async def _get_redis(self):
        return await get_redis()

    async def is_kill_switch_active(self) -> bool:
        r = await self._get_redis()
        return (await r.get(GOD_KEYS["kill_switch"])) == "1"

    async def set_kill_switch(self, active: bool) -> None:
        r = await self._get_redis()
        await r.set(GOD_KEYS["kill_switch"], "1" if active else "0")

    async def is_investigation_mode(self) -> bool:
        r = await self._get_redis()
        return (await r.get(GOD_KEYS["investigation"])) == "1"

    async def set_investigation_mode(self, active: bool) -> None:
        r = await self._get_redis()
        await r.set(GOD_KEYS["investigation"], "1" if active else "0")

    async def is_max_alert_mode(self) -> bool:
        r = await self._get_redis()
        return (await r.get(GOD_KEYS["max_alert"])) == "1"

    async def set_max_alert_mode(self, active: bool) -> None:
        r = await self._get_redis()
        await r.set(GOD_KEYS["max_alert"], "1" if active else "0")

    async def get_risk_limit(self) -> int:
        r = await self._get_redis()
        val = await r.get(GOD_KEYS["risk_limit"])
        return int(val) if val else 70

    async def set_risk_limit(self, limit: int) -> None:
        if not 0 <= limit <= 100:
            raise ValueError("Risk limit must be 0-100")
        r = await self._get_redis()
        await r.set(GOD_KEYS["risk_limit"], str(limit))

    async def get_blocked_countries(self) -> List[str]:
        r = await self._get_redis()
        return list(await r.smembers(GOD_KEYS["blocked_countries"]) or [])

    async def block_country(self, country_code: str) -> None:
        r = await self._get_redis()
        await r.sadd(GOD_KEYS["blocked_countries"], country_code.upper())

    async def unblock_country(self, country_code: str) -> None:
        r = await self._get_redis()
        await r.srem(GOD_KEYS["blocked_countries"], country_code.upper())

    async def invalidate_all_jwt(self) -> None:
        """Invalidate all JWT - sets a timestamp; refresh logic can check iat < this."""
        import time
        r = await self._get_redis()
        await r.set(GOD_KEYS["jwt_invalidated_at"], str(int(time.time())))

    async def get_state(self) -> dict:
        return {
            "kill_switch": await self.is_kill_switch_active(),
            "investigation_mode": await self.is_investigation_mode(),
            "max_alert_mode": await self.is_max_alert_mode(),
            "risk_limit": await self.get_risk_limit(),
            "blocked_countries": await self.get_blocked_countries(),
        }
