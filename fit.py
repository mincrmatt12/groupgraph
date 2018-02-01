import curves as ruv
import numpy as np
import copy

PAGE_SIZE_X = 1100
PAGE_SIZE_Y = 1100
EDGE_X = 400
EDGE_Y = 200

CRAMP = 100
CCRAMP = 150
AIR = 280
EQUIL = 45


def are_nodes_invalid(node_positions, minx, miny, maxx, maxy):
    for node in node_positions:
        if minx < node[0] < maxx and miny < node[1] < maxy: continue
        return True
    return False


def fit_to_groups(groups, nodes, node_sizes):
    # start with random arrangement of nodes

    node_positions = np.zeros((len(nodes), 2), dtype=np.float64)
    node_positions[:, 0] = np.random.uniform(EDGE_X, PAGE_SIZE_X, size=(len(nodes),))
    node_positions[:, 1] = np.random.uniform(EDGE_Y, PAGE_SIZE_Y, size=(len(nodes),))

    curve_shapes = generate_curves(node_positions, node_sizes, groups)

    iter = 1
    niceity = 0
    max_nice = 6

    last_good = None
    lgi = 0
    
    aci = are_curves_invalid(curve_shapes, node_positions, groups, node_sizes)

    while aci[0] or are_nodes_invalid(node_positions, 0, 0, PAGE_SIZE_X, PAGE_SIZE_Y) or aci[3]:
        if are_nodes_invalid(node_positions, 0, 0, PAGE_SIZE_X, PAGE_SIZE_Y):
            print("################ rerandom #####################")
            lgi = 0
            iter = 0
            node_positions[:, 0] = np.random.uniform(EDGE_X, PAGE_SIZE_X, size=(len(nodes),))
            node_positions[:, 1] = np.random.uniform(EDGE_Y, PAGE_SIZE_Y, size=(len(nodes),))
            curve_shapes = generate_curves(node_positions, node_sizes, groups)
            aci = are_curves_invalid(curve_shapes, node_positions, groups, node_sizes)
            continue
        if not aci[0] and are_curves_invalid(
                curve_shapes, node_positions, groups, node_sizes)[3]:
            niceity += 1
            print ("################################## niceity ###############################")
            last_good = [copy.deepcopy(curve_shapes), copy.deepcopy(node_positions)]
            lgi = iter
            if niceity > max_nice:
                #ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions)
                break
        else:
            if niceity > 0 and max_nice > 3:
                max_nice -= 1
            niceity = 0
            if last_good is not None and iter - lgi > 40:
                ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions, node_sizes)

                return last_good

        for nodenum in range(len(nodes)):
            for num in range(len(groups)):
                if nodenum in groups[num]:
                    center = center_of(groups[num], node_positions)
                    if not ruv.point_inside_curve(curve_shapes[num], node_positions[nodenum]):
                        abc = ruv.distance(node_positions[nodenum], center)
                        node_positions[nodenum] = ruv.explode(node_positions[nodenum], center, -(abc-10))

                    if ruv.distance(node_positions[nodenum], center) < CRAMP + 2:
                        node_positions[nodenum] = ruv.explode(node_positions[nodenum], center, 5)
                    if ruv.distance(node_positions[nodenum], center) < AIR: continue
                    d = ruv.distance(node_positions[nodenum], center)
                    d /= 4
                    if ruv.distance(node_positions[nodenum], center) < AIR / 1.8:
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
            for other in range(len(nodes)):
                if other == nodenum: continue
                if ruv.distance(node_positions[nodenum], node_positions[other]) < CCRAMP:
                    node_positions[other] = ruv.explode(node_positions[other], node_positions[nodenum], CCRAMP/3)
                    # explodes nodes to keep them away


        curve_shapes = generate_curves(node_positions, node_sizes, groups)
        #ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions)
        iter += 1
        if iter > 500:
            print("################ reset #####################")
            ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions, node_sizes)

            return curve_shapes, node_positions

        print("############ iter {}".format(iter))
        if iter % 2 == 0:
            print("#" + aci[4])
        aci = are_curves_invalid(curve_shapes, node_positions, groups, node_sizes)

    ruv.debug_save_as_svg(f"{iter}d.svg", curve_shapes, node_positions, node_sizes)

    return curve_shapes, node_positions


def are_curves_invalid(curves, node_positions, groups, node_sizes):
    is_invalid = False
    reshuffle = False
    niceness = False
    move = list(range(len(groups)))
    reasons = [set(), set(), set(), set(), set()]
    for num, curve in enumerate(curves):
        for a, b in zip(node_positions[groups[num]], groups[num]):
            if not ruv.point_inside_curve(curve, a, node_sizes[b]-0.5):
                is_invalid = True
                reasons[0] |= {b}
            if ruv.distance(a, center_of(groups[num], node_positions)) > AIR:
                reasons[1] |= {b}
                niceness = True
            elif ruv.distance(a, center_of(groups[num], node_positions)) < CRAMP:
                if len(groups[num]) > 3:
                    reasons[2] |= {b}
                    is_invalid = True
        for j in range(len(node_positions)):
            if j in groups[num]: continue
            if ruv.point_inside_curve(curve, node_positions[j], node_sizes[j]-0.5):
                reasons[4] |= {j}
                is_invalid = True
        move.remove(num)

    reasons = [len(x) for x in reasons]
    percent_validated = (((len(node_positions) * 5) - sum(reasons)) / (len(node_positions) * 5)) * 100
    return is_invalid, move, reshuffle, niceness, f"Percent {percent_validated:.2f}, {reasons[0]} outside curves, " \
                                                  f"{reasons[1]} too airy, {reasons[2]} too cramped," \
                                                  f" {reasons[4]} in wrong clouds "


def check_equil(pos, center):
    a = pos - center
    b = abs(a[0] - a[1])
    return b > EQUIL


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
    nodes = ("George", "Lennie", "Crooks", "Wife", "Curley", "Carlson", "Candy", "Slim")
    if False:
        groups = []
        c =np.random.randint(1, 9)
        print("c", c)
        for i in range(c):
            r = np.arange(start=0, stop=len(nodes))
            print ("r", r)
            np.random.shuffle(r)
            group = r[:np.random.randint(1, 7)]
            groups.append(group)
        groups = np.array(groups)
        print(groups)
        nodes = np.array(nodes)
        for i in groups:
            print(nodes[i], i)
    groups = np.array([[0, 1, 4, 5, 6, 7], [2], [3], [0, 1], [4, 5, 7]])
    node_sizes = np.random.randint(10, 20, len(nodes))
    print(fit_to_groups(groups, nodes, node_sizes))
