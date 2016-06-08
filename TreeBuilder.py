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

        error_level = False
        error_parent = None

        pattern = re.compile("(?<=\\()(.+?)(?=\\))")
        for raw_node in node_list:
            temp = re.findall(pattern, raw_node)
            if len(temp) > 0: # This is an omitted node
                omitted_node_data = temp[0].split(" - ")[0]
                child = Node(omitted_node_data, True)
                if self.tree.contains(child, True):
                    found_node = self.tree.find(child)
                    if found_node == None:
                        print (raw_node)
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
            if level == parent.get_level() + 2 and not error_level:
                error_level = True
                error_parent = parent
            elif error_level and error_parent.get_level() >= level:
                error_level = False

            if error_level:
                level = level - 1

            while(parent.get_level() >= level):
                parent = parent.get_parent()

            parent.add_child(child)
            parent = child

        return self.tree


def main():

    dataFile = "/home/mi/boss-operations/oldDependencyTree.txt"
    tree = TreeBuilder(dataFile).build()

    raw_node_text = "javax.servlet.jsp:jsp-api:jar:2.1:compile"
    node = Node(raw_node_text)
    print (tree.contains(node, True))
    print (tree.contains_ignore_version(node))

    found_node = tree.find_ignore_version(node)
    print (found_node.data)
    print (found_node.omitted)


    dataFile1 = "/home/mi/boss-operations/DependencyTree.txt"
    tree1 = TreeBuilder(dataFile).build()

    raw_node_text1 = "javax.servlet.jsp:jsp-api:jar:2.1:compile"
    found_node1 = tree1.find(Node(raw_node_text1))
    print (tree1.contains(found_node1, True))
    print (found_node1.data)
    print (found_node1.omitted)


if __name__ == '__main__':
    main()

