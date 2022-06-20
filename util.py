from math import log10 , floor

def round_it(x, sig):
    return round(x, sig-int(floor(log10(abs(x))))-1)

def remove_point1(x):
    """ Cuts off a trailing .0 from a string """
    if x.endswith(".0"):
        return x[:len(x) - 2]
    else:
        return x

def fmt_si(r, suffix):
    # Round to three significant digits first 
    rr = round_it(r, 3)
    if rr < 0:
        return ""
    # Figure out the scale of the rounded number
    places = log10(rr)
    if places < -12.0:
        return str(rr) + " " + suffix
    elif places < -9.0:
        return remove_point1(str(round_it(rr * 1e12, 3))) + "p" + suffix
    elif places < -6.0:
        return remove_point1(str(round_it(rr * 1e9, 3))) + " n" + suffix 
    elif places < -3.0:
        return remove_point1(str(round_it(rr * 1e6, 3))) + " u" + suffix 
    elif places < 0.0:
        return remove_point1(str(round_it(rr * 1e3, 3))) + " m" + suffix 
    else:
        return remove_point1(str(round_it(rr, 3))) + " " + suffix
