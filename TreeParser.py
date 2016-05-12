from itertools import islice

class TreeParser:
    def __init__(self, data):
        self.data = data
        self.root_name = ""

    def parse(self):
        nodeList = []
        f = open(self.data)
        self.root_name = f.readline().strip("\n");

        for line in islice(f, 1, None):
            nodeList.append(line.strip("\n"))
        f.close()
        return nodeList

def main():
    dataFile = "dependencyTree.txt"
    temp  = TreeParser(dataFile)
    nodeList = temp.parse()
    print (temp.root_name)

    for rawNode in nodeList:
        print(rawNode)


if __name__ == '__main__':
    main()