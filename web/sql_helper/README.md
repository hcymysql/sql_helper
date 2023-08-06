### sql_helper Web端接口

一、环境搭建

```
shell> yum install httpd php php-mysqlnd
shell> systemctl restart httpd.service
```

1） 把 https://github.com/hcymysql/sql_helper/archive/refs/heads/main.zip 安装包解压缩到 /var/www/html/目录下

目录结构如下：
```
sql_helper
├── conn.php
├── css
│   └── bootstrap.min.css
├── schema
│   └── sql_helper_schema.sql
├── sql_helper_args
├── sql_helper.php
└── sql_helper_result.php
```

2）赋予sql_helper_args文件可执行权限
```
shell> cd /var/www/html/sql_helper/
shell> chmod 755 sql_helper_args
```

二、sql_helper 网页端部署

1）导入sql_helper工具表结构
```
shell> mysql -uroot -p123456 < ./schema/sql_helper_schema.sql
```

2）录入你线上的数据库信息（你可以填写从库信息）
```
mysql> insert into sql_helper.dbinfo values(1,'192.168.0.11','test','admin','123456',3306);
```

3）配置conn.php文件

-- 改成你的sql_helper库连接信息

4）页面访问

http://yourIP/sql_helper/sql_helper.php

加一个超链接，可方便地接入你们的自动化运维平台里。





