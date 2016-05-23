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
            temp = re.findall(pattern, raw_node)
            if len(temp) > 0: # This is an omitted node
                omitted_node_data = temp[0].split(" - ")[0]
                child = Node(omitted_node_data, omitted = True)
                if self.tree.contains(child, ignore_omitted = False):
                    found_node = self.tree.find(child)
                    found_node.times = found_node.times + 1
                elif omitted_node_data in self.omitted_dict:
                    self.omitted_dict[omitted_node_data] = self.omitted_dict[omitted_node_data] + 1
                else:
                    self.omitted_dict[omitted_node_data] = 1
                # continue
            else: #This is not an omitted node
                child = Node(raw_node.split("- ")[1])
                if child.data in self.omitted_dict:
                    child.times = self.omitted_dict[child.data] + 1

            level = self.compute_level(raw_node)
            while(parent.get_level() >= level):
                parent = parent.get_parent()

            parent.add_child(child)
            parent = child

        return self.tree


#TODO: print build with ancestors with -->
def main():
    # read from dependencies.txt file
    # parse file into Tree
    # run some find and contains
    # run some print path on nodes

    dataFile = "dependencyTree.txt"
    tree = TreeBuilder(dataFile).build()

    # print(tree.toString())

    raw_node_text = "com.xiaomi.telecom.boss:boss-common:jar:1.0.0-SNAPSHOT:compile"
    # print (tree.find(Node(raw_node_text)))
    found_node = tree.find_contain_omitted(Node(raw_node_text))

    for node in found_node:
        print (node.build_with_ancestors())
    # print (found_node.times)

    # print(found_node.toString(False))
    # print(found_node.build_with_children())
    # print(found_node.build_with_ancestors(False))

if __name__ == '__main__':
    main()

