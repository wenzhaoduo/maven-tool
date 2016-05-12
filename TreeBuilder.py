from Tree import Tree
from Node import Node
from TreeParser import TreeParser
import re

class TreeBuilder:
    def __init__(self, data):
        self.data = data
        self.root = Node("")
        self.tree = Tree(self.root)
        self.omitted_dict = {}

    def compute_level(self, raw_node):
        space_count = 0
        for c in raw_node:
            if(c == ' '):
                space_count = space_count +1
            elif(c == '+' or c == '\\'):
                break

        if (space_count % 2 == 0):
            level = (int)(1 + space_count / 2)
        else:
            level = int(1 + (space_count - 1) / 2)

        return level

    def build(self):
        tree_parser = TreeParser(self.data)
        node_list = tree_parser.parse()

        self.root = Node(tree_parser.root_name)
        self.tree = Tree(self.root)

        parent = self.root

        pattern = re.compile("(?<=\\()(.+?)(?=\\))")

        for raw_node in node_list:
            level = self.compute_level(raw_node)

            temp = re.findall(pattern, raw_node)
            if len(temp) > 0: # This is an omitted node
                omitted_node_data = temp[0].split(" - ")[0]
                omitted_node = Node(omitted_node_data)
                if self.tree.contains(omitted_node):
                    child = self.tree.find(omitted_node)
                    child.times = child.times + 1
                elif omitted_node_data in self.omitted_dict:
                    self.omitted_dict[omitted_node_data] = self.omitted_dict[omitted_node_data] + 1
                else:
                    self.omitted_dict[omitted_node_data] = 1
                continue

            child = Node(raw_node.split("- ")[1])

            if child.data in self.omitted_dict:
                child.times = self.omitted_dict[child.data] + 1

            while(parent.get_level() >= level):
                parent = parent.get_parent()

            parent.add_child(child)
            parent = child

        return self.tree

def main():
    # read from dependencies.txt file
    # parse file into Tree
    # run some find and contains
    # run some print path on nodes

    dataFile = "oldDependencyTree.txt"
    tree = TreeBuilder(dataFile).build()

    print(tree.toString())

    raw_node_text = "javax.mail:mail:jar:1.5:compile"
    print (tree.contains_ignore_version(Node(raw_node_text)))
    # found_node = tree.find(Node(raw_node_text))
    # print (found_node.times)

    # print(found_node.toString(False))
    # print(found_node.build_with_children())
    # print(found_node.build_with_ancestors(False))

if __name__ == '__main__':
    main()

