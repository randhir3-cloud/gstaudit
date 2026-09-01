"""Plugin manifest schema — contract every GAIS plugin must export."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PluginNavigationItem(BaseModel):
    label: str
    path: str
    permission: Optional[str] = None
    icon: str = ""


class PluginDashboardCard(BaseModel):
    dataset_key: str
    title: str
    component: str = "DatasetCard"


class PluginComparisonSpec(BaseModel):
    comparison_id: str
    left_dataset: str
    right_dataset: str
    label: str
    trigger_route: str = ""


class PluginJobSpec(BaseModel):
    job_type: str
    comparison_id: Optional[str] = None
    title: str = ""


class PluginReportSection(BaseModel):
    section_id: str
    title: str
    order: int = 0


class PluginManifest(BaseModel):
    """Declarative plugin contract surfaced to platform and operators."""

    id: str
    name: str
    version: str = "1.0.0"
    author: str = "GAIS"
    description: str = ""
    required_permissions: List[str] = Field(default_factory=list)
    routes: List[str] = Field(default_factory=list)
    cards: List[PluginDashboardCard] = Field(default_factory=list)
    jobs: List[PluginJobSpec] = Field(default_factory=list)
    reports: List[PluginReportSection] = Field(default_factory=list)
    comparisons: List[PluginComparisonSpec] = Field(default_factory=list)
    navigation: List[PluginNavigationItem] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)
    datasets: Dict[str, str] = Field(default_factory=dict)

    def to_public_dict(self) -> dict:
        return self.model_dump()
