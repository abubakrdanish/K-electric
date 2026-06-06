"""Main submission target: Strategy class with plan/replan/step lifecycle."""

from __future__ import annotations

from lib.dispatch import balance_net_demand
from lib.llm import parse_alert_with_llm
from lib.parsing import is_actionable_directive, parse_export_cap_mw, parse_soc_floor


class Strategy:
    def __init__(self):
        self.handled_alert_ids: set[str] = set()
        self.soc_floor: float | None = None
        self.export_cap_mw: float | None = None
        self.stance = "balanced"
        self.price_history: list[float] = []

    def plan(self, state: dict) -> dict:
        for alert in state.get("alerts", []):
            self._ingest_alert(alert)
        return {}

    def replan(self, state: dict, alerts: list) -> dict:
        new_alerts = [a for a in alerts if a.get("id") not in self.handled_alert_ids]
        if not new_alerts:
            return {}

        for alert in new_alerts:
            self._ingest_alert(alert)
        return {}

    def _ingest_alert(self, alert: dict) -> None:
        alert_id = alert.get("id")
        if not alert_id or alert_id in self.handled_alert_ids:
            return
        if not is_actionable_directive(alert):
            self.handled_alert_ids.add(alert_id)
            return

        description = alert.get("description", "")
        floor = parse_soc_floor(description)
        if floor is not None:
            self.soc_floor = floor

        export_cap = parse_export_cap_mw(description)
        if export_cap is not None:
            self.export_cap_mw = export_cap

        llm = parse_alert_with_llm(description)
        if llm.get("soc_floor") is not None:
            self.soc_floor = float(llm["soc_floor"])
        if llm.get("export_cap_mw") is not None:
            self.export_cap_mw = float(llm["export_cap_mw"])
        if llm.get("stance") in {"balanced", "conserve", "aggressive"}:
            self.stance = llm["stance"]

        self.handled_alert_ids.add(alert_id)

    def step(self, state: dict) -> dict:
        demand = float(state.get("demand", 0.0))
        solar = float(state.get("solar", 0.0))
        soc = float(state.get("soc", 0.5))
        price = float(state.get("price", 0.0))
        self.price_history.append(price)

        action = balance_net_demand(
            demand,
            solar,
            soc=soc,
            price=price,
            soc_floor=self.soc_floor,
            price_history=self.price_history,
        )

        if self.stance == "conserve":
            action["battery_flow_mw"] = min(action["battery_flow_mw"], 0.0)

        if self.export_cap_mw is not None:
            net = demand - solar
            flow = action["battery_flow_mw"]
            export_mw = max(0.0, -(net - flow))
            action["curtail_solar"] = max(
                action["curtail_solar"],
                max(0.0, export_mw - self.export_cap_mw),
            )

        return action
