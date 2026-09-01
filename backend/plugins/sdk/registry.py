"""Central plugin registry — navigation, routes, comparators, jobs, cards."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter

from plugins.sdk.manifest import PluginManifest

ComparisonRunner = Callable[..., Any]


class PluginRegistry:
    def __init__(self) -> None:
        self._manifests: Dict[str, PluginManifest] = {}
        self._routers: List[APIRouter] = []
        self._comparison_runners: Dict[str, ComparisonRunner] = {}
        self._merge_handlers: Dict[str, Callable] = {}
        self._validators: Dict[str, Callable] = {}
        self._upload_handlers: Dict[str, Callable] = {}
        self._report_sections: Dict[str, List[dict]] = {}
        self._permissions: set[str] = set()
        self._datasets: Dict[str, str] = {}
        self._comparison_pairs: List[dict] = []
        self._navigation: List[dict] = []
        self._dashboard_cards: List[dict] = []
        self._audit_actions: Dict[str, str] = {}

    def register_manifest(self, manifest: PluginManifest) -> None:
        self._manifests[manifest.id] = manifest
        for perm in manifest.required_permissions:
            self._permissions.add(perm)
        for card in manifest.cards:
            self._dashboard_cards.append({**card.model_dump(), "plugin_id": manifest.id})
        for comp in manifest.comparisons:
            self._comparison_pairs.append({**comp.model_dump(), "plugin_id": manifest.id})
        for nav in manifest.navigation:
            self._navigation.append({**nav.model_dump(), "plugin_id": manifest.id})
        for dataset_key, label in manifest.datasets.items():
            self._datasets[dataset_key] = label
        for report in manifest.reports:
            self._report_sections.setdefault(manifest.id, []).append(report.model_dump())
        for route in manifest.routes:
            action = manifest.settings.get("audit_actions", {}).get(route)
            if action:
                self._audit_actions[route] = action

    def add_router(self, router: APIRouter) -> None:
        self._routers.append(router)

    def register_comparison_runner(self, comparison_id: str, runner: ComparisonRunner) -> None:
        self._comparison_runners[comparison_id] = runner

    def get_comparison_runner(self, comparison_id: str) -> Optional[ComparisonRunner]:
        return self._comparison_runners.get(comparison_id)

    def register_merge_handler(self, dataset_key: str, handler: Callable) -> None:
        self._merge_handlers[dataset_key] = handler

    def get_merge_handler(self, dataset_key: str) -> Optional[Callable]:
        return self._merge_handlers.get(dataset_key)

    def register_validator(self, name: str, handler: Callable) -> None:
        self._validators[name] = handler

    def register_upload_handler(self, dataset_key: str, handler: Callable) -> None:
        self._upload_handlers[dataset_key] = handler

    def list_manifests(self) -> List[PluginManifest]:
        return list(self._manifests.values())

    def get_manifest(self, plugin_id: str) -> Optional[PluginManifest]:
        return self._manifests.get(plugin_id)

    @property
    def routers(self) -> List[APIRouter]:
        return list(self._routers)

    @property
    def datasets(self) -> Dict[str, str]:
        return dict(self._datasets)

    @property
    def comparison_pairs(self) -> List[dict]:
        return list(self._comparison_pairs)

    @property
    def navigation(self) -> List[dict]:
        return list(self._navigation)

    @property
    def dashboard_cards(self) -> List[dict]:
        return list(self._dashboard_cards)

    @property
    def permissions(self) -> List[str]:
        return sorted(self._permissions)

    @property
    def audit_actions(self) -> Dict[str, str]:
        return dict(self._audit_actions)

    def public_catalog(self) -> dict:
        return {
            "plugins": [m.to_public_dict() for m in self.list_manifests()],
            "datasets": self.datasets,
            "comparison_pairs": self.comparison_pairs,
            "navigation": self.navigation,
            "dashboard_cards": self.dashboard_cards,
        }


plugin_registry = PluginRegistry()
