
def interp_g(ax, bx, ay, by, target_x):
    span = bx - ax
    if span == 0:
        return ay
    s = (target_x - ax) / span
    return ay + (by - ay) * s


def interp_f(x_list, x_target):
    last_index = len(x_list) - 1
    # Check to see if we are before the first x
    if x_target <= x_list[0]:
        return 0, 0
    elif x_target >= x_list[last_index]:
        return last_index, last_index
    # Scan
    for i in range(len(x_list) - 1):
        if x_target == x_list[i]:
            return i, i
        elif (x_target > x_list[i]) and (x_target < x_list[i + 1]):
            return i, i + 1
    return last_index, last_index


def interp(x_list, y_list, x_target):
    if len(x_list) != len(y_list):
        raise Exception("Length error")
    x_points = interp_f(x_list, x_target)
    return interp_g(x_list[x_points[0]], x_list[x_points[1]], y_list[x_points[0]], y_list[x_points[1]], x_target)


