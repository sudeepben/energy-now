"""Tests for decide_dispatch and the blackout / runtime additions."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from build_dispatch_signal import (
    BATTERY_CAPACITY_KWH,
    SOC_CRITICAL_PCT,
    SOC_DEPLETED_PCT,
    battery_runtime_minutes,
    decide_dispatch,
)


def make_state(**overrides):
    base = {
        "electricity_price_usd_per_kwh": 0.20,
        "battery_state": "high",
        "thermal_state": "normal",
        "workload_state": "high",
        "battery_soc_pct": 80.0,
        "power_kw_total": 12.0,
    }
    base.update(overrides)
    return base


class TestBatteryRuntime:
    def test_zero_load_is_infinite(self):
        assert battery_runtime_minutes(soc_pct=50, load_kw=0) == float("inf")

    def test_below_floor_is_zero(self):
        assert battery_runtime_minutes(soc_pct=SOC_DEPLETED_PCT - 1, load_kw=10) == 0

    def test_known_value(self):
        # 50% of 500 kWh = 250 kWh usable above the 5% floor (45% × 500 = 225 kWh).
        # At 60 kW load: 225 / 60 = 3.75 hours = 225 minutes.
        runtime = battery_runtime_minutes(
            soc_pct=50, load_kw=60, capacity_kwh=500, floor_pct=SOC_DEPLETED_PCT,
        )
        assert runtime == pytest.approx(225.0, rel=1e-3)


class TestDecideDispatchNormal:
    def test_returns_required_keys(self):
        out = decide_dispatch(make_state(), grid_available=True)
        for key in ("price_state", "battery_action", "power_source",
                    "compute_mode", "decision_reason", "battery_runtime_minutes"):
            assert key in out

    def test_normal_does_not_emit_blackout_reason(self):
        out = decide_dispatch(make_state(), grid_available=True)
        assert not out["decision_reason"].startswith("blackout_")

    def test_runtime_is_finite_under_load(self):
        out = decide_dispatch(make_state(power_kw_total=20), grid_available=True)
        assert out["battery_runtime_minutes"] > 0
        assert out["battery_runtime_minutes"] != float("inf")


class TestDecideDispatchBlackout:
    def test_forces_battery_when_soc_healthy(self):
        out = decide_dispatch(make_state(battery_soc_pct=80), grid_available=False)
        assert out["power_source"] == "battery"
        assert out["battery_action"] == "discharge"
        assert out["decision_reason"] == "blackout_battery_only"

    def test_never_runs_full_during_blackout(self):
        # Even with high workload + cheap price, blackout must not run "full".
        out = decide_dispatch(
            make_state(workload_state="high", electricity_price_usd_per_kwh=0.05),
            grid_available=False,
        )
        assert out["compute_mode"] != "full"

    def test_critical_only_below_critical_soc(self):
        out = decide_dispatch(
            make_state(battery_soc_pct=SOC_CRITICAL_PCT - 1),
            grid_available=False,
        )
        assert out["power_source"] == "battery"
        assert out["compute_mode"] == "critical_only"
        assert out["decision_reason"] == "blackout_low_soc_critical"

    def test_off_when_battery_depleted(self):
        out = decide_dispatch(
            make_state(battery_soc_pct=SOC_DEPLETED_PCT - 1),
            grid_available=False,
        )
        assert out["power_source"] == "off"
        assert out["compute_mode"] == "critical_only"
        assert out["decision_reason"] == "blackout_battery_depleted"

    def test_blackout_never_charges(self):
        # No matter the price/SoC combo, charging during a blackout is impossible.
        for soc in (10, 50, 90):
            for price in (0.05, 0.20, 0.40):
                out = decide_dispatch(
                    make_state(battery_soc_pct=soc, electricity_price_usd_per_kwh=price),
                    grid_available=False,
                )
                assert out["battery_action"] != "charge"
