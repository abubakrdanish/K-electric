"""Shared dispatch math used by controllers."""

from __future__ import annotations

INVERTER_LIMIT_MW = 50.0
EXPORT_CAP_MW = 50.0
IMPORT_CAP_MW = 120.0


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def balance_net_demand(
    demand_mw: float,
    solar_mw: float,
    *,
    soc: float,
    price: float,
    soc_floor: float | None = None,
    fcas_reserve_mw: float = 0.0,
    price_history: list[float] | None = None,
) -> dict[str, float]:
    """Baseline duck-curve dispatch with safety rails."""
    solar_surplus = solar_mw - demand_mw
    battery_flow = 0.0
    curtail_solar = 0.0
    emergency_generator = 0.0

    inverter_headroom = INVERTER_LIMIT_MW - fcas_reserve_mw
    avg_price = (
        sum(price_history[-12:]) / len(price_history[-12:])
        if price_history and len(price_history) >= 4
        else price
    )

    target_soc = soc_floor if soc_floor is not None else 0.5

    if solar_surplus > 0 and soc < 0.95:
        battery_flow = -min(solar_surplus, inverter_headroom)
    elif solar_surplus < 0:
        deficit = abs(solar_surplus)
        if soc_floor is not None and soc < target_soc + 0.05:
            battery_flow = 0.0
        elif price >= avg_price and soc > max(0.15, target_soc - 0.1):
            battery_flow = min(deficit, inverter_headroom)
        elif price < 0 and soc < 0.9:
            battery_flow = -min(inverter_headroom, deficit + 10.0)

    if soc_floor is not None and soc < target_soc:
        needed = (target_soc - soc) * 100.0 / 0.25
        battery_flow = min(battery_flow, 0.0)
        battery_flow = max(battery_flow, -min(needed, inverter_headroom))

    net_city_demand = demand_mw - solar_mw - battery_flow

    if net_city_demand < -EXPORT_CAP_MW:
        curtail_solar = abs(net_city_demand) - EXPORT_CAP_MW
    elif net_city_demand > IMPORT_CAP_MW:
        emergency_generator = net_city_demand - IMPORT_CAP_MW

    return {
        "battery_flow_mw": battery_flow,
        "emergency_generator": emergency_generator,
        "curtail_solar": curtail_solar,
        "fcas_reserve_mw": fcas_reserve_mw,
    }
