import argparse
import os

parser = argparse.ArgumentParser()

parser.add_argument("path", help = "the path of pom file")
parser.add_argument("-addcommon", help = "add common dependencies", action = "store_true")
parser.add_argument("-addundeclared", help = " add used and undeclared dependencies", action = "store_true")
parser.add_argument("-exclude", help = "exclude heavy transitive dependencies. Please note that this method will remove dependencies and project might doesn't work after removing. Do not use this until you can handle when the project compiles or runs unsuccessfully.", action = "store_true")
# parser.add_argument("-h", "--help", help = "show this message", action = "store_true")

args = parser.parse_args()
# if args.addcommon:
#     print (args.addcommon)

print (os.path.dirname(args.path))