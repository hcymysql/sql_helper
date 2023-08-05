<?php

$conn = mysqli_connect("127.0.0.1", "admin", "123456", "sql_helper", "3306") or die("数据库链接错误" . mysqli_error());
mysqli_query($conn, "set names utf8");

?>
