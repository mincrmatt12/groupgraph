import numpy as np
from scipy.spatial import ConvexHull
import svgpathtools
import svgwrite


def cp_for(start, middle, end):
    t = 0.5
    return np.array([
        middle[0] / (2 * t * (1 - t)) - start[0] * t / (2 * (1 - t)) - end[0] * ((1 - t) / (2 * t)),
        middle[1] / (2 * t * (1 - t)) - start[1] * t / (2 * (1 - t)) - end[1] * ((1 - t) / (2 * t)),
    ])


def find_group_for_nodes(nodes, node_sizes):
    new_points = []
    for j, i in enumerate(nodes):
        new_points.append(i)
        new_points.append(i + np.array([node_sizes[j] + 20, 0]))
        new_points.append(i + np.array([-node_sizes[j] - 20, 0]))
        new_points.append(i + np.array([0, node_sizes[j] + 20]))
        new_points.append(i + np.array([0, -node_sizes[j] - 20]))

    valid_edges = ConvexHull(new_points)
    new_points = np.array(new_points)[valid_edges.vertices]
    new_points = np.append(new_points, [new_points[0]], axis=0)

    for i in range(1, len(new_points) - 1, 2):
        new_points[i] = cp_for(new_points[i - 1], new_points[i], new_points[i + 1])

    new_points = [x for x in new_points]

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


def point_inside_curve(c, p, s=0):
    crv = np.array(c)
    center = np.array([
        np.average(crv[:, 0]),
        np.average(crv[:, 1])
    ])
    new_crv = []
    for pt in crv:
        if s == 0:
            new_crv.append(pt)
        else:
            new_crv.append(explode(pt, center, (s / 2)))
    new_crv = np.array(new_crv)
    pth = svgpathtools.parse_path(get_path_for_curve(new_crv))
    bbox = pth.bbox()

    end = p[0] + 1j * bbox[3]
    p = p[0] + 1j * p[1]
    curve = svgpathtools.Path(svgpathtools.Line(p, end))

    intersection_count = len(curve.intersect(pth))

    return intersection_count % 2 == 1


def debug_save_as_svg(p, crves, positions, node_sizes):
    dwg = svgwrite.Drawing(p, size=("11in", "17in"))
    dwg.viewbox(width=1100, height=1700)

    for j, i in enumerate(positions):
        c = dwg.circle(center=(i[0], i[1]), r=int(node_sizes[j]))
        c.fill('blue')
        dwg.add(c)

    for crv in crves:
        pth = dwg.path(d=get_path_for_curve(crv))
        pth.fill('none').stroke('orange', width=5)
        dwg.add(pth)

    dwg.save(True)


if __name__ == "__main__":
    pts = (np.random.rand(50, 2) + 1) * np.array([800, 300])
    sizes = (np.random.rand(50) + 1) * 15
    crv = find_group_for_nodes(pts[:30], sizes[:30])
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
