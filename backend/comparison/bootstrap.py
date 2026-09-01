"""Register GSTR-1 comparator — core bootstrap (routes via plugins/gstr1)."""

from comparison.comparators.gstr1_vs_eway_outward import compare_gstr1_vs_eway_outward
from comparison.models import ComparisonConfig
from comparison.registry import comparison_registry

GSTR1_EWB_CONFIG = ComparisonConfig(
    comparison_id="gstr1_ewb_outward",
    left_dataset="gstr1",
    right_dataset="ewb_outward",
    left_label="GSTR-1",
    right_label="EWB OUTWARD",
)

comparison_registry.register("gstr1_ewb_outward", GSTR1_EWB_CONFIG, compare_gstr1_vs_eway_outward)
