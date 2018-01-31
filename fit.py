import curves as ruv
import numpy as np

PAGE_SIZE_X = 1100
PAGE_SIZE_Y = 1700


def are_nodes_invalid(node_positions, minx, miny, maxx, maxy):
    for node in node_positions:
        if minx < node[0] < maxx and miny < node[1] < maxy: continue
        return True
    return False


def fit_to_groups(groups, nodes, node_sizes):
    # start with random arrangement of nodes

    node_positions = np.zeros((len(nodes), 2), dtype=np.float64)
    node_positions[:, 0] = np.random.uniform(500, 1100, size=(len(nodes),))
    node_positions[:, 1] = np.random.uniform(500, 1700, size=(len(nodes),))

    curve_shapes = generate_curves(node_positions, node_sizes, groups)

    iter = 1
    niceity = 0
    max_nice = 6

    while are_curves_invalid(curve_shapes, node_positions, groups)[0] or are_nodes_invalid(node_positions, 0, 0, 1100,
                                                                                           1700) or are_curves_invalid(curve_shapes, node_positions, groups)[3]:
        if are_curves_invalid(curve_shapes, node_positions, groups)[2] or are_nodes_invalid(node_positions, 0, 0, 1100,
                                                                                           1700):
            node_positions[:, 0] = np.random.uniform(0, 1100, size=(len(nodes),))
            node_positions[:, 1] = np.random.uniform(0, 1700, size=(len(nodes),))
            curve_shapes = generate_curves(node_positions, node_sizes, groups)
            continue
        if not are_curves_invalid(curve_shapes, node_positions, groups)[0] and are_curves_invalid(curve_shapes, node_positions, groups)[3]:
            niceity += 1
            print ("################################## niceity ###############################")
            if niceity > max_nice:
                #ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions)
                break
        else:
            if niceity > 0 and max_nice > 3:
                max_nice -= 1
            niceity = 0
        for nodenum in range(len(nodes)):
            for num in range(len(groups)):
                if nodenum in groups[num]:
                    center = center_of(groups[num], node_positions)

                    if ruv.distance(node_positions[nodenum], center) < 85:
                        node_positions[nodenum] = ruv.explode(node_positions[nodenum], center, 5)
                    if ruv.distance(node_positions[nodenum], center) < 100: continue
                    d = ruv.distance(node_positions[nodenum], center)
                    d /= 4

                    node_positions[nodenum] = ruv.explode(node_positions[nodenum], center, -d)
                if ruv.point_inside_curve(curve_shapes[num], node_positions[nodenum]):
                    bbox = ruv.get_curve_bbox(curve_shapes[num])
                    s = (max(bbox[1] - bbox[0], bbox[3] - bbox[2]) / 2) * np.sqrt(2)
                    s += node_sizes[nodenum] + 1
                    s /= 15

                    center = np.array([
                        (bbox[0] + bbox[1]) / 2,
                        (bbox[2] + bbox[3]) / 2,
                    ])

                    node_positions[nodenum] = ruv.explode(node_positions[nodenum], center, s)

        curve_shapes = generate_curves(node_positions, node_sizes, groups)
        #ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions)
        iter += 1
        if iter > 200 and niceity == 0:
            print("################ reset #####################")
            node_positions[:, 0] = np.random.uniform(0, 1100, size=(len(nodes),))
            node_positions[:, 1] = np.random.uniform(0, 1700, size=(len(nodes),))
            curve_shapes = generate_curves(node_positions, node_sizes, groups)
            iter = 0

        if iter % 10 == 0:
            print("############ iter {}".format(iter))

    ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions)

    return curve_shapes


def are_curves_invalid(curves, node_positions, groups):
    is_invalid = False
    reshuffle = False
    niceness = False
    move = list(range(len(groups)))
    for num, curve in enumerate(curves):
        for a in node_positions[groups[num]]:
            if not ruv.point_inside_curve(curve, a):
                is_invalid = True
                reshuffle = True
            if ruv.distance(a, center_of(groups[num], node_positions)) > 220:
                niceness = True
            elif ruv.distance(a, center_of(groups[num], node_positions)) < 80:
                if len(groups[num]) > 3:
                    is_invalid = True
            if check_equil(a, center_of(groups[num], node_positions)):
                niceness = True
        for j in range(len(node_positions)):
            if j in groups[num]: continue
            if ruv.point_inside_curve(curve, node_positions[j]):
                is_invalid = True
        move.remove(num)
    return is_invalid, move, reshuffle, niceness


def check_equil(pos, center):
    a = pos - center
    b = abs(a[0] - a[1])
    return b > 40


def center_of(group, node_positions):
    arr = node_positions[group]
    return np.array([
        np.average(arr[:, 0]),
        np.average(arr[:, 1])
    ])


def generate_curves(node_positions, node_sizes, groups):
    curves = []
    for group in groups:
        pos, siz = node_positions[group], node_sizes[group]
        curves.append(ruv.find_group_for_nodes(pos, siz))
    return curves


if __name__ == "__main__":
    nodes = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L")
    groups = np.array([[1, 2, 3, 4, 5], [0, 2, 3, 4], [1, 4, 5, 8], [2, 10], [2], [1, 5, 7]])
    node_sizes = np.repeat(15, len(nodes))
    print(fit_to_groups(groups, nodes, node_sizes))
