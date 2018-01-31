import numpy as np
from scipy.spatial import ConvexHull
import svgpathtools
import bezier


def cp_for(start, middle, end):
    t = 0.5
    return np.array([
        middle[0] / (2 * t * (1 - t)) - start[0] * t / (2 * (1 - t)) - end[0] * ((1 - t) / (2 * t)),
        middle[1] / (2 * t * (1 - t)) - start[1] * t / (2 * (1 - t)) - end[1] * ((1 - t) / (2 * t)),
    ])


def find_group_for_nodes(nodes, node_sizes):
    nodes = nodes[:]
    if len(nodes) == 1:
        node_sizes = np.tile(node_sizes, 4)
        nodes_ = [[nodes[0][0] - node_sizes[0]*4, nodes[0][1]], [nodes[0][0] + node_sizes[0]*4, nodes[0][1]],
                  [nodes[0][0], nodes[0][1]] + node_sizes[0]*4, [nodes[0][0], nodes[0][1] - node_sizes[0]*4]]
        nodes = nodes_

    elif len(nodes) == 2:
        arr = np.array(nodes)
        node_sizes = np.tile(node_sizes, 2)
        center = np.array([
            np.average(arr[:, 0]),
            np.average(arr[:, 1])
        ])
        nodes_ = [nodes[0], nodes[1], [
            center[0] + 25, center[1] + 25
        ], [
            center[0] - 25, center[1] - 25
        ]]
        nodes = nodes_

    arr = np.array(nodes)
    center = np.array([
        np.average(arr[:, 0]),
        np.average(arr[:, 1])
    ])

    new_points = [explode(x, center, node_sizes[i] * 4) for i, x in enumerate(nodes)]

    valid_edges = ConvexHull(new_points)
    new_points = np.array(new_points)[valid_edges.vertices]

    for i in range(1, len(new_points) - 1, 2):
        new_points[i] = cp_for(new_points[i - 1], new_points[i], new_points[i + 1])

    new_points = [x for x in new_points]
    new_points.append(new_points[0])

    return new_points


def distance(node, center):
    x = node[0] - center[0]
    y = node[1] - center[1]

    return np.sqrt(x ** 2 + y ** 2)


def explode(node, center, amt):
    x = node[0] - center[0]
    y = node[1] - center[1]

    if not abs(x) < 1:
        x /= np.sqrt(x ** 2 + y ** 2)

    if not abs(y) < 1:
        y /= np.sqrt(x ** 2 + y ** 2)

    x *= amt
    y *= amt
    return node + np.array([x, y])


def get_path_for_curve(c):
    s = f"M {c[0][0]} {c[0][1]} "
    for i in range(1, len(c) - 1, 2):
        fs = f"Q {c[i][0]} {c[i][1]} {c[i+1][0]} {c[i+1][1]} "
        s += fs
    s += "Z"
    return s


def get_angled_path_for_curve(c):
    s = f"M {c[0][0]} {c[0][1]} "
    for i in range(1, len(c) - 1, 2):
        fs = f"L {c[i+1][0]} {c[i+1][1]} "
        s += fs
    return s[:-1]


def get_curve_bbox(c):
    return svgpathtools.parse_path(get_path_for_curve(c)).bbox()


def point_inside_curve(c, p):
    bbox = get_curve_bbox(c)
    curve_ = bezier.Curve(np.asfortranarray([
        [p[0], p[1]],
        [p[0], bbox[3] + 10]
    ]), degree=1)
    curves = []
    for i in range(0, len(c) - 1, 2):
        try:
            curves.append(bezier.Curve(np.asfortranarray([
                c[i],
                c[i + 1],
                c[i + 2]
            ]), degree=2))
        except IndexError:
            curves.append(bezier.Curve(np.asfortranarray([
                c[i],
                c[i + 1],
                c[0]
            ]), degree=2))

    intersection_count = 0
    for i in curves:
        intersection_count += len(i.intersect(curve_))

    return intersection_count % 2 == 1


import svgwrite


def debug_save_as_svg(p, crves, positions):
    dwg = svgwrite.Drawing(p, size=("1200px", "1800px"))
    dwg.viewbox(width=1200, height=1800)

    for crv in crves:
        pth = dwg.path(d=get_path_for_curve(crv))
        pth.fill('none').stroke('orange', width=5)
        dwg.add(pth)

    for i in positions:
        c = dwg.circle(center=(i[0], i[1]), r=15)
        c.fill('blue')
        dwg.add(c)

    dwg.save(True)


if __name__ == "__main__":
    pts = (np.random.rand(30, 2) + 1) * np.array([800, 300])
    sizes = (np.random.rand(30) + 1) * 15
    crv = find_group_for_nodes(pts, sizes)
    dwg = svgwrite.Drawing("a.svg", size=("1800px", "900px"))
    dwg.viewbox(width=1800, height=900)

    pth = dwg.path(d=get_path_for_curve(crv))
    pth.fill('none').stroke('orange', width=5)
    dwg.add(pth)

    center = np.array([
        np.average(pts[:, 0]),
        np.average(pts[:, 1])
    ])

    c = dwg.circle(center=(center[0], center[1]), r=2)
    c.fill('green')
    dwg.add(c)

    for i, j in zip(pts, sizes):
        c = dwg.circle(center=(i[0], i[1]), r=j)
        c.fill('blue' if point_inside_curve(crv, np.array(i)) else 'red')
        dwg.add(c)

    dwg.save(True)
