#!/usr/bin/env python3
# -*- coding: utf8 -*-

import subprocess
import getpass
import argparse
import os, sys
import zipfile
from TreeBuilder import TreeBuilder
from Node import Node


def get_all_classes (pom, project_dir, outputfile, class_name = ""):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the project.\n")

    tree = TreeBuilder("dependencyTree.txt").build()
    proc = subprocess.check_call(["rm", "dependencyTree.txt"])

    classes_jar_dict = {} #{classname: [jars]}
    jar_dependency_dict = {} #{jarname: [dependencies]}
    traverse_tree(tree.root, classes_jar_dict, jar_dependency_dict)

    if class_name == "": #no classes given
        show_duplicate_classes (classes_jar_dict, outputfile)
    else:
        class_len = class_name.split(".")
        if len(class_len) > 1:
            full_path = True
        else:
            full_path = False

        find_jar(class_name, classes_jar_dict, jar_dependency_dict, tree, full_path, outputfile)


def traverse_tree (root, classes_jar_dict, jar_dependency_dict):
    for child in root.children:
        if not child.omitted:

            dependency = child.get_data()
            jar_path = generate_jar_path(dependency)
            jar_name = jar_path.split("/")[-1]
            if jar_name not in jar_dependency_dict:
                dependency_list = [dependency]
                jar_dependency_dict[jar_name] = dependency_list
            else:
                dependency_list = jar_dependency_dict.get(jar_name)
                dependency_list.append(dependency)

            classes_list = get_classes(jar_path)
            for class_name in classes_list:
                if class_name not in classes_jar_dict:
                    jar_list = [jar_name]
                    classes_jar_dict[class_name] = jar_list
                else:
                    jar_list = classes_jar_dict.get(class_name)
                    jar_list.append(jar_name)

            traverse_tree (child, classes_jar_dict, jar_dependency_dict)


#path = /home/mi/.m2/repository/groupId/artifactId/version/artifactId-version(-classifier).jar (replace "." of groupId with "/")
#The format of jar is: com.xiaomi.telecom.boss:boss-common:jar:1.0.0-SNAPSHOT:compile
def generate_jar_path (jar):
    jar_info = jar.split(":")
    groupId = jar_info[0].replace(".", "/")
    user = getpass.getuser()

    if len(jar_info) == 5:
        path = "/home/" + user+ "/.m2/repository/" + groupId + "/" + jar_info[1] + "/" + jar_info[-2] + "/" + jar_info[1] + "-" + jar_info[-2] + ".jar"
    elif len(jar_info) == 6: #dependency has a classifier element
        path = "/home/" + user+ "/.m2/repository/" + groupId + "/" + jar_info[1] + "/" + jar_info[-2] + "/" + jar_info[1] + "-" + jar_info[-2] + "-" + jar_info[-3] + ".jar"

    return path


def get_classes (jar_path):
    classes_list = []
    if not os.path.exists(jar_path):
        return classes_list
        
    zf = zipfile.ZipFile(jar_path, 'r')
    try:
        lst = zf.infolist()
        for item in lst:
            file = item.filename
            if  file.endswith('.class') and "$" not in file: #ignore inner classes or anonymous class
                file = file[:-6]
                file = file.replace("/", ".")
                classes_list.append(file)
    finally:
        zf.close()

    return classes_list


def show_duplicate_classes (classes_jar_dict, outputfile):
    duplicate_found = False

    for class_name in classes_jar_dict:
        jar_list = classes_jar_dict[class_name]
        if len(jar_list) > 1:
            if not duplicate_found:
                if outputfile == "":
                    print ("[WARNING]---------------Duplicate Classes Found---------------")
                else:
                    with open(outputfile, "a") as f:
                        f.write("[WARNING]---------------Duplicate Classes Found---------------")
                        f.write("\n")
                duplicate_found = True

            if outputfile == "":
                print ("\""+ class_name+ "\" found in", jar_list + "\n")

            else:
                with open(outputfile, "a") as f:
                    f.write("\"" + class_name + "\" found in " + str(jar_list) + "\n\n")


    if not duplicate_found:
        print ("[INFO]---------------No Duplicate Classes Found---------------\n")


def find_jar (class_name, classes_jar_dict, jar_dependency_dict, tree, full_path, outputfile):
    if class_name not in classes_jar_dict and full_path:
        print ("[WARNING] " + class_name + "not found\n")
        return

    jar_list = []
    class_jar_dict = {}
    if full_path:
        jar_list = classes_jar_dict[class_name]
        if outputfile == "":
            print ("\n\""+ class_name+ "\" found in", jar_list)
            print ("-------------------------------------------------------\n")
        else:
            with open (outputfile, "a") as f:
                f.write ("\""+ class_name+ "\" found in " + str(jar_list) + "\n")
                f.write("-------------------------------------------------------\n\n")

        for jar in jar_list:
            dependency_list = jar_dependency_dict.get(jar)
            for dependency in dependency_list:
                node = tree.find(Node(dependency))
                if outputfile == "":
                    print (node.build_with_ancestors() + "\n")
                else:
                    with open (outputfile, "a") as f:
                        f.write (node.build_with_ancestors() + "\n\n")

    else:
        for class_temp in classes_jar_dict:
            class_temp_name = class_temp.split(".")[-1]
            if class_temp_name == class_name:
                for jar in classes_jar_dict[class_temp]:
                    jar_list.append(jar)
                class_jar_dict[class_temp] = jar_list
                jar_list = []

        if outputfile == "":
            print ("\n\""+ class_name+ "\" found in", class_jar_dict)
            print ("-------------------------------------------------------\n")
        else:
            with open (outputfile, "a") as f:
                f.write ("\""+ class_name+ "\" found in " + str(class_jar_dict) + "\n")
                f.write("-------------------------------------------------------\n\n")

        for key in class_jar_dict:
            jar_list = class_jar_dict.get(key)
            for jar in jar_list:
                dependency_list = jar_dependency_dict.get(jar)
                for dependency in dependency_list:
                    node = tree.find(Node(dependency))
                    if outputfile == "":
                        print (node.build_with_ancestors() + "\n")
                    else:
                        with open (outputfile, "a") as f:
                            f.write (node.build_with_ancestors() + "\n\n")


def find_duplicate_dependency (pom, project_dir, outputfile):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the project.\n")

    tree = TreeBuilder("dependencyTree.txt").build()
    proc = subprocess.check_call(["rm", "dependencyTree.txt"])

    duplicate_found = False
    duplicate_found = find_duplicate (tree.root, tree, outputfile, duplicate_found)

    if not duplicate_found:
        print ("[INFO]---------------No Duplicate Dependencies Found---------------\n")

def find_duplicate (node, tree, outputfile, duplicate_found):
    for child in node.children:
        if child.omitted:
            continue

        duplicate_node = tree.find_contain_omitted(child)

        if len(duplicate_node) > 1:
            if not duplicate_found:
                if outputfile == "":
                    print ("[WARNING]---------------Duplicate Dependencies Found---------------\n")
                else:
                    with open (outputfile, "a") as f:
                        f.write ("[WARNING]---------------Duplicate Classes Found---------------\n\n")
                duplicate_found = True
            duplicate_node.remove(child)
            duplicate_node.append(child)
            print_duplicate_node(duplicate_node, outputfile)

        result = find_duplicate(child, tree, outputfile, duplicate_found)

    return (duplicate_found or result)

def print_duplicate_node (node_list, outputfile):
    if outputfile == "": # print on the terminal
        print ("-------------------------------------------------------")
        print (node_list[-1].build_with_ancestors())
        print ("---------------Omitted versions----------------")
        for i in range(0, len(node_list) - 1):
            print (node_list[i].build_with_ancestors() + "\n")
        print ("")
    else:
        with open(outputfile, "a") as f:
            f.write("-------------------------------------------------------\n")
            f.write(node_list[-1].build_with_ancestors() + "\n")
            f.write("---------------Omitted versions----------------\n")
            for i in range(0, len(node_list) - 1):
                f.write (node_list[i].build_with_ancestors() + "\n")
            f.write("\n")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("pom", help = "the path of pom file")
    parser.add_argument("-dc", "--duplicateclass", help = " find all found duplicate classes", action = "store_true")
    parser.add_argument("-fj", "--findjar", help = "find all jars containing a given class name")
    parser.add_argument("-dj", "--duplicatejar", help = "find all jars if they have different versions or they repeat the same version", action = "store_true")
    parser.add_argument("-of", "--outputfile", help = "output the result to file. This param only works for -dc and -dj")

    args = parser.parse_args()

    project_dir = os.path.dirname(args.pom)

    if args.outputfile:
        temp = args.outputfile.split("/")
        if len(temp) == 1 and project_dir != "":
            args.outputfile = project_dir + "/" + args.outputfile

        with open(args.outputfile, "w") as f: #clean the output file
            f.write("")
    else:
        args.outputfile = ""

    if args.duplicateclass:
        get_all_classes (args.pom, project_dir, args.outputfile)

    if args.findjar:
        get_all_classes(args.pom, project_dir, args.outputfile, args.findjar)

    if args.duplicatejar:
        find_duplicate_dependency(args.pom, project_dir, args.outputfile)


    if  not (args.duplicateclass or args.findjar or args.duplicatejar):
        print ("Failed to run. Please specify at least one optional argument.")
        print ("Type \"./TraverseJar.py -h\" for details.")

if __name__ == '__main__':
    main()