#!/usr/bin/env python3
# -*- coding: utf8 -*-

import subprocess
import argparse
import os
import glob
import copy
import zipfile
from TreeBuilder import TreeBuilder
from Node import Node

#TODO: 不需要输入完整路径，只需要输入类名，就可以找到所有的jar包，并输出依赖关系
def get_all_classes (pom, project_dir = "", class_name = ""):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the pom.xml.")

    tree = TreeBuilder("dependencyTree.txt").build()
    proc = subprocess.check_call(["rm", "dependencyTree.txt"])

    classes_jar_dict = {} #{classname: [jars]}
    jar_dependency_dict = {} #{jarname: [dependencies]}
    traverse_tree(tree.root, classes_jar_dict, jar_dependency_dict)

    if class_name == "": #no classes given
        show_duplicate_classes (classes_jar_dict)
    else:
        class_len = class_name.split("/")
        if len(class_len) > 1:
            full_path = True
        else:
            full_path = False

        find_jar(class_name, classes_jar_dict, jar_dependency_dict, tree, full_path)


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

    if len(jar_info) == 5:
        path = "/home/mi/.m2/repository/" + groupId + "/" + jar_info[1] + "/" + jar_info[-2] + "/" + jar_info[1] + "-" + jar_info[-2] + ".jar"
    elif len(jar_info) == 6: #dependency has a classifier element
        path = "/home/mi/.m2/repository/" + groupId + "/" + jar_info[1] + "/" + jar_info[-2] + "/" + jar_info[1] + "-" + jar_info[-2] + "-" + jar_info[-3] + ".jar"

    return path


def get_classes(jar_path):
    classes_list = []
    if not os.path.exists(jar_path):
        # print ("[ERROR] " + jar_path + " not found. Its scope might be system.")
        return classes_list
        
    zf = zipfile.ZipFile(jar_path, 'r')
    try:
        lst = zf.infolist()
        for item in lst:
            file = item.filename
            if  file.endswith('.class') and "$" not in file: #ignore inner classes or anonymous class
                classes_list.append(file)
    finally:
        zf.close()

    return classes_list


def show_duplicate_classes (classes_jar_dict):
    duplicate_found = False
    for class_name in classes_jar_dict:
        jar_list = classes_jar_dict[class_name]
        if len(jar_list) > 1:
            if not duplicate_found:
                print ("[WARNING]---------------Duplicate Classes Found---------------")
                duplicate_found = True
            print ("\""+ class_name+ "\" found in", jar_list)

    if not duplicate_found:
        print ("[INFO]---------------No Duplicate Classes Found---------------")

    print ("")


def find_jar (class_name, classes_jar_dict, jar_dependency_dict, tree, full_path):
    if class_name not in classes_jar_dict and full_path:
        print ("[WARNING] " + class_name + "not found\n")
        return

    jar_list  = []
    if full_path:
        jar_list = classes_jar_dict[class_name]

    else:
        for class_temp in classes_jar_dict:
            class_temp_name = class_temp.split("/")[-1]
            if class_temp_name == class_name:
                for jar in classes_jar_dict[class_temp]:
                    jar_list.append(jar)

    print ("\n\""+ class_name+ "\" found in", jar_list)
    for jar in jar_list:
        dependency_list = jar_dependency_dict.get(jar)
        for dependency in dependency_list:
            node = tree.find(Node(dependency))
            print (node.build_with_ancestors())

    print ("")



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("pom", help = "the path of pom file")
    parser.add_argument("-dc", "--duplicateclass", help = " show all found duplicate classes", action = "store_true")
    parser.add_argument("-fj", "--findjar", help = "given a class name, find all jars containing it")

    args = parser.parse_args()

    project_dir = os.path.dirname(args.pom)

    if args.duplicateclass:
        get_all_classes (args.pom, project_dir)

    if args.findjar:
        get_all_classes(args.pom, project_dir, args.findjar)



if __name__ == '__main__':
    main()