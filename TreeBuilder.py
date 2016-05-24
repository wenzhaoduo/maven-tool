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


#TODO: print build with ancestors with -->
def main():

    dataFile = "/home/mi/boss-operations/dependencyTree.txt"
    tree = TreeBuilder(dataFile).build()

    # print(tree.toString())
    for i in range (0, len(tree.root.children)):
        print (i)

    # raw_node_text = "|  |  |        +- org.apache.avro:avro:jar:1.5.3:compile"
    # raw_node_text = "|  |        +- com.xiaomi.mfs.common:mfs-common:jar:1.2.6:compile"
    # print (TreeBuilder(dataFile).compute_level(raw_node_text))
    # print (tree.find(Node(raw_node_text)))
    # found_node = tree.find_contain_omitted(Node(raw_node_text))

    # for node in found_node:
    #     print (node.build_with_ancestors())
    # print (found_node.times)

    # print(found_node.toString(False))
    # print(found_node.build_with_children())
    # print(found_node.build_with_ancestors(False))

if __name__ == '__main__':
    main()

