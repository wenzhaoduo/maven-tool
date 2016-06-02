#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import xml.etree.ElementTree as ET
import sys, os
import argparse
from TreeBuilder import TreeBuilder
from Node import Node

#namespace
POM_NS = "{http://maven.apache.org/POM/4.0.0}"
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

#file name
DEPENDENCY_TREE_FILE = "dependencyTree.txt"
MODIFIED_DEPENDENCY_FILE = "modifiedDependency.txt"


# find the dependencies used commonly
def find_common_dependency (pom, project_dir, common_times):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the project.")

    tree = TreeBuilder(DEPENDENCY_TREE_FILE).build()

    find_common (pom, tree.root, common_times)

    proc = subprocess.check_call(["rm", DEPENDENCY_TREE_FILE])


def find_common (pom, root, common_times):
    for child in root.children:
        if child.get_times() >= int(common_times) and child.get_level() > 1: #if a dependency appear frequently more than common_times, declare it in the pom.xml
            # add_dependency(pom, child)
            print(child.build_with_ancestors())

        find_common (pom, child, common_times)


def add_dependency (pom, node):
    print(node.build_with_ancestors())

    tree = ET.parse(pom)
    root = tree.getroot()
    dependencies = root.find("%sdependencies" %(POM_NS))

    dependency = ET.SubElement(dependencies, "dependency")
    dependency.tail = "\n"
    dependency.text = "\n"

    data = node.get_data()
    jar_info = data.split(":")

    childElement = ET.SubElement(dependency, "groupId")
    childElement.text = jar_info[0]
    childElement.tail = "\n"

    childElement = ET.SubElement(dependency, "artifactId")
    childElement.text = jar_info[1]
    childElement.tail = "\n"

    childElement = ET.SubElement(dependency, "version")
    childElement.text = jar_info[-2]
    childElement.tail = "\n"

    if len(jar_info) == 6:
        childElement = ET.SubElement(dependency, "classifier")
        childElement.text = jar_info[-3]
        childElement.tail = "\n"

    tree.write(pom, method = "xml")


def add_used_undeclared_dependency (pom, project_dir): 
    if project_dir != "":
        os.chdir(project_dir)

    analyze_output = "dependencyAnalyze.txt"
    analyze_pom = open(analyze_output, "w")  #write the result of analyze to this file
    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:analyze"], stdout=analyze_pom) 
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the project.")
    finally:
        analyze_pom.close()

    tree = TreeBuilder(DEPENDENCY_TREE_FILE).build()
    node = ""

    analyze_pom = open(analyze_output, "r")
    data = ""
    flag = False
    return_status = False #decide whether calling this function again
    for line in analyze_pom:
        if line == "[WARNING] Used undeclared dependencies found:\n":
            flag = True
            continue

        elif flag and not line.startswith("[WARNING]    "):
            break

        if flag:
            data = line.strip("[WARNING] \n")
            found_node = tree.root.find(Node(data))
            add_dependency(pom, found_node)

    analyze_pom.close()
    proc = subprocess.check_call(["rm", analyze_output, DEPENDENCY_TREE_FILE])
    return return_status


def find_heavy_transitive_dependency (pom, project_dir, heavy_times):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the project.")

    tree = TreeBuilder(DEPENDENCY_TREE_FILE).build()

    for child in tree.root.children: #first level dependency
        for grandchild in child.children: #second level dependency
            children_number = count_children(grandchild) + 1
            if children_number >= int(heavy_times):
                print (grandchild.get_data())

    proc = subprocess.check_call(["rm", DEPENDENCY_TREE_FILE])


def count_children (root):
    counts = 0
    for child in root.children:
        if not child.omitted:
            counts = counts + 1 + count_children(child)
    return counts


def pretty_pom (pom):
    tree = ET.parse(pom)
    root = tree.getroot()
    pretty_pom_run(root, "    ", "\n")
    tree.write(pom, method = "xml")


# revise the pom.xml to make it look comfortable
def pretty_pom_run (element, indent, newline, level = 0): 
    if element: 
        if element.text == None or element.text.isspace(): 
            element.text = newline + indent * (level + 1)    
        else:  
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)  

    temp = list(element)
    for subelement in temp:  
        if temp.index(subelement) < (len(temp) - 1): 
            subelement.tail = newline + indent * (level + 1)  
        else: 
            subelement.tail = newline + indent * level  
        pretty_pom_run(subelement, indent, newline, level = level + 1) 


def main ():
    parser = argparse.ArgumentParser()

    parser.add_argument("pom", help = "the path of pom file")
    parser.add_argument("-au", "--addundeclared", help = " add used and undeclared dependencies", action = "store_true")
    parser.add_argument("-fc", "--findcommon", help = "find all dependencies appearing frequently more than a given number")
    parser.add_argument("-fh", "--findheavy", help = "find all heavy transitive dependencies with children more than a given number")

    args = parser.parse_args()

    project_dir = os.path.dirname(args.pom)

    if args.findcommon:
        print ("[INFO]----------Commonly Used Dependencies Found----------\n")

        find_common_dependency(args.pom, project_dir, args.findcommon)

        print ("[INFO]----------------------------------------------------------------------\n")

        
    if args.addundeclared:
        print ("[INFO]----------Adding Used Undeclared Dependencies----------\n")

        status = add_used_undeclared_dependency(args.pom, project_dir)
        while status:
            status = add_used_undeclared_dependency(args.pom, project_dir)

        print ("[INFO]----------------------------------------------------------------------\n")
        

    if args.findheavy:
        print ("[INFO]----------Heavy Level 2 Dependencies Found----------\n")

        find_heavy_transitive_dependency(args.pom, project_dir, args.findheavy)

        print ("[INFO]----------------------------------------------------------------------\n")


    if args.addundeclared:
        pretty_pom(args.pom)


    if not (args.findcommon or args.addundeclared or args.findheavy):
        print ("Failed to run. Please specify at least one optional argument.")
        print ("Type \"./AnalyzeDependency.py -h\" for details.")
        

if __name__ == '__main__':
    main()