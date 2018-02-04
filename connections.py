import svgwrite
import svgwrite.text
import svgpathtools
import numpy as np
import curves as ruv


def complex_as_point(p):
    return p[0] + 1j * p[1]


def find_path_between_points(p1, p2):
    # temp
    if ruv.distance(p1, p2) < 100:
        edist = 100 - ruv.distance(p1, p2)
        mid = np.array([
            (p1[0] + p1[1]) / 2,
            (p2[0] + p2[1]) / 2
        ])
        dir = p1[0] % 2 == 0
        vec = (p2 - p1) / ruv.distance(p1, p2)
        a = vec[0]
        b = vec[1]
        if dir:
            a = -a
        else:
            b = -b
        vec[0] = b
        vec[1] = a
        p0 = mid + (vec * edist)
        pth = svgpathtools.Path(svgpathtools.QuadraticBezier(complex_as_point(p1), complex_as_point(ruv.cp_for(p1, p0, p2)), complex_as_point(p2)))
    else:
        pth = svgpathtools.Path(svgpathtools.Line(complex_as_point(p1), complex_as_point(p2)))

    return pth.d()


def create_path_for_connection(connection, node_positions, curves, node_sizes):
    if connection[4]:
        crv = ruv.get_path_for_curve(curves[connection[0]])
        pth = svgpathtools.parse_path(crv)
        bbox = pth.bbox()
        centerA = np.array([
            (bbox[0] + bbox[1]) / 2,
            (bbox[2] + bbox[3]) / 2
        ])

        positionsA = []
        for i in np.arange(0, 1.05, 0.05):
            p = pth.point(i)
            positionsA.append(np.array([
                p.real,
                p.imag
            ]))
    else:
        centerA = node_positions[connection[0]]

        positionsA = [
            centerA + np.array([node_sizes[connection[0]], 0]),
            centerA + np.array([-node_sizes[connection[0]], 0]),
            centerA + np.array([0, node_sizes[connection[0]]]),
            centerA + np.array([0, -node_sizes[connection[0]]])
        ]
    if connection[5]:
        crv = ruv.get_path_for_curve(curves[connection[1]])
        pth = svgpathtools.parse_path(crv)
        bbox = pth.bbox()
        centerB = np.array([
            (bbox[0] + bbox[1]) / 2,
            (bbox[2] + bbox[3]) / 2
        ])

        positionsB = []
        for i in np.arange(0, 1.05, 0.05):
            p = pth.point(i)
            positionsB.append(np.array([
                p.real,
                p.imag
            ]))
        offset = 0
    else:
        centerB = node_positions[connection[1]]
        offset = node_sizes[connection[1]]

        positionsB = [
            centerB + np.array([node_sizes[connection[1]], 0]),
            centerB + np.array([-node_sizes[connection[1]], 0]),
            centerB + np.array([0, node_sizes[connection[1]]]),
            centerB + np.array([0, -node_sizes[connection[1]]])
        ]

    positionsA_prime = []
    for i in positionsA:
        if ruv.distance(centerB, i) < 50 + offset + 2:
            continue
        positionsA_prime.append(i)
    posA = min(positionsA_prime, key=lambda x: ruv.distance(centerB, x))
    posB = min(positionsB, key=lambda x: ruv.distance(posA, x))

    return find_path_between_points(posA, posB)


arrowhead = None


def create_arrowhead_marker(dwg):
    global arrowhead
    marker = dwg.marker(insert=(0.1, 1.5), size=(3, 3), orient="auto")
    triangle = dwg.polyline([
        (0, 0), (1.5, 1.5), (0, 3)
    ])

    triangle.fill("black")

    marker.add(triangle)
    dwg.defs.add(marker)
    arrowhead = marker


def add_path_to_drawing(connection, node_positions, node_sizes, curves, dwg):
    pth_string = create_path_for_connection(connection, node_positions, curves, node_sizes)
    pth_element = dwg.path(d=pth_string)
    pth_element.stroke("black", width=(connection[3] * 3) + 7, linecap="round")
    pth_element['marker-end'] = arrowhead.get_funciri()
    pth_element.fill("none")
    dwg.add(pth_element)
    width = ((connection[3] * 3) + 7) * (11/9)
    offset = width / 4

    text = svgwrite.text.Text("", font_family="Open Sans", font_size=width, dy=[offset], fill="gray")
    text_pth = svgwrite.text.TextPath(path=pth_element, text=connection[2], startOffset="5%")
    text.add(text_pth)
    dwg.add(text)
