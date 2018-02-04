import svgwrite

colors = [
    "orange",
    "rgb(100,149,237)",
    "green",
    "black",
    "greenyellow",
    "darkblue",
    "orangered"
]

dashes = [
    [20, 20],
    [10, 10],
    [20, 10, 20, 10],
    [30, 30, 10, 10]
]

anon = ["gray", False, None]


# legendspec: base_color, has_dash, dashes
# dashes: dashspec, dash_color

def generate_legendspec(name, existing_legendspecs, offset=0):
    h = hash(name) + offset
    base_color = colors[h % len(colors)]
    content = [base_color, None, None]
    if h % 3 == 0:
        hashcolor = (colors + ["white"])[h % (len(colors)+1)]
        dash = dashes[h % len(dashes)]
        content[1] = True
        content[2] = [dash, hashcolor]
    else:
        content[1] = False
    if content in existing_legendspecs:
        return generate_legendspec(name, existing_legendspecs, offset+1)
    existing_legendspecs.append(content)
    print(f"[Legend] Creating legend with color {content[0]}")
    if content[1]:
        print(f"[Legend] Dashes are color {content[2][1]} in pattern {content[2][0]}.")
    return content


def create_path(legendspec, curve, dwg: svgwrite.Drawing, s):
    path_base = dwg.path(d=curve)
    path_base.fill("none").stroke(legendspec[0], width=6 if not s else 3)
    paths = [path_base]
    if legendspec[1]:
        path_dashes = dwg.path(d=curve)
        path_dashes.fill("none").stroke(legendspec[2][1], width=6 if not s else 3)
        path_dashes.dasharray(legendspec[2][0])
        paths.append(path_dashes)
    for i in paths:
        dwg.add(i)
    return paths
