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
    def get_data_for_display(self):
        data_spilt = self.data.split(":")
        groupId = data_spilt[0]
        artifactId = data_spilt[1]
        version = data_spilt[-2]
        if len(data_spilt) == 5:
            return groupId + ":" + artifactId + ":" + version
        else:
            classifier = data_spilt[-3]
        return groupId + ":" + artifactId + ":" + classifier + ":" + version

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
                if not ignore_omitted:
                    found = True
                elif ignore_omitted and not self.omitted:
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
            if self.data == other.data:
                found_flag = self
            else:
                for child in self.children:
                    if child.omitted:
                        continue
                    found_flag = child.find(other)
                    if found_flag != None:
                        break
        return found_flag

    def find_contain_omitted(self, other, node_list): #all dependencies with the same groupId and artifactId as self
        if self.__class__ == other.__class__:
            if self.groupId == other.groupId and self.artifactId == other.artifactId:
                node_list.append(self)

            for child in self.children:
                child.find_contain_omitted(other, node_list)


    def find_ignore_version(self, other): #find an dependency with the same groupId and artifactId as self
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
        for child in self.children:
            result += child.build_with_children()
        return result

    def build_with_ancestors(self):
        result = self.get_ancestors()
        ancestors = result.split("\n")
        result = ancestors[0].strip()

        for i in range(1, len(ancestors) - 1):
            result = result + " --> " + ancestors[i]

        return result

    def get_ancestors(self):
        result = ""
        if self.parent.level > 0:
            result = self.parent.get_ancestors()
        return result + self.get_data_for_display() + "\n"


def main():
    node = Node("hello world")
    print(node.contains("hello world"))

if __name__ == "__main__":
    main()