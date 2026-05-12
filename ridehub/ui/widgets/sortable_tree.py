class SortableTree:
    def __init__(self, tree):
        self.tree = tree
        self.sort_state = {}

    def attach(self):
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort(c))

    def sort(self, col):
        rows = [(self.tree.set(item, col), item) for item in self.tree.get_children("")]
        reverse = not self.sort_state.get(col, False)
        self.sort_state[col] = reverse

        def key(row):
            value = str(row[0]).replace("%", "").replace("km", "").replace(",", "").strip()
            try:
                return float(value)
            except ValueError:
                return value.lower()

        rows.sort(key=key, reverse=reverse)
        for index, (_, item) in enumerate(rows):
            self.tree.move(item, "", index)
