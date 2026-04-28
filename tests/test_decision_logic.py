"""Tests for the decision functions and honest cost model."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from build_dispatch_signal import (
    classify_price,
    compute_costs,
    decide_battery_action,
    decide_compute_mode,
    decide_power_source,
)


class TestClassifyPrice:
    @pytest.mark.parametrize("price,expected", [
        (0.05, "cheap"),
        (0.15, "cheap"),
        (0.20, "normal"),
        (0.34, "normal"),
        (0.35, "expensive"),
        (0.50, "expensive"),
    ])
    def test_thresholds(self, price, expected):
        assert classify_price(price) == expected


class TestDecideBatteryAction:
    def test_charge_when_cheap_and_not_full(self):
        assert decide_battery_action("cheap", "low") == "charge"
        assert decide_battery_action("cheap", "medium") == "charge"

    def test_no_charge_when_already_high(self):
        assert decide_battery_action("cheap", "high") == "hold"

    def test_discharge_when_expensive_and_not_empty(self):
        assert decide_battery_action("expensive", "high") == "discharge"
        assert decide_battery_action("expensive", "medium") == "discharge"

    def test_no_discharge_when_empty(self):
        assert decide_battery_action("expensive", "low") == "hold"

    def test_hold_when_normal(self):
        assert decide_battery_action("normal", "medium") == "hold"


class TestDecidePowerSource:
    def test_cheap_prefers_grid(self):
        assert decide_power_source("cheap", "high") == "grid"

    def test_expensive_prefers_battery(self):
        assert decide_power_source("expensive", "high") == "battery"

    def test_expensive_with_empty_battery_falls_back_hybrid(self):
        assert decide_power_source("expensive", "low") == "hybrid"


class TestDecideComputeMode:
    def test_thermal_dominates(self):
        assert decide_compute_mode("hot", "high", "cheap") == "critical_only"

    def test_warm_plus_expensive_reduces(self):
        assert decide_compute_mode("warm", "high", "expensive") == "reduced"

    def test_high_workload_runs_full(self):
        assert decide_compute_mode("normal", "high", "normal") == "full"


class TestComputeCosts:
    def _make_df(self, rows):
        return pd.DataFrame(rows)

    def test_grid_only_savings_are_zero(self):
        df = self._make_df([
            {"timestamp": "2026-01-01 00:00", "power_kw_total": 10,
             "electricity_price_usd_per_kwh": 0.20, "power_source": "grid"},
            {"timestamp": "2026-01-01 00:01", "power_kw_total": 10,
             "electricity_price_usd_per_kwh": 0.20, "power_source": "grid"},
        ])
        out = compute_costs(df)
        assert out["cost_savings"].sum() == pytest.approx(0.0)
        assert out["cost_actual"].sum() == pytest.approx(out["cost_baseline"].sum())

    def test_battery_at_high_price_saves_money(self):
        # Avg price = 0.25, imputed battery price = 0.25 / 0.85 ≈ 0.294.
        # At price = 0.40 > 0.294, battery use saves money.
        df = self._make_df([
            {"timestamp": "2026-01-01 00:00", "power_kw_total": 10,
             "electricity_price_usd_per_kwh": 0.10, "power_source": "grid"},
            {"timestamp": "2026-01-01 00:01", "power_kw_total": 10,
             "electricity_price_usd_per_kwh": 0.40, "power_source": "battery"},
        ])
        out = compute_costs(df)
        assert out["cost_savings"].sum() > 0

    def test_battery_at_low_price_loses_money(self):
        # Battery use at a price below the imputed cost should be negative savings.
        df = self._make_df([
            {"timestamp": "2026-01-01 00:00", "power_kw_total": 10,
             "electricity_price_usd_per_kwh": 0.30, "power_source": "grid"},
            {"timestamp": "2026-01-01 00:01", "power_kw_total": 10,
             "electricity_price_usd_per_kwh": 0.10, "power_source": "battery"},
        ])
        out = compute_costs(df)
        # Row 2 should show a loss (cost_actual > cost_baseline for that row).
        row = out.iloc[1]
        assert row["cost_actual"] > row["cost_baseline"]

    def test_dt_is_one_minute(self):
        # 1 row at 60 kW for 1 minute = 1 kWh, costing price * 1 kWh.
        df = self._make_df([
            {"timestamp": "2026-01-01 00:00", "power_kw_total": 60,
             "electricity_price_usd_per_kwh": 0.20, "power_source": "grid"},
        ])
        out = compute_costs(df)
        assert out["cost_baseline"].iloc[0] == pytest.approx(0.20)
