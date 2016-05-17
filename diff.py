#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys,os
import argparse
from TreeBuilder import TreeBuilder
from Node import Node

def find_diff (project_dir):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the pom.xml.")

    proc = subprocess.check_call(["mv", "pom.xml", "new_pom.xml"])
    proc = subprocess.check_call(["mv", "pomBase.xml", "pom.xml"])

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=oldDependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of old version project. Please check the old version pom.xml.")

    proc = subprocess.check_call(["mv", "pom.xml", "pomBase.xml"])
    proc = subprocess.check_call(["mv", "new_pom.xml", "pom.xml"])

    old_tree = TreeBuilder("oldDependencyTree.txt").build()
    new_tree = TreeBuilder("dependencyTree.txt").build()

    new_dependency = []

    print ("[INFO]-----------------Version changed dependencies-----------------")
    find_diff_and_new (new_tree.root.children, old_tree, new_dependency)
    print ("[INFO]-----------------------------------------------------------------------------\n")

    print ("[INFO]-----------------New dependencies-----------------")
    print_new_dependency(new_tree, new_dependency)
    print ("[INFO]-----------------------------------------------------------------------------\n")

    proc = subprocess.check_call(["rm", "dependencyTree.txt", "oldDependencyTree.txt", "pomBase.xml"])


def find_diff_and_new (children, old_tree, new_dependency):
    for child in children: 
        if old_tree.contains_ignore_version(child) and not old_tree.contains(child):
            found_node = old_tree.find_ignore_version(child)
            parent = child
            while parent.level > 1:
                parent = parent.get_parent()
            print ("[WARNING] Changed dependency: \"" + found_node.toString().strip() + "\" --> \"" + child.toString().strip() + "\" UNDER \"" + parent.toString().strip() + "\"")

        elif not old_tree.contains_ignore_version(child):
            new_dependency.append(child)

        find_diff_and_new(child.children, old_tree, new_dependency)


def print_new_dependency(tree, new_dependency):
    for dependency in new_dependency:
        parent = dependency
        while parent.level > 1:
            parent = parent.get_parent()
        print ("[INFO] New dependency: \"" + dependency.toString().strip() + "\" UNDER \"" + parent.toString().strip() + "\"")


def get_pom_base(project_dir, branch = "master", version = None):
    if project_dir != "":
        os.chdir(project_dir)

    proc = subprocess.check_call(["cp", "pom.xml", "pom_newversion.xml"])

    if version == None:
        proc = subprocess.check_call(["git", "fetch", "origin", branch], stdout=subprocess.PIPE)
    else:
        proc = subprocess.check_call(["git", "fetch", "origin", version], stdout=subprocess.PIPE)

    proc = subprocess.check_call(["git", "checkout", "FETCH_HEAD", "--", "pom.xml" ])

    proc = subprocess.check_call(["mv", "pom.xml", "pomBase.xml"])
    proc = subprocess.check_call(["mv", "pom_newversion.xml", "pom.xml"])


def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument("pom", help = "the path of pom.xml")

    parser.add_argument("-b", "--branch", help = "select a branch. Default branch is master")
    parser.add_argument("-v", "--version", help = "select a version number. This will ignore the branch even if branch is given")

    args = parser.parse_args()

    project_dir = os.path.dirname(args.pom)

    if args.version:
        get_pom_base(project_dir, version = args.version)

    elif args.branch:
        get_pom_base(project_dir, branch = args.branch)

    else:
        get_pom_base(project_dir)

    find_diff(project_dir)

if __name__ == "__main__":
    main()
