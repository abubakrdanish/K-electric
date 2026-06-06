"""Simple function controller — good starting point for duck_curve."""

from lib.dispatch import balance_net_demand


def controller(state: dict) -> dict:
    demand = float(state.get("demand", 0.0))
    solar = float(state.get("solar", 0.0))
    soc = float(state.get("soc", 0.5))
    price = float(state.get("price", 0.0))

    return balance_net_demand(
        demand,
        solar,
        soc=soc,
        price=price,
    )
