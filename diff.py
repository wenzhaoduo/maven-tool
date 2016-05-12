#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from TreeBuilder import TreeBuilder
from Node import Node

def find_diff (new_pom, old_pom):
    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the pom.xml.")

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

    new_dependency = []

    find_diff_and_new (new_tree.root.children, old_tree, new_dependency)
    print_new_dependency1(new_tree, new_dependency)

def find_diff_and_new (children, old_tree, new_dependency):
    for child in children: 
        if old_tree.contains_ignore_version(child) and not old_tree.contains(child):
            found_node = old_tree.find_ignore_version(child)
            parent = child
            while parent.level > 1:
                parent = parent.get_parent()
            print ("[WARNING] Changed dependency: \"" + found_node.toString().strip() + "\" --> \"" + child.toString().strip() + "\" UNDER \"" + parent.toString().strip() + "\".")

        elif not old_tree.contains_ignore_version(child):
            new_dependency.append(child)

        find_diff_and_new(child.children, old_tree, new_dependency)

def print_new_dependency1(tree, new_dependency):
    print ("[INFO]----------------------------------------------------New dependencies found----------------------------------------------------")

    for dependency in new_dependency:
        parent = dependency
        while parent.level > 1:
            parent = parent.get_parent()
        print ("[INFO] New dependency: \"" + dependency.toString().strip() + "\" UNDER \"" + parent.toString().strip() + "\". ")

def main():
    old_pom = "pom_backup.xml"
    new_pom = "pom.xml"

    find_diff(new_pom, old_pom)

if __name__ == "__main__":
    main()
