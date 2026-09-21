"""Deliberately small exception hierarchy for Career OS's synthetic core."""

from __future__ import annotations


class CareerOSError(Exception):
    """Base error safe to show from the local CLI."""


class SchemaValidationError(CareerOSError):
    """A fixture or provider payload does not meet the typed contract."""


class ProviderUnavailable(CareerOSError):
    """A selected optional provider is not configured or reachable."""


class ProviderResponseError(CareerOSError):
    """A provider returned a response that cannot safely be scored."""


class ProviderAbstention(CareerOSError):
    """A provider deliberately declined a case without making a prediction."""


class StoreSafetyError(CareerOSError):
    """The requested SQLite database is not explicitly a synthetic Career OS store."""


class RevisionConflict(CareerOSError):
    """An optimistic-concurrency precondition did not match the durable revision."""


class EventConflict(CareerOSError):
    """An event id was reused for a different durable transition."""


class DuplicateBusinessApplication(CareerOSError):
    """A simulated application has the same verified business identity as an existing one."""


class RecoveryRequired(CareerOSError):
    """A submission state is unknown and must be reconciled before another send."""


class InvariantViolation(CareerOSError):
    """A requested state transition would falsify a Career OS domain invariant."""
