######### CLASS NODE  ######### 

class Node:
    def __init__(self, data, omitted = False):
        self.parent = None
        self.level = 0
        self.times = 1
        self.omitted = omitted #whether this node is omitted
        self.data = data
        self.children = []
        self.groupId = ""
        self.artifactId = ""

        if data != "":
            data_spilt = data.split(":")
            self.groupId = data_spilt[0]
            self.artifactId = data_spilt[1]

    def get_data(self):
        return self.data
    def get_children(self):
        return self.children
    def get_level(self):
        return self.level
    def get_parent(self):
        return self.parent
    def get_times(self):
        return self.times

    def add_child(self, node):
        if self.__class__ == node.__class__:
            node.parent = self
            node.level = self.level + 1
            self.children.append(node)

    def equals(self, other):
        if self.__class__ == other.__class__:
            if self.data == other.data and not self.omitted:
                return True
        return False

    def contains(self, other, ignore_omitted):
        found = False
        if self.__class__ == other.__class__:
            if self.data == other.data:
                if ignore_omitted:
                    found = True
                elif not ignore_omitted and not self.omitted:
                    found = True
            else:
                for child in self.children:
                    found = child.contains(other, ignore_omitted)
                    if(found == True):
                        break
        return found

    def contains_ignore_version(self, other):
        found = False
        if self.__class__ == other.__class__:
            if self.groupId == other.groupId and self.artifactId == other.artifactId:
                found = True
            else:
                for child in self.children:
                    found = child.contains_ignore_version(other)
                    if found == True:
                        break
        return found

    def find(self, other):
        found_flag = None
        if self.__class__ == other.__class__:
            if self.data == other.data and not self.omitted:
                found_flag = self
            else:
                for child in self.children:
                    found_flag = child.find(other)
                    if found_flag != None:
                        break
        return found_flag

    def find_contain_omitted(self, other, node_list):
        if self.__class__ == other.__class__:
            if self.data == other.data:
                node_list.append(self)

            for child in self.children:
                child.find_contain_omitted(other, node_list)

    def find_ignore_version(self, other):
        found_flag = None
        if self.__class__ == other.__class__:
            if not self.omitted and self.groupId == other.groupId and self.artifactId == other.artifactId:
                found_flag = self
            else:
                for child in self.children:
                    found_flag = child.find_ignore_version(other)
                    if found_flag != None:
                        break
        return found_flag

    def toString(self):
        tabs = ""
        for i in range(0, self.level):
            tabs += "  "
        # return str(self.level)  + "," + str(self.times) + "," + str(self.omitted) + ","+ tabs + self.data + "\n"
        return tabs + self.data + "\n"

    def build_with_children(self):
        result = self.toString()
        for child in self.children and not child.omitted:
            result += child.build_with_children()
        return result

    def build_with_ancestors(self):
        result = ""
        if self.parent.level > 0:
            result = self.parent.build_with_ancestors()
        return result + self.toString()

######### END OF CLASS ######### 

def main():
    node = Node("hello world")
    print(node.contains("hello world"))

if __name__ == "__main__":
    main()