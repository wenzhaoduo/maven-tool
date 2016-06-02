---------------------------------------------
Principles Of Dependency Tree
---------------------------------------------

(1) 根节点作为0级依赖
(2) 如果两个依赖版本不同，则认为是不同的依赖
(3) 除了0级依赖 (根节点) 和一级依赖 (pom中声明的依赖)，其他都认为是传递依赖


-----------
diff.py
-----------

此程序可以判断当添加某一个依赖后，新添加的依赖引入的依赖有哪些，以及整个项目是否有依赖的版本发生了改变。

(1) Strategy

step1
根据调用时传入的参数 branch 或者 version，从 git.n.xiaomi.com 上选择一个 pom.xml 作为基准
如果同时指定 branch 和 version，仅考虑 version 所对应的pom.xml
如果没有指定 branch，则默认是 master 上最新的 pom.xml（可能有其他开发者有新的push），因此建议指定版本

git fetch origin <branch> or <commitID> //下载所有的change
git checkout FETCH_HEAD -- pom.xml //将change应用到pom.xml

step2
比较本地 pom.xml 的依赖树和从 git 上拉下来的 pom.xml 的依赖树
比较是否有传递依赖的版本发生变化或者本地 pom.xml 的依赖树新增了依赖
在终端输出比较结果

(2) Command Line Arguments

usage: diff.py [-h] [-b BRANCH] [-v VERSION] pom

positional arguments:
  pom                   the path of pom.xml

optional arguments:
  -h, --help    show this help message and exit
  -b BRANCH, --branch BRANCH
                            select a branch. Default branch is master
  -v VERSION, --version VERSION
                            select a version number. This will ignore the branch
                            even if branch is given

(3) Example

(3.1) 比较本地pom.xml 和 master 分支下最新的pom.xml
    ./diff.py ~/boss-operations/pom.xml

(3.1) 比较本地pom.xml 和 maven-dev 分支下最新的pom.xml
    ./diff.py ~/boss-operations/pom.xml -b maven-dev

(3.2) 比较本地pom.xml 和 434082306750c215a26044bcdc165c740ddfa6be 对应的pom.xml
    ./diff.py ~/boss-operations/pom.xml -v 434082306750c215a26044bcdc165c740ddfa6be

(4) Output Example

来自 git.n.xiaomi.com:xiaomi-telecom/boss-operations
 * branch            maven-dev  -> FETCH_HEAD
[INFO]-----------------Version changed dependencies-----------------
[WARNING] Changed dependency: "org.codehaus.plexus:plexus-utils:2.0.5" --> "org.codehaus.plexus:plexus-utils:1.4.1" UNDER "org.apache.maven:maven-artifact:2.0.6"
[INFO]-----------------------------------------------------------------------------

[INFO]-----------------New dependencies-----------------
[INFO] New dependency: "com.xiaomi.infra:scribe-log4j:1.0.0-SNAPSHOT" UNDER "org.apache.hbase:hbase:0.94.11-mdh1.2.5"
[INFO]-----------------------------------------------------------------------------

 * branch            maven-dev  -> FETCH_HEAD
 表示将采用 maven-dev 分支下最新的 pom.xml 作为比较基准

Changed dependency: "commons-digester:commons-digester:1.8" --> "commons-digester:commons-digester:1.6" 
表示依赖 "commons-digester:commons-digester:1.8" 有新版本 "commons-digester:commons-digester:1.6"

UNDER "com.xiaomi:xiaomi-common-logger:2.6.26"
表示在一级依赖 "com.xiaomi:xiaomi-common-logger:2.6.26" 下


-----------------------------------
AnalyzeDependency.py
-----------------------------------

(1) Strategy

(1.1) 找出常用的传递依赖
    执行 mvn clean dependency:tree -Dverbose, 遍历依赖树，如果某个依赖出现次数不低于给定的一个值，则输出该依赖及其依赖路径

(1.2) 添加未声明的依赖
    执行 mvn clean dependency:analyze 找出 used undeclared dependencies (被显示使用但是没有声明的依赖)，并将这些依赖在pom.xml中声明。此方法会改变pom.xml，同时会删除pom.xml的所有注释
    如果 jar A 的里的类 ClassA 被 import 了，maven 就会认为 jar A 是 used dependency。
    所以要在 IDE 中自动删除没用的 import，避免引入不需要的依赖

(1.3) 找出大的二级依赖
    执行 mvn clean dependency:tree -Dverbose, 遍历依赖树，如果某个2级依赖子树包含的节点不低于给定值，将输出该二级依赖


(2) Command Line Arguments

usage: AnalyzeDependency.py [-h] [-au] [-fd] [-fc FINDCOMMON] [-fh FINDHEAVY] pom

positional arguments:
  pom                   the path of pom file

optional arguments:
  -h, --help            show this help message and exit
  -fc FINDCOMMON, --findcommon FINDCOMMON #(1.1)
                       find all dependencies appearing more than a given number
 -au, --addundeclared #(1.2)
                       add used and undeclared dependencies
 -fh FINDHEAVY, --findheavy FINDHEAVY #(1.3)
                       find all heavy transitive dependencies with children
                       more than a given number
 -fd, --findduplicate  #(1.4)
                       find all dependencies if they have different versions
                       or they appear more than oncef



(3) Example

(3.1) 找出常用的依赖(1.1)
    ./AnalyzeDependency.py ~/boss-operations/pom.xml -fc 5

    Output:
    [INFO]----------Commonly used dependencies Found----------
    com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> log4j:log4j:1.2.14
    [INFO]----------------------------------------------------------------------
    依赖“log4j:log4j:1.2.14”至少出现了5次

(3.2) 添加未声明的依赖(1.2)
    ./AnalyzeDependency.py ~/boss-operations/pom.xml -au

    Output:
    [INFO]----------Adding Used undeclared dependencies----------
    com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.ning:async-http-client:1.7.14
    [INFO]----------------------------------------------------------------------
    把依赖“com.ning:async-http-client:1.7.14”在pom.xml中声明

(3.3) 找出大的二级依赖(1.3)
    ./AnalyzeDependency.py ~/boss-operations/pom.xml -fh 5

    Output:
    [INFO]----------Heavy Level 2 Dependencies Found----------
    com.xiaomi:miuicloud-common:1.0-SNAPSHOT
    [INFO]----------------------------------------------------------------------
    二级依赖“com.xiaomi:miuicloud-common:1.0-SNAPSHOT”至少有5个孩子节点



-----------------------------------
TraverseJar.py
-----------------------------------

(1) Strategy

(1.1) 找出重复的类 
    执行 mvn clean dependency:tree，遍历依赖树上所有的jar包，找出重复的类。

(1.2) 根据类名找jar包
    执行 mvn clean dependency:tree，遍历依赖树上所有的jar包，若jar包包含该类，则输出该jar包。
    (1.1)和(1.2)都只扫描本地仓库的jar包，忽略掉jdk和scope为system的jar包。

(1.3) 找出有重复版本或者有版本冲突的依赖
    执行 mvn clean dependency:tree -Dverbose, 遍历依赖树，找出有重复版本或者有版本冲突的依赖，输出打包时选择的依赖以及被忽略的依赖，以及他们的传递路径。


(2) Command Line Arguments

usage: TraverseJar.py [-h] [-dc] [-dj] [-fj FINDJAR] pom

positional arguments:
  pom                   the path of pom file

optional arguments:
  -h, --help            show this help message and exit
  -dc, --duplicateclass  #(1.1)
                        find all found duplicate classes
  -fj FINDJAR, --findjar FINDJAR  #(1.2)
                        given a class name, find all jars containing it
  -dj, --duplicatejar  #(1.3)
                        find all jars if they have different versions or they
                        repeat the same version


(3) Example

(3.1) 找出重复的类 (1.1)
    ./TraverseJar.py ~/boss-operations/pom.xml -dc

    Output:
    "org.springframework.web.context.request.RequestContextListener" found in ['spring-2.5.6.SEC01.jar', 'spring-web-2.5.6.SEC01.jar']

(3.2) 根据类名找jar包 (1.2)
给定的类名可以带包名，也可以不带包名，两种情况的输出结果可能不同。

(3.2.1) 类不带包名
    ./TraverseJar.py ~/boss-operations/pom.xml -fj RequestContextListener

    Output:
    "RequestContextListener" found in {'org.springframework.web.context.request.RequestContextListener': ['spring-2.5.6.SEC01.jar', 'spring-web-2.5.6.SEC01.jar']}
    -------------------------------------------------------
    com.xiaomi.miliao:miliao-serviceapi:1.0.8 --> org.springframework:spring:2.5.6.SEC01
    com.xiaomi.miliao:miliao-serviceapi:1.0.8 --> org.springframework:spring-webmvc:2.5.6.SEC01 --> org.springframework:spring-web:2.5.6.SEC01

    ~/mavenTool$ ./TraverseJar.py ~/boss-operations/pom.xml -fj Grammar

    "Grammar" found in {'antlr.Grammar': ['antlr-2.7.2.jar'], 'org.apache.xerces.xni.grammars.Grammar': ['xercesImpl-2.9.1.jar'], 'antlr.preprocessor.Grammar': ['antlr-2.7.2.jar']}
    -------------------------------------------------------
    com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.xiaomi:passport-service-api:0.0.26-SNAPSHOT --> org.apache.struts:struts-taglib:1.3.10 --> org.apache.struts:struts-core:1.3.10 --> antlr:antlr:2.7.2
    com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.xiaomi:passport-service-api:0.0.26-SNAPSHOT --> xerces:xercesImpl:2.9.1
    com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.xiaomi:passport-service-api:0.0.26-SNAPSHOT --> org.apache.struts:struts-taglib:1.3.10 --> org.apache.struts:struts-core:1.3.10 --> antlr:antlr:2.7.2



(3.2.2) 类带了包名 (1.3)
    ./TraverseJar.py ~/boss-operations/pom.xml -fj org.springframework.web.context.request.RequestContextListener

    Output:
    "org.springframework.web.context.request.RequestContextListener" found in ['spring-2.5.6.SEC01.jar', 'spring-web-2.5.6.SEC01.jar']
    com.xiaomi.miliao:miliao-serviceapi:1.0.8 --> org.springframework:spring:2.5.6.SEC01
    com.xiaomi.miliao:miliao-serviceapi:1.0.8 --> org.springframework:spring-webmvc:2.5.6.SEC01 --> org.springframework:spring-web:2.5.6.SEC01

(3.3) 找出有重复版本或者有版本冲突的依赖
    ./TraverseJar.py ~/boss-operations/pom.xml -fd

    Output:
    [INFO]----------Duplicated Jars Found----------
    com.xiaomi:xiaomi-common-logger:2.6.26 --> org.apache.thrift:thrift:0.5.0-fix-thrift1190  
    ---------------Omitted versions---------------- 
    com.xiaomi.telecom.cdr:cdr-common:0.0.1-SNAPSHOT --> com.xiaomi:xiaomi-common-thrift:2.5.6 --> com.xiaomi:xiaomi-thrift-shared:2.0.3 --> org.apache.thrift:thrift:0.5.0
    ----------------------------------------------------------------------
    [INFO]----------------------------------------------------------------------

    打包选择的版本为“org.apache.thrift:thrift:0.5.0-fix-thrift1190”，被忽略的为“org.apache.thrift:thrift:0.5.0”






-------------------------------------------------------------------------
TreeBuilder.py / Node.py / Tree.py / TreeParser.py
-------------------------------------------------------------------------
解析 mvn dependency:tree 输出的txt文本，并生成一棵依赖树