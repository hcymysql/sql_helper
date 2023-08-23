# sql_helper - 输入SQL自动判断条件字段是否增加索引

#### 2023-08-22日更新：修复join多表关联后，where条件表达式字段判断不全。重新拉取sql_helper和sql_helper_args覆盖即可。

索引在数据库中非常重要，它可以加快查询速度并提高数据库性能。对于经常被用作查询条件的字段，添加索引可以显著改善查询效率。然而，索引的创建和维护需要考虑多个因素，包括数据量、查询频率、更新频率等。

sql_helper 工具是一个开源项目，其主要功能是自动判断条件字段是否需要增加索引，适用于MySQL5.7/8.0和MariaDB数据库，并且旨在帮助开发人员优化数据库查询性能。通过分析SQL语句，该工具可以检测出哪些条件字段可以考虑添加索引来提高查询效率。

### 工作流程

第一步、通过SQL语法解析器，提炼出表名，别名，关联字段名，条件字段名，排序字段名，分组字段名。

第二步、检查是否有where条件，如没有则给出提示。

第三步、检测到a join b on a.id = b.id（关联查询时），通过查询表结构，检查关联字段是否有索引，如没有给出创建索引提示。

第四步、通过调用Explain执行计划，如果type值是ALL，或者rows大于1000，检查该表（如有别名，找到其对应的原始表名）和where条件字段的数据分布，工具默认会采样10万条数据作为样本，检查Cardinality基数，例如sex性别字段，有男女两个值，如果占比超过半数（50%），则不建议对该字段创建索引。

第五步、检查group by和order by字段（同样的算法），之后与where条件字段合并，组合成联合索引。

第六步、检查这些字段之前是否创建过索引，如果没有给与提示创建，如果之前就有索引，不提示。

    需要注意的是：sql_helper工具假定您的sql语句条件表达式都为and的前提下，提示创建联合索引。
    
    如果是or，sql解析器解析起来会有些困难(sql灵活多变，且不固定，无法用通用的算法组合字段)。
  
    例如where c1 = 1 or c2 = 2
  
    工具会提示(c1,c2)创建一个联合索引，但实际上应该单独对c1和c2创建一个独立索引。
  
    即select ... from t where c1 = 1
    union all
    select ... from t where c2 = 2


### 命令行方式使用 | [web端接口使用](https://github.com/hcymysql/sql_helper/blob/main/web/sql_helper/README.md)
```
shell> chmod 755 sql_helper
shell> ./sql_helper -f test.yaml -q "select * from sbtest1 limit 1;"
或者
shell> sql_helper -f test.yaml -q "select（SQL太长可以直接回车分割）
>  * from sbtest1 limit 10"
```

注：test.yaml为MySQL配置文件，如果SQL里包含反引号，请直接去掉反引号。

--sample参数：默认采样10万条数据（你可以在从库上获取样本数据），根据你的实际情况，适当增加采样数据，比如100-1000万行，这样工具会更精准的判断是否添加索引。

仅支持SELECT查询（主要针对慢日志里的SQL）

![image](https://github.com/hcymysql/sql_helper/assets/19261879/a603a7fd-7163-4c05-a5fd-4e605f02acc5)

![image](https://github.com/hcymysql/sql_helper/assets/19261879/39da7b69-aebb-4c27-ac18-f0abc497064d)

请注意，自动判断是否增加索引只是一个辅助功能，最终的决策还应该根据具体的业务需求和数据库性能优化的考虑来进行。此外，索引的创建和维护需要谨慎操作，需要考虑数据量、查询频率、更新频率等因素，以避免对数据库性能产生负面影响。

工具适用于Centos7 系统
