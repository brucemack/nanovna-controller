"""
Sweep analysis: local VSWR minima/maxima and frequency ranges where the
VSWR stays at or below a given threshold.

All detection works on the reflection coefficient magnitude |Γ| rather than
on VSWR.  VSWR is a monotonic function of |Γ| so minima, maxima and threshold
crossings are identical, but |Γ| stays finite (VSWR explodes as |Γ| -> 1 and
measurement noise can even push |Γ| slightly above 1).
"""
import math
import re
from calcs import interp_g

# Minimum change in |Γ| that the curve must reverse by before a turning point
# is accepted as a local minimum/maximum.  This suppresses measurement noise.
# Near a good match 0.01 in |Γ| is roughly 0.02 in VSWR.
EXTREMA_MIN_GAMMA_CHANGE = 0.01


def vswr_to_gamma(vswr):
    return (vswr - 1.0) / (vswr + 1.0)


def gamma_to_vswr(gamma):
    if gamma >= 1.0:
        return math.inf
    return (1.0 + gamma) / (1.0 - gamma)


def parse_vswr_thresholds(text):
    """
    Parses a comma and/or space separated list of VSWR thresholds.
    Returns a sorted list of unique values; an empty input gives an empty list.
    """
    if text is None or text.strip() == "":
        return []
    thresholds = set()
    for token in re.split(r"[,;\s]+", text.strip()):
        if token == "":
            continue
        try:
            value = float(token)
        except ValueError:
            raise Exception("Invalid VSWR threshold: " + token)
        if not math.isfinite(value) or value <= 1.0:
            raise Exception("Invalid VSWR threshold: " + token + " (must be greater than 1)")
        thresholds.add(value)
    return sorted(thresholds)


def find_local_extrema(gammas, min_change=EXTREMA_MIN_GAMMA_CHANGE):
    """
    Finds local minima and maxima using hysteresis: a candidate is confirmed
    only after the curve has moved back from it by more than min_change.
    Turning points on the first or last sample are not reported.

    :return: A list of (index, "minimum" | "maximum") tuples in frequency order.
    """
    n = len(gammas)
    if n < 3:
        return []
    extrema = []
    min_i = max_i = 0
    # None until the initial direction is known, then the kind of turning
    # point we are currently waiting for
    seeking = None
    for i in range(1, n):
        g = gammas[i]
        if g > gammas[max_i]:
            max_i = i
        if g < gammas[min_i]:
            min_i = i
        if seeking != "minimum" and g < gammas[max_i] - min_change:
            extrema.append((max_i, "maximum"))
            seeking = "minimum"
            # All samples since max_i are above g, so the minimum candidate starts here
            min_i = i
        elif seeking != "maximum" and g > gammas[min_i] + min_change:
            extrema.append((min_i, "minimum"))
            seeking = "maximum"
            max_i = i
    return [(i, kind) for (i, kind) in extrema if 0 < i < n - 1]


def find_ranges_below(frequencies, gammas, gamma_threshold):
    """
    Finds the frequency ranges where |Γ| <= gamma_threshold.  Range edges
    between two samples are linearly interpolated.

    :return: A list of dicts with start_hz, end_hz, min_index, open_start
        and open_end.  open_start/open_end mean the range touches the sweep
        edge and may continue beyond it.
    """
    if len(frequencies) != len(gammas):
        raise Exception("Length error")
    ranges = []
    current = None
    for i, g in enumerate(gammas):
        if g <= gamma_threshold:
            if current is None:
                if i == 0:
                    start = frequencies[0]
                else:
                    start = interp_g(gammas[i - 1], g, frequencies[i - 1], frequencies[i], gamma_threshold)
                current = {"start_hz": start, "min_index": i, "open_start": i == 0}
            elif g < gammas[current["min_index"]]:
                current["min_index"] = i
        elif current is not None:
            current["end_hz"] = interp_g(gammas[i - 1], g, frequencies[i - 1], frequencies[i], gamma_threshold)
            current["open_end"] = False
            ranges.append(current)
            current = None
    if current is not None:
        current["end_hz"] = frequencies[-1]
        current["open_end"] = True
        ranges.append(current)
    return ranges


def _fmt_mhz(frequency_hz):
    return "{:.03f}".format(frequency_hz / 1000000.0)


def _fmt_vswr(gamma):
    vswr = gamma_to_vswr(gamma)
    if math.isinf(vswr):
        return "∞"
    return "{:.02f}".format(vswr)


def analyze_sweep(frequencies, gammas, thresholds):
    """
    Builds the formatted (JSON-ready) analysis of a full-resolution sweep.

    :param frequencies: Measured frequencies in Hz
    :param gammas: Reflection coefficient magnitudes |Γ| at those frequencies
    :param thresholds: VSWR thresholds for the range analysis
    """
    if len(frequencies) != len(gammas):
        raise Exception("Length error")
    extrema = [
        {
            "kind": kind,
            "frequency_mhz": _fmt_mhz(frequencies[i]),
            "vswr": _fmt_vswr(gammas[i])
        }
        for (i, kind) in find_local_extrema(gammas)
    ]
    bands = []
    for threshold in thresholds:
        ranges = [
            {
                "start_mhz": _fmt_mhz(r["start_hz"]),
                "end_mhz": _fmt_mhz(r["end_hz"]),
                "min_vswr": _fmt_vswr(gammas[r["min_index"]]),
                "min_frequency_mhz": _fmt_mhz(frequencies[r["min_index"]]),
                "open_start": r["open_start"],
                "open_end": r["open_end"]
            }
            for r in find_ranges_below(frequencies, gammas, vswr_to_gamma(threshold))
        ]
        bands.append({"threshold": "{:.02f}".format(threshold), "ranges": ranges})
    return {
        "point_count": len(frequencies),
        "extrema": extrema,
        "bands": bands
    }
