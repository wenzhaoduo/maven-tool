#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import xml.etree.ElementTree as ET
import re
import sys
import types
from TreeBuilder import TreeBuilder

#namespace
POM_NS = "{http://maven.apache.org/POM/4.0.0}"
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")

#file name
DEPENDENCY_TREE_FILE = "dependencyTree.txt"
MODIFIED_DEPENDENCY_FILE = "modifiedDependency.txt"


# add the dependencies used commonly
def add_common_dependency (pom):
    try:
        proc = subprocess.check_call(["mvn", "clean", "dependency:tree", "-Dverbose", "-Doutput=dependencyTree.txt", "-DoutputType=text"], stdout=subprocess.PIPE) 
    except  subprocess.CalledProcessError: # if something wrong with pom.xml, mvn dependency:analyze will not execute successfully, so we raise an error and stop the program
        sys.exit ("[ERROR]: An error occurs when generating dependency tree of project. Please check the pom.xml.")

    tree = TreeBuilder(DEPENDENCY_TREE_FILE).build()

    find_common_dependency (pom, tree.root)


def find_common_dependency (pom, root):
    for child in root.children:
        if child.get_times() >= 5:
            jar_info = child.get_data().split(":")
            dependency = jar_info[0] + ":" + jar_info[1] + ":" + jar_info[-2]

            if len(jar_info) == 6: #append classifier tag
                dependency = dependency + ":" + jar_info[-3]

            add_dependency(pom, dependency)

        find_common_dependency (pom, child)


# add used and undeclared dependency
#TODO: keep the comment when revise the pom file.
#TODO: handle classifier tag
def add_used_undeclared_dependency (pom): 
    analyze_output = "dependencyAnalyze.xml"
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
    returnStatus = 0 #decide whether calling this function again
    for line in analyze_pom:
        line = line.strip()

        if line == "<dependency>":
            flag = True
            returnStatus = 1
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
    return returnStatus


#TODO: handle the dependency with classifier tag.
def add_dependency (pom, data):
    with open(MODIFIED_DEPENDENCY_FILE, "a") as f:
        f.write(data)
        f.write("\n")

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


# modify the pom.xml to make it look comfortable
def pretty_pom (element, indent, newline, level = 0): # elemnt为传进来的Elment类，参数indent用于缩进，newline用于换行  
    if element:  # 判断element是否有子元素  
        if element.text == None or element.text.isspace(): # 如果element的text没有内容  
            element.text = newline + indent * (level + 1)    
        else:  
            element.text = newline + indent * (level + 1) + element.text.strip() + newline + indent * (level + 1)  
    #else:  # 此处两行如果把注释去掉，Element的text也会另起一行  

    temp = list(element) # 将elemnt转成list  
    for subelement in temp:  
        if temp.index(subelement) < (len(temp) - 1): # 如果不是list的最后一个元素，说明下一个行是同级别元素的起始，缩进应一致  
            subelement.tail = newline + indent * (level + 1)  
        else:  # 如果是list的最后一个元素， 说明下一行是母元素的结束，缩进应该少一个  
            subelement.tail = newline + indent * level  
        pretty_pom(subelement, indent, newline, level = level + 1) # 对子元素进行递归操作  


def exclude_heavy_transitive_depency (pom):
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
            if (children_number >= 5):
                exclude_dependency(pom, grandchild.get_data(), child.get_data())
                exclude_flag = True

    return exclude_flag


def count_children (root):
    counts = 0
    for child in root.children:
        counts = counts + 1 + count_children(child)
    return counts


# exclude the child_dependency from root_dependency
def exclude_dependency (pom, child_dependency, root_dependency):
    with open(MODIFIED_DEPENDENCY_FILE, "a") as f:
        f.write(child_dependency)
        f.write("\n")


    root_dependency_info = root_dependency.split(":")
    child_dependency_info = child_dependency.split(":")

    tree = ET.parse(pom)
    root = tree.getroot()
    dependencies = root.find("%sdependencies" %(POM_NS))

    for dependency in dependencies:
        flag = 0;
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

        childElement = ET.SubElement(exclusion, "groupId")
        childElement.text = child_dependency_info[0]
        childElement.tail = "\n"

        childElement = ET.SubElement(exclusion, "artifactId")
        childElement.text = child_dependency_info[1]
        childElement.tail = "\n"

    tree.write(pom, method = "xml")

def main():
    #clear the modifiedDependency.txt
    f = open(MODIFIED_DEPENDENCY_FILE, "w")
    f.write("")
    f.close()


    print ("[INFO] Adding common dependencies...")

    f = open(MODIFIED_DEPENDENCY_FILE, "a")
    f.write("[INFO] Dependecies are added bacause they are commonly used.\n")
    f.write("[INFO]------------------------------------------------------------------------------------\n")
    f.close()

    add_common_dependency("pom.xml")

    f = open(MODIFIED_DEPENDENCY_FILE, "a")
    f.write("[INFO]------------------------------------------------------------------------------------\n\n")


    print ("[INFO] Adding used and undeclared dependencies...")

    f.write("[INFO] Dependecies are added bacause they are used and undeclared.\n")
    f.write("[INFO]------------------------------------------------------------------------------------\n")
    f.close()

    status = add_used_undeclared_dependency("pom.xml")
    while status == 1:
        status = add_used_undeclared_dependency("pom.xml")

    f = open(MODIFIED_DEPENDENCY_FILE, "a")
    f.write("[INFO]------------------------------------------------------------------------------------\n\n")


    print ("[INFO] Excluding heavy transitive dependencies...")

    f.write("[INFO] These are heavy transitive dependecies excluded.\n")
    f.write("[INFO]------------------------------------------------------------------------------------\n")
    f.close()

    exclude_flag = exclude_heavy_transitive_depency("pom.xml")
    while exclude_flag:
        exclude_flag = exclude_heavy_transitive_depency ("pom.xml")

    f = open(MODIFIED_DEPENDENCY_FILE, "a")
    f.write("[INFO]------------------------------------------------------------------------------------\n\n")
    f.close()


    tree = ET.parse("pom.xml")
    root = tree.getroot()
    pretty_pom(root, "    ", "\n")
    tree.write("pom.xml", method = "xml")


if __name__ == '__main__':
    main()