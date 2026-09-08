"""An IoT morning: pulses, gaps, skew, and the source that keeps its word.

Run with: python -m examples.iotmorning
"""

from __future__ import annotations

from rill.gapfill import GapFiller
from rill.heartbeat import HeartbeatMonitor
from rill.punctuate import PunctuatedSource
from rill.skewmeter import SkewMeter


def six_am_the_roll_call():
    monitor = HeartbeatMonitor(pulse_interval=10)
    monitor.event("thermostat", now=100)
    monitor.pulse("door-sensor", now=98)
    monitor.pulse("basement-cam", now=60)
    print(f"06:00  {monitor.read('door-sensor', now=105)}")
    print(f"       {monitor.roll(now=105)}")


def seven_am_the_gap():
    filler = GapFiller(window_size=10, policy="render-gap")
    observed = {0: 21, 10: 19, 30: 22}
    series = filler.fill(observed, 0, 30)
    print(f"07:00  {series[2]}")
    print(f"       {filler.outage_check(observed, expected_windows=10)}")


def eight_am_the_skew():
    meter = SkewMeter()
    for number in range(50):
        meter.observe(
            event_time=100 + number,
            arrival=102 + number + (4 if number % 10 == 0 else 0),
        )
    print(f"08:00  {meter.what_if_table([2, 6]).splitlines()[1].strip()}")
    print(f"       {meter.what_if_table([2, 6]).splitlines()[2].strip()}")


def nine_am_the_kept_word():
    source = PunctuatedSource(name="factory-gateway")
    source.punctuate(through=200)
    source.event(250)
    source.event(190)
    print(f"09:00  {source.trust_ledger()}")


def main() -> int:
    six_am_the_roll_call()
    seven_am_the_gap()
    eight_am_the_skew()
    nine_am_the_kept_word()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
