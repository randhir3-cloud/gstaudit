"""GAIS Audit Intelligence — automated analysis of comparison results."""

__all__ = ["analyze_session", "get_case_intelligence"]


def __getattr__(name: str):
    if name in __all__:
        from intelligence.intelligence_service import analyze_session, get_case_intelligence

        return {"analyze_session": analyze_session, "get_case_intelligence": get_case_intelligence}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
