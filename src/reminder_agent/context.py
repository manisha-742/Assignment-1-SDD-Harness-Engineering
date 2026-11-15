"""Runtime and fixed evaluation reference contexts."""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ContextConfigurationError(ValueError):
    """Raised when local date/time interpretation is not configured safely."""


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    reference_instant: datetime
    time_zone: str
    locale: str | None
    source: Literal["runtime", "evaluation"]

    def __post_init__(self) -> None:
        if self.reference_instant.tzinfo is None:
            raise ContextConfigurationError("reference instant must be timezone-aware")
        try:
            ZoneInfo(self.time_zone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ContextConfigurationError(
                "time zone must be a valid IANA zone"
            ) from error
        if self.source not in ("runtime", "evaluation"):
            raise ContextConfigurationError(
                "context source must be runtime or evaluation"
            )

    @classmethod
    def from_environment(
        cls,
        environ: Mapping[str, str] | None = None,
        now: datetime | None = None,
    ) -> "RuntimeContext":
        settings = os.environ if environ is None else environ
        zone_name = settings.get("REMINDER_TIME_ZONE", "").strip()
        if not zone_name:
            raise ContextConfigurationError(
                "REMINDER_TIME_ZONE must be set to an IANA time-zone name"
            )
        try:
            zone = ZoneInfo(zone_name)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ContextConfigurationError(
                "REMINDER_TIME_ZONE must be a valid IANA time-zone name"
            ) from error

        configured_instant = settings.get("REMINDER_REFERENCE_INSTANT", "").strip()
        if now is not None:
            instant = now
        elif configured_instant:
            try:
                instant = datetime.fromisoformat(
                    configured_instant.replace("Z", "+00:00")
                )
            except ValueError as error:
                raise ContextConfigurationError(
                    "REMINDER_REFERENCE_INSTANT must be an ISO 8601 date-time "
                    "with an offset"
                ) from error
        else:
            instant = datetime.now(timezone.utc)
        if instant.tzinfo is None:
            if configured_instant and now is None:
                raise ContextConfigurationError(
                    "REMINDER_REFERENCE_INSTANT must include a UTC offset"
                )
            raise ContextConfigurationError(
                "reference instant must be timezone-aware; configure an ISO 8601 offset"
            )
        locale = settings.get("REMINDER_LOCALE", "").strip() or None
        return cls(
            reference_instant=instant.astimezone(zone),
            time_zone=zone_name,
            locale=locale,
            source="runtime",
        )

    @classmethod
    def fixed(
        cls,
        reference_instant: str | datetime,
        time_zone: str,
        locale: str | None,
    ) -> "RuntimeContext":
        instant = (
            datetime.fromisoformat(reference_instant.replace("Z", "+00:00"))
            if isinstance(reference_instant, str)
            else reference_instant
        )
        if instant.tzinfo is None:
            raise ContextConfigurationError(
                "fixed reference instant must include an offset"
            )
        try:
            zone = ZoneInfo(time_zone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ContextConfigurationError(
                "time zone must be a valid IANA zone"
            ) from error
        return cls(
            reference_instant=instant.astimezone(zone),
            time_zone=time_zone,
            locale=locale.strip() if locale and locale.strip() else None,
            source="evaluation",
        )
