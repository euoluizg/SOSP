import os

def is_feature_enabled(flag_name: str, default: bool = False) -> bool:
    """Verifica se uma feature flag está ativa via variável de ambiente (ADR-007)."""
    val = os.environ.get(flag_name)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")

# Flags padrão do MVP (ADR-007)
FEATURE_REVIEWS_ENABLED = is_feature_enabled("FEATURE_REVIEWS_ENABLED", False)
FEATURE_PUSH_ENABLED = is_feature_enabled("FEATURE_PUSH_ENABLED", False)
FEATURE_SMS_ENABLED = is_feature_enabled("FEATURE_SMS_ENABLED", False)
FEATURE_WHATSAPP_ENABLED = is_feature_enabled("FEATURE_WHATSAPP_ENABLED", False)
FEATURE_GOVBR_INTEGRATION_ENABLED = is_feature_enabled("FEATURE_GOVBR_INTEGRATION_ENABLED", False)
FEATURE_REPORTS_EXPORT = is_feature_enabled("FEATURE_REPORTS_EXPORT", True)

