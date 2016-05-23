#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import xml.etree.ElementTree as ET
import re
import sys, os
import argparse
from TreeBuilder import TreeBuilder

#namespace
POM_NS = "{http://maven.apache.org/POM/4.0.0}"
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

#file name
DEPENDENCY_TREE_FILE = "dependencyTree.txt"
MODIFIED_DEPENDENCY_FILE = "modifiedDependency.txt"


# add the dependencies used commonly
# TODO: 添加参数times，让使用者决定出现多少次以上需要提到一级依赖
def add_common_dependency (pom, project_dir, common_times):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the pom.xml.")

    tree = TreeBuilder(DEPENDENCY_TREE_FILE).build()

    find_common_dependency (pom, tree.root, common_times)

    proc = subprocess.check_call(["rm", DEPENDENCY_TREE_FILE])


def find_common_dependency (pom, root, common_times):
    for child in root.children:
        if child.get_times() >= int(common_times) and child.get_level() > 1: #if a dependency appear more than 5 times, declare it on the pom.xml
            jar_info = child.get_data().split(":")
            dependency = jar_info[0] + ":" + jar_info[1] + ":" + jar_info[-2]

            if len(jar_info) == 6: #append classifier tag
                dependency = dependency + ":" + jar_info[-3]

            add_dependency(pom, dependency)

        find_common_dependency (pom, child, common_times)


def add_dependency (pom, data):
    print (data)

    tree = ET.parse(pom)
    root = tree.getroot()
    dependencies = root.find("%sdependencies" %(POM_NS))

    dependency = ET.SubElement(dependencies, "dependency")
    dependency.tail = "\n"
    dependency.text = "\n"

    jar_info = data.split(":")

    childElement = ET.SubElement(dependency, "groupId")
    childElement.text = jar_info[0]
    childElement.tail = "\n"

    childElement = ET.SubElement(dependency, "artifactId")
    childElement.text = jar_info[1]
    childElement.tail = "\n"

    childElement = ET.SubElement(dependency, "version")
    childElement.text = jar_info[2]
    childElement.tail = "\n"

    if len(jar_info) == 4:
        childElement = ET.SubElement(dependency, "classifier")
        childElement.text = jar_info[3]
        childElement.tail = "\n"

    tree.write(pom, method = "xml")


# add used and undeclared dependency
def add_used_undeclared_dependency (pom, project_dir): 
    if project_dir != "":
        os.chdir(project_dir)

    analyze_output = "dependencyAnalyze.txt"
    analyze_pom = open(analyze_output, "w")  #write the result of analyze to this file
    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:analyze", "-DoutputXML"], stdout=analyze_pom) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when analyzing dependencies of project. Please check the pom.xml.")
    finally:
        analyze_pom.close()

    analyze_pom = open(analyze_output, "r")
    data = ""
    flag = False
    data_construct_finished = False
    return_status = False #decide whether calling this function again
    for line in analyze_pom:
        line = line.strip()

        if line == "<dependency>":
            flag = True
            return_status = True
            continue
        elif line == "</dependency>":
            flag = False
            data_construct_finished = True
        elif line == "</version>":
            continue

        if flag:
            pattern = re.compile(">[^<]+<")
            temp = re.findall(pattern, line)
            elementText = temp[0].strip("<>")

            if data == "":
                data = data + elementText
            else:
                data = data + ":" + elementText

            if len(temp) == 2:
                elementText = temp[1].strip("<>")
                data = data + ":" + elementText

        if data_construct_finished:
            add_dependency(pom, data)
            data_construct_finished = False
            data = ""

    analyze_pom.close()
    proc = subprocess.check_call(["rm", "dependencyAnalyze.txt"])
    return return_status


# TODO: 添加参数times，让使用者决定二级依赖节点数在多大规模时需要exclude
def exclude_heavy_transitive_depency (pom, project_dir, exclude_fail, heavy_times):
    if project_dir != "":
        os.chdir(project_dir)

    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the pom.xml.")

    tree = TreeBuilder(DEPENDENCY_TREE_FILE).build()

    # if a transitive dependency has more than 5 children, exclude it.
    exclude_flag = False;
    for child in tree.root.children: #first level dependency
        for grandchild in child.children: #second level dependency
            children_number = count_children(grandchild) + 1
            if children_number >= heavy_times and not grandchild.get_data() in exclude_fail:
                exclude_succ = exclude_dependency(pom, project_dir, grandchild.get_data(), child.get_data())
                if not exclude_succ:
                    exclude_fail.append(grandchild.get_data())
                exclude_flag = True

    proc = subprocess.check_call(["rm", DEPENDENCY_TREE_FILE])
    return exclude_flag


def count_children (root):
    counts = 0
    for child in root.children:
        counts = counts + 1 + count_children(child)
    return counts


# exclude the child_dependency from root_dependency
def exclude_dependency (pom, project_dir, child_dependency, root_dependency):
    root_dependency_info = root_dependency.split(":")
    child_dependency_info = child_dependency.split(":")

    tree = ET.parse(pom)
    root = tree.getroot()
    dependencies = root.find("%sdependencies" %(POM_NS))

    for dependency in dependencies:
        flag = 0
        for child in dependency[0: 2]:
            tag = child.tag.replace(POM_NS, "")
            if tag == "groupId" and  child.text == root_dependency_info[0]:
                flag = flag + 1
            elif tag == "artifactId" and child.text == root_dependency_info[1]:
                flag = flag + 1

        if flag != 2:
            continue

        exclusions = dependency.find("%sexclusions" %(POM_NS))
        if exclusions == None:
            exclusions = ET.Element("exclusions")
            dependency.insert(3, exclusions)

        exclusion = ET.SubElement(exclusions, "exclusion")
        exclusion.text = "\n"
        exclusion.tail = "\n"

        groupId = ET.SubElement(exclusion, "groupId")
        groupId.text = child_dependency_info[0]
        groupId.tail = "\n"

        artifactId = ET.SubElement(exclusion, "artifactId")
        artifactId.text = child_dependency_info[1]
        artifactId.tail = "\n"

    if project_dir != "":
        os.chdir(project_dir)

    proc = subprocess.check_call(["cp", "pom.xml", "pom_old.xml"]) #backup pom.xml

    tree.write(pom, method = "xml")

    exclude_succ = True
    try:
        proc = subprocess.check_call(["mvn", "clean", "compile"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: 
        proc = subprocess.check_call(["rm", "pom.xml"])
        proc = subprocess.check_call(["cp", "pom_old.xml", "pom.xml"])
        exclude_succ = False
    finally:
        proc = subprocess.check_call(["rm", "pom_old.xml"])

    if exclude_succ:
        print (child_dependency)

    return exclude_succ


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


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("pom", help = "the path of pom file")
    parser.add_argument("-addundeclared", help = " add used and undeclared dependencies", action = "store_true")
    parser.add_argument("-addcommon", help = "add common dependencies")
    parser.add_argument("-exclude", help = "exclude heavy transitive dependencies. Please note that this method will remove dependencies and project might doesn't work after removing. Do not use this until you can handle when the project compiles or runs unsuccessfully")

    args = parser.parse_args()

    project_dir = os.path.dirname(args.pom)

    if args.addcommon:
        print ("[INFO]----------Adding commonly used dependencies----------")

        add_common_dependency(args.pom, project_dir, args.addcommon)

        print ("[INFO]----------------------------------------------------------------------\n")

        
    if args.addundeclared:
        print ("[INFO]----------Adding used undeclared dependencies----------")

        status = add_used_undeclared_dependency(args.pom, project_dir)
        while status:
            status = add_used_undeclared_dependency(args.pom, project_dir)

        print ("[INFO]----------------------------------------------------------------------\n")
        

    if args.exclude:
        print ("[INFO]----------Heavy transitive Dependencies----------")

        exclude_fail = []
        status = exclude_heavy_transitive_depency(args.pom, project_dir, exclude_fail, args.exclude)
        while status:
            status = exclude_heavy_transitive_depency (args.pom, project_dir, exclude_fail, args.exclude)

        print ("[INFO]----------------------------------------------------------------------\n")


    if args.addcommon or args.addundeclared or args.exclude:
        pretty_pom(args.pom)
    else:
        print ("Failed to run. Please specify at least one optional argument.")
        print ("Type \"./AnalyzeDependency.py -h\" for more information.")
        

if __name__ == '__main__':
    main()