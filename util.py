from math import log10 , floor

def round_it(x, sig):
    return round(x, sig-int(floor(log10(abs(x))))-1)

def remove_point1(x):
    """ Cuts off a trailing .0 from a string """
    if x.endswith(".0"):
        return x[:len(x) - 2]
    else:
        return x

def fmt_si(r):
    # Round to three significant digits first 
    rr = round_it(r, 3)
    # Figure out the scale of the rounded number
    places = log10(rr)
    if places < -12.0:
        return str(rr)
    elif places < -9.0:
        return remove_point1(str(round_it(rr * 1e12, 3))) + "p" 
    elif places < -6.0:
        return remove_point1(str(round_it(rr * 1e9, 3))) + "n" 
    elif places < -3.0:
        return remove_point1(str(round_it(rr * 1e6, 3))) + "u" 
    elif places < 0.0:
        return remove_point1(str(round_it(rr * 1e3, 3))) + "m" 
    else:
        return remove_point1(str(round_it(rr, 3)))
