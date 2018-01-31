class Powermap:
    def __init__(self):
        self.people = []
        self.connections = []  # (pAi pBi action intensity)
        self.groups = {}

    def compute_legend(self):
        pass