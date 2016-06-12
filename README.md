---------------------------------------------
Principles Of Dependency Tree
---------------------------------------------

* 根节点作为0级依赖
* 如果两个依赖版本不同，则认为是不同的依赖
* 除了0级依赖 (根节点) 和一级依赖 (pom中声明的依赖)，其他都认为是传递依赖

-----------------------------------
AnalyzeDependency.py
-----------------------------------

* Strategy

	* 找出常用的传递依赖
    执行 `mvn clean dependency:tree -Dverbose`, 遍历依赖树，如果某个依赖出现次数不低于给定的一个值，则输出该依赖及其依赖路径

    * 添加未声明的依赖
    执行 `mvn clean dependency:analyze` 找出 used undeclared dependencies (被使用但是没有声明的依赖)，并将这些依赖在pom.xml中声明。此方法会改变pom.xml，同时会删除pom.xml的所有注释
    	  如果 jar A 的里的类 ClassA 被 import 了，maven 就会认为 jar A 是 used dependency。所以要在 IDE 中自动删除没用的 import，避免引入不需要的依赖

    * 找出大的二级依赖
    执行 `mvn clean dependency:tree -Dverbose`, 遍历依赖树，如果某个2级依赖子树包含的节点不低于给定值，将该二级依赖输出


* Command Line Arguments

    usage: AnalyzeDependency.py [-h] [-au] [-fd] [-fc FINDCOMMON] [-fh FINDHEAVY] pom

    positional arguments:
      pom                   the path of pom file

    optional arguments:
      -h, --help            show this help message and exit
      -fc FINDCOMMON, --findcommon FINDCOMMON
                           find all dependencies appearing more than a given number
      -au, --addundeclared
                           add used and undeclared dependencies
      -fh FINDHEAVY, --findheavy FINDHEAVY
                           find all heavy transitive dependencies with children
                           more than a given number
      -of OUTPUTFILE, --outputfile OUTPUTFILE
                           output the result to file


* Example

	* 找出常用的依赖，结果输出到~/boss-operations/result.txt
    `./AnalyzeDependency.py ~/boss-operations/pom.xml -fc 5 -of result.txt`

          Output:
          [INFO]----------Commonly used dependencies Found----------
          com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> log4j:log4j:1.2.14
          [INFO]----------------------------------------------------------------------
          依赖“log4j:log4j:1.2.14”至少出现了5次

	* 添加未声明的依赖
    `./AnalyzeDependency.py ~/boss-operations/pom.xml -au`

          Output:
          [INFO]----------Adding Used undeclared dependencies----------
          com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.ning:async-http-client:1.7.14
          [INFO]----------------------------------------------------------------------
          把依赖“com.ning:async-http-client:1.7.14”在pom.xml中声明

	* 找出大的二级依赖
    `./AnalyzeDependency.py ~/boss-operations/pom.xml -fh 5`

          Output:
          [INFO]----------Heavy Level 2 Dependencies Found----------
          com.xiaomi:miuicloud-common:1.0-SNAPSHOT
          [INFO]----------------------------------------------------------------------
          二级依赖“com.xiaomi:miuicloud-common:1.0-SNAPSHOT”至少有5个孩子节点


-----------
diff.py
-----------

此程序可以判断当添加某一个依赖后，新添加的依赖引入的依赖有哪些，以及整个项目是否有依赖的版本发生了改变。

* Strategy
    * 根据调用时传入的参数`branch`或者`version`，从仓库中选择一个 pom.xml 作为基准
        * `git fetch origin <branch> or <commitID>`，取回 branch 或 commitID 对应的更新
        * `git checkout FETCH_HEAD -- pom.xml`，从取回的更新`FETCH_HEAD`中恢复特定的文件`pom.xml`
    * 如果同时指定`branch`和`version`，仅考虑`version`所对应的 pom.xml
    * 如果没有指定`branch`和`version`，则默认是`master`分支最新的 pom.xml（可能有其他开发者有新的push），因此建议指定`version`
    * 比较本地 pom.xml 的依赖树和从 仓库选择的 pom.xml 的依赖树，找出是否有传递依赖的版本发生变化或者本地 pom.xml 的依赖树新增了依赖
     	 `--`是为了告诉git，`pom.xml`是一个文件，如`pom.xml`和某一个分支同名，则会引起git混淆，用`--`可以避免这个问题。

* Command Line Arguments

    usage: diff.py [-h] [-b BRANCH] [-v VERSION] [-of OUTPUTFILE] pom

    positional arguments:
      pom                   the path of pom.xml

    optional arguments:
      -h, --help            show this help message and exit
      -b BRANCH, --branch BRANCH
                            select a branch. Default branch is master
      -v VERSION, --version VERSION
                            select a version number. The branch will be ignored
                            even if branch is given
      -of OUTPUTFILE, --outputfile OUTPUTFILE
                            output the result to file


* Example

	* `./diff.py ~/boss-operations/pom.xml -of result.txt`
	比较本地pom.xml 和 master 分支下最新的pom.xml，结果输出到~/boss-operations/result.txt

	* `./diff.py ~/boss-operations/pom.xml -b maven-dev`
	比较本地pom.xml 和 maven-dev 分支下最新的pom.xml

	* `./diff.py ~/boss-operations/pom.xml -v 434082306750c215a26044bcdc165c740ddfa6be`
	比较本地pom.xml 和 434082306750c215a26044bcdc165c740ddfa6be 对应的pom.xml

* Output Example

      * branch            7904b625d7ef7e2f36d28629bfdff1178303b462 -> FETCH_HEAD
      [INFO]-----------------Version changed dependencies Found-----------------
      "javax.servlet.jsp:jsp-api:jar:2.1:compile" --> "javax.servlet.jsp:jsp-api:jar:2.1:runtime" UNDER "com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT"

      "org.apache.zookeeper:zookeeper:3.4.4-mdh1.0.2" --> "org.apache.zookeeper:zookeeper:3.4.4-mdh1.0.3" UNDER "com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT"

      [INFO]-----------------------------------------------------------------------------

      [INFO]-----------------New dependencies Found-----------------
      com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:xiaomi-common-zookeeper:2.5.8 --> org.apache.zookeeper:zookeeper:3.4.4-mdh1.0.3 --> jline:jline:0.9.94

      [INFO]-----------------------------------------------------------------------------

	`\* branch            7904b625d7ef7e2f36d28629bfdff1178303b462 -> FETCH_HEAD`
 	表示将采用 commitID 为 7904b625d7ef7e2f36d28629bfdff1178303b462 的 pom.xml 作为比较基准

	`"org.apache.zookeeper:zookeeper:3.4.4-mdh1.0.2" --> "org.apache.zookeeper:zookeeper:3.4.4-mdh1.0.3"`
    表示仓库的项目依赖 "org.apache.zookeeper:zookeeper:3.4.4-mdh1.0.2" 在修改了pom.xml 之后变成 "org.apache.zookeeper:zookeeper:3.4.4-mdh1.0.3"

    `UNDER "com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT"`
    表示改变的依赖在一级依赖 "com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT" 下


-----------------------------------
TraverseJar.py
-----------------------------------

* Strategy

    * 找出重复的类
        执行 `mvn clean dependency:tree`，遍历依赖树上所有的jar包，找出重复的类。

    * 根据类名找jar包
        执行 `mvn clean dependency:tree`，遍历依赖树上所有的jar包，若jar包包含该类，则输出该jar包。

          以上都只扫描本地仓库的jar包，忽略掉jdk和scope为system的jar包。

    * 找出有重复版本或者有版本冲突的依赖
        执行 `mvn clean dependency:tree -Dverbose`，遍历依赖树，找出有重复版本或者有版本冲突的依赖，输出打包时选择的依赖以及被忽略的依赖，以及他们的传递路径。


* Command Line Arguments

    usage: TraverseJar.py [-h] [-dc] [-dj] [-fj FINDJAR] pom

    positional arguments:
      pom                   the path of pom file

    optional arguments:
      -h, --help            show this help message and exit
      -dc, --duplicateclass
                            find all found duplicate classes
      -fj FINDJAR, --findjar FINDJAR
                            given a class name, find all jars containing it
      -dj, --duplicatejar
                            find all jars if they have different versions or they
                            repeat the same version
      -of OUTPUTFILE, --outputfile OUTPUTFILE
                            output the result to file


* Example

	* `./TraverseJar.py ~/boss-operations/pom.xml -dc -of result.txt`
	找出重复的类，结果输出到~/boss-operations/result.txt

    	  Output:
    	  "org.springframework.web.context.request.RequestContextListener" found in ['spring-2.5.6.SEC01.jar', 'spring-web-2.5.6.SEC01.jar']

	* 根据类名找jar包，并输出该jar包的传递路径
	给定的类名可以带包名，也可以不带包名，两种情况的输出结果可能不同。

		* 类不带包名，则输出该类所有的路径
    	`./TraverseJar.py ~/boss-operations/pom.xml -fj Grammar`

              Output:
              "Grammar" found in {'antlr.Grammar': ['antlr-2.7.2.jar'], 'org.apache.xerces.xni.grammars.Grammar': ['xercesImpl-2.9.1.jar'], 'antlr.preprocessor.Grammar': ['antlr-2.7.2.jar']}
              -------------------------------------------------------
              com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.xiaomi:passport-service-api:0.0.26-SNAPSHOT --> org.apache.struts:struts-taglib:1.3.10 --> org.apache.struts:struts-core:1.3.10 --> antlr:antlr:2.7.2

              com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.xiaomi:passport-service-api:0.0.26-SNAPSHOT --> xerces:xercesImpl:2.9.1

              com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.xiaomi:passport-service-api:0.0.26-SNAPSHOT --> org.apache.struts:struts-taglib:1.3.10 --> org.apache.struts:struts-core:1.3.10 --> antlr:antlr:2.7.2
		包含类`Grammar`的引用路径有`antlr.Grammar`，`org.apache.xerces.xni.grammars.Grammar`和`antlr.preprocessor.Grammar`，其中`antlr.Grammar`在 antlr-2.7.2.jar 中，传递路径为
        	  com.xiaomi.telecom.boss:boss-common:1.0.0-SNAPSHOT --> com.xiaomi:miuicloud-common:1.0-SNAPSHOT --> com.xiaomi:passport-service-api:0.0.26-SNAPSHOT --> org.apache.struts:struts-taglib:1.3.10 --> org.apache.struts:struts-core:1.3.10 --> antlr:antlr:2.7.2

		* 类带了包名
    	`./TraverseJar.py ~/boss-operations/pom.xml -fj org.springframework.web.context.request.RequestContextListener`

              Output:
              "org.springframework.web.context.request.RequestContextListener" found in ['spring-2.5.6.SEC01.jar', 'spring-web-2.5.6.SEC01.jar']
              -------------------------------------------------------
              com.xiaomi.miliao:miliao-serviceapi:1.0.8 --> org.springframework:spring:2.5.6.SEC01
              com.xiaomi.miliao:miliao-serviceapi:1.0.8 --> org.springframework:spring-webmvc:2.5.6.SEC01 --> org.springframework:spring-web:2.5.6.SEC01

	* 找出有重复版本或者有版本冲突的依赖
    `./TraverseJar.py ~/boss-operations/pom.xml -fd`

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