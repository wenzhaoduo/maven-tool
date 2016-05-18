---------------------------------------------
Principles Of Dependency Tree
---------------------------------------------

(1) 根节点作为0级依赖
(2) 构建依赖树的时候，忽略掉omitted dependencies
(3) 如果两个依赖版本不同，则认为是不同的依赖
(4) 除了0级依赖 (根节点) 和一级依赖 (pom中声明的依赖)，其他都认为是传递依赖


-----------
diff.py
-----------

(1) Strategy

step1
根据调用时传入的参数 branch 或者 version，从 git.n.xiaomi.com 上选择一个 pom.xml 作为基准
如果同时指定 branch 和 version，仅考虑 version 所对应的pom.xml
如果没有指定 branch，则默认是 master 上最新的 pom.xml

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
[WARNING] Changed dependency: "org.codehaus.plexus:plexus-utils:jar:2.0.5:compile" --> "org.codehaus.plexus:plexus-utils:jar:1.4.1:compile" UNDER "org.apache.maven:maven-artifact:jar:2.0.6:compile"
[INFO]-----------------------------------------------------------------------------

[INFO]-----------------New dependencies-----------------
[INFO] New dependency: "com.xiaomi.infra:scribe-log4j:jar:1.0.0-SNAPSHOT:compile" UNDER "org.apache.hbase:hbase:jar:0.94.11-mdh1.2.5:compile"
[INFO]-----------------------------------------------------------------------------

 * branch            maven-dev  -> FETCH_HEAD
 表示将采用 maven-dev 分支下最新的 pom.xml 作为比较基准

Changed dependency: "commons-digester:commons-digester:jar:1.8:compile" --> "commons-digester:commons-digester:jar:1.6:compile" 
表示依赖 "commons-digester:commons-digester:jar:1.8:compile" 有新版本 "commons-digester:commons-digester:jar:1.6:compile"

UNDER "com.xiaomi:xiaomi-common-logger:jar:2.6.26:compile"
表示在一级依赖 "com.xiaomi:xiaomi-common-logger:jar:2.6.26:compile" 下


-----------------------------------
AnalyzeDependency.py
-----------------------------------

(1) Strategy

主要有3个方法，可分开调用，每次指定调用至少一个方法。每个方法都可能改变pom.xml，同时会删除pom.xml的所有注释

(1.1) 添加常用的传递依赖
    执行 maven dependency:tree -Dverbose, 遍历依赖树，如果某个依赖出现次数不低于5次，将在pom.xml中声明该依赖

(1.2) 添加未声明的依赖
    执行 maven dependency:analyze 找出 used undeclared dependencies (被显示使用但是没有声明的依赖)，并将这些依赖在pom.xml中声明
    如果 jar A 的里的类 ClassA 在 import 了，maven 就会认为 jar A 是 used dependency。
    所以要在 IDE 中自动删除没用的 import，避免引入不需要的依赖

(1.3) 排除大的二级依赖
    执行 maven dependency:tree -Dverbose, 遍历依赖树，如果某个2级依赖子树有不低于5个节点，在pom.xml中exclude该依赖
    每一次exclude之后都会执行mvn clean compile，如果compile失败，就不会exclude该依赖
    这个功能可能会 exclude 运行时需要用的dependency，需慎用

(2) Command Line Arguments

usage: AnalyzeDependency.py [-h] [-addcommon] [-addundeclared] [-exclude] path

positional arguments:
  pom			the path of pom file

optional arguments:
  -h, --help		show this help message and exit
  -addcommon		add common dependencies
  -addundeclared	add used and undeclared dependencies
  -exclude		exclude heavy transitive dependencies

(3) Example

分别添加常用的依赖(1.1)，添加未声明的依赖(1.2)，排除大的二级依赖(1.3)
./AnalyzeDependency.py ~/boss-operations/pom.xml -addcommon -addundeclared -exclude

(4) Output Example

[INFO]----------Commonly used dependencies----------
org.apache.maven:maven-artifact:2.0.6
[INFO]----------------------------------------------------------------------

[INFO]----------Used undeclared dependencies----------
org.testng:testng:6.8.5
[INFO]----------------------------------------------------------------------

[INFO]----------Excluded Dependencies----------
com.xiaomi:miliao-common:jar:2.0.1:compile
[INFO]----------------------------------------------------------------------


-------------------------------------------------------------------------
TreeBuilder.py / Node.py / Tree.py / TreeParser.py
-------------------------------------------------------------------------
解析 mvn dependency:tree 输出的txt文本，并生成一棵依赖树