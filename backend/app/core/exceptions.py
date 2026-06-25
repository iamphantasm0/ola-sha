class OlaError(Exception):
    """Base application error."""


class ProviderError(OlaError):
    """Raised when an upstream provider (Paycrest) returns an error."""


class StateError(OlaError):
    """Raised when an action is attempted in an invalid order state."""
