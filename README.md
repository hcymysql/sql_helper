# sql_helper
输入SQL自动判断条件字段是否增加索引

使用：
```
shell> chmod 755 sql_helper
shell> ./sql_helper -f test.yaml -q 'select * from sbtest1 limit 1;'
```

注：test.yaml为MySQL配置文件

--sample参数：默认采样10万条数据（你可以在从库上获取样本数据），根据你的实际情况，适当增加采样数据，比如100-1000万行，这样工具会更精准的判断是否添加索引。

仅支持SELECT查询（主要针对慢日志里的SQL）

![image](https://github.com/hcymysql/sql_helper/assets/19261879/937178c0-9cef-47fd-ba4c-05001ac219ad)
