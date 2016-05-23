import Node

class Tree:
    def __init__(self, root):
        self.root = root
    def getRoot(self):
        return self.root
    def contains(self, node, ignore_omitted = True):
        return self.root.contains(node, ignore_omitted)
    def contains_ignore_version(self, node):
        return self.root.contains_ignore_version(node)
    def find(self, node):
        return self.root.find(node)
    def find_ignore_version(self, node):
        return self.root.find_ignore_version(node)
    def find_contain_omitted(self, node):
        nodes_list = []
        self.root.find_contain_omitted(node, nodes_list)
        return nodes_list
    def toString(self):
        return self.root.build_with_children()
