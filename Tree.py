import Node

class Tree:
    def __init__(self, root):
        self.root = root
    def getRoot(self):
        return self.root
    def contains(self, node):
        return self.root.contains(node)
    def contains_ignore_version(self, node):
        return self.root.contains_ignore_version(node)
    def find(self, node):
        return self.root.find(node)
    def find_ignore_version(self, node):
        return self.root.find_ignore_version(node)
    def toString(self):
        return self.root.build_with_children()
