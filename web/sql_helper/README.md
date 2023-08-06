### sql_helper Web端接口 - 加一个超链接，可方便地接入你们的自动化运维平台里。

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
├── sql_helper_args
├── sql_helper.php
└── sql_helper_result.php
```

```
shell> cd /var/www/html/sql_helper/
shell> chmod 755 sql_helper_args
```

2）
