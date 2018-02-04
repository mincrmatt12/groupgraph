import curves
import fit
import numpy as np
import svgwrite
import legend

print("[Powermap] Page size is 11in x 17in")


class Powermap:
    def __init__(self, people, groups, connections, outname="powermap.svg"):
        self.people = {x: i for i, x in enumerate(people)}
        self.connections = connections  # (pAi pBi action intensity groupA groupB)
        self.node_sizes = [0] * len(people)
        self.groups = groups
        self.group_num = {x: i for i, x in enumerate(self.groups.keys())}
        self.reverse_group_num = {self.group_num[x]: x for x in self.group_num}
        self.node_positions = []
        self.curves = {}
        self.paths = []
        self.dwg = svgwrite.Drawing(outname, size=("11in", "17in"))
        self.dwg.viewbox(width=1100, height=1700)
        self.legend = {}

    def compute_sizes(self):
        print("[Powermap] Computing sizes")
        rank = {x: 0 for x in self.people}
        for connection in self.connections:
            if connection[4]:
                for person in self.groups[connection[0]]:
                    rank[person] += 1
            else:
                rank[connection[0]] += 1
        for i in self.people:
            self.node_sizes[self.people[i]] = (rank[i] * 2.5) + 50

    def compute_groups(self):
        self.compute_sizes()
        print("[Powermap] Computing groups")
        groups = [None] * len(self.groups)
        node_sizes = np.array(self.node_sizes)
        nodes = np.array(list(self.people.keys()))
        for group in self.groups:
            groups[self.group_num[group]] = self.groups[group]
        groups = np.array(groups)
        curves, self.node_positions = fit.fit_to_groups(groups, nodes, node_sizes)
        for j, i in enumerate(curves):
            self.curves[self.reverse_group_num[j]] = i

    def create_legends(self):
        used_legendspecs = []
        print("[Powermap] Creating legends")
        for group in self.groups.keys():
            if group.startswith("anon"):
                continue
            self.legend[group] = legend.generate_legendspec(group, used_legendspecs)

    def create_paths_for_curves(self):
        self.compute_groups()
        self.create_legends()
        print("[Powermap] Creating paths")
        for group in self.groups:
            legendspec = legend.anon
            if group in self.legend:
                legendspec = self.legend[group]
            legend.create_path(legendspec, curves.get_path_for_curve(self.curves[group]), self.dwg)

    def create_circles(self):
        print("[Powermap] Drawing circles")
        for j, pt in enumerate(self.people):
            siz = self.node_sizes[j]
            pos = self.node_positions[j] - np.array([siz] * 2)
            pt_g = self.dwg.g(transform=f"translate({pos[0]}, {pos[1]})")
            circle = self.dwg.circle(center=[siz, siz], r=siz, fill="rgb(0, 191, 255)")
            pt_g.add(circle)
            text = self.dwg.text(pt, [siz, siz], font_size=siz/2, font_family="Open Sans", text_anchor="middle")
            pt_g.add(text)
            self.dwg.add(pt_g)

    def draw_map(self):
        self.create_paths_for_curves()
        self.create_circles()

    def draw(self):
        self.draw_map()
        #self.draw_legend()

    def save(self):
        self.dwg.save()


if __name__ == "__main__":
    pmap = Powermap(
        ["Lennie", "George", "Curley", "Carlson", "Slim", "Candy", "Curley's Wife", "Crooks"],
        {
            "White&Male": [0, 1, 2, 3, 4, 5],
            "anon_dog": [2, 3, 4],
            "anon_lennie": [1, 2, 3, 4, 5],
            "anon_seperate": [0, 1, 2, 3, 4, 5, 6],
            "Female": [6],
            "Black": [7]
        },
        []
    )
    pmap.draw()
    pmap.save()
