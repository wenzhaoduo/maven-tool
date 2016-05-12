#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import xml.etree.ElementTree as ET
import sys
import os
from TreeBuilder import TreeBuilder
from Node import Node

#namespace
POM_NS = "{http://maven.apache.org/POM/4.0.0}"
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

def find_new_dependency (old_root, new_root):
    new_dependency_list = []

    old_dependencies = old_root.find("%sdependencies" %(POM_NS))
    new_dependencies = new_root.find("%sdependencies" %(POM_NS))

    for new_dependency in new_dependencies:
        new_groupId = new_dependency.find("%sgroupId" %(POM_NS)).text
        new_artifactId = new_dependency.find("%sartifactId" %(POM_NS)).text
        new_version = new_dependency.find("%sversion" %(POM_NS)).text
        
        find_dependency = False
        for old_dependency in old_dependencies:
            old_groupId = old_dependency.find("%sgroupId" %(POM_NS)).text
            old_artifactId = old_dependency.find("%sartifactId" %(POM_NS)).text
            old_version = old_dependency.find("%sversion" %(POM_NS)).text

            flag = 0
            if new_groupId == old_groupId:
                flag = flag + 1

            if new_artifactId == old_artifactId:
                flag = flag + 1

            if flag == 2:
                find_dependency = True
                break

        if not find_dependency:
            new_dependency_list.append(new_dependency)

    print_new_dependency (new_dependency_list)

def print_new_dependency (new_dependency):
    tree = TreeBuilder("dependencyTree.txt").build()

    print ("[INFO] The new pom has new dependencies below.")
    for dependency in new_dependency:
        root = ""
        child = dependency.find("%sgroupId" %(POM_NS))
        if (child != None):
            groupId = child.text
            root = root + groupId + ":"

        child = dependency.find("%sartifactId" %(POM_NS))
        if (child != None):
            artifactId = child.text
            root = root + artifactId + ":jar:" 

        child = dependency.find("%sclassifier" %(POM_NS))
        if (child != None):
            classifier = child.text
            root = root + classifier + ":"

        child = dependency.find("%sversion" %(POM_NS))
        if (child != None):
            version = child.text
            root = root + version + ":compile"

        print (root)
        found_node = tree.find(Node(root))
        print(found_node.build_with_children())

def find_diff_version (new_pom, old_pom):
    new_dependency = []

    proc = subprocess.check_call(["mv", new_pom, "new_pom.xml"])
    proc = subprocess.check_call(["mv", old_pom, "pom.xml"])

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=oldDependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of old version project. Please check the old version pom.xml.")

    proc = subprocess.check_call(["mv", "pom.xml", "pom_backup.xml"])
    proc = subprocess.check_call(["mv", "new_pom.xml", "pom.xml"])

    old_tree = TreeBuilder("oldDependencyTree.txt").build()
    new_tree = TreeBuilder("dependencyTree.txt").build()

    find_diff (new_tree.root.children, old_tree, new_dependency)
    print_new_dependency1(new_tree, new_dependency)

def find_diff (children, old_tree, new_dependency):
    for child in children: #first level dependency
        if old_tree.contains_ignore_version(child) and not old_tree.contains(child):
            found_node = old_tree.find_ignore_version(child)
            parent = child
            while parent.level > 1:
                parent = parent.get_parent()
            print ("[WARNING] Changed dependency: \"" + found_node.toString().strip() + "\" --> \"" + child.toString().strip() + "\" UNDER \"" + parent.toString().strip() + "\".")

        elif not old_tree.contains_ignore_version(child):
            new_dependency.append(child)

        find_diff(child.children, old_tree, new_dependency)

def print_new_dependency1(tree, new_dependency):
    print ("[INFO]-------------------------------------------------------------------------------------------------------------------------")

    for dependency in new_dependency:
        parent = dependency
        while parent.level > 1:
            parent = parent.get_parent()
        print ("[WARNING] New dependency: \"" + dependency.toString().strip() + "\" UNDER \"" + parent.toString().strip() + "\". ")
        
        # found_node = tree.find(dependency)
        # print(found_node.build_with_children())

def main():
    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the pom.xml.")

    old_pom = "pom_backup.xml"
    new_pom = "pom.xml"

    old_root = ET.parse(old_pom).getroot()
    new_root = ET.parse(new_pom).getroot()

    # find_new_dependency(old_root, new_root)
    find_diff_version(new_pom, old_pom)

if __name__ == "__main__":
    main()
