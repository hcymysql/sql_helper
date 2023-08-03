# sql_helper
输入SQL自动判断条件字段是否增加索引

使用：
```
shell> chmod 755 sql_helper
shell> ./sql_helper -f test.yaml -q 'select * from sbtest1 limit 1;'
```

注：test.yaml为MySQL配置文件
