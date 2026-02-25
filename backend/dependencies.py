from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

settings = get_settings()

RATE_LIMIT = f"{settings.rate_limit_per_day}/day" if settings.rate_limit_per_day > 0 else "99999/day"
ATTACK_RATE_LIMIT_SCOPE = "attack-endpoints"
JUDGE_MODEL = settings.judge_model

limiter = Limiter(key_func=get_remote_address)
