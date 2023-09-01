<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>SQL自助查询优化</title>
    <meta name="description" content="Ela Admin - HTML5 Admin Template">
    <meta name="viewport" content="width=device-width, initial-scale=1">


<link rel="stylesheet" href="css/bootstrap.min.css">

</head>
<body>

<?php

$get_dbname=$_POST['select_yourdb'];
$get_sql = $_POST['input_yoursql'];
$get_sql = str_replace('`', '', $get_sql);

    if(empty($get_dbname)){
	header("Location:sql_helper.php");
    }

require_once 'conn.php';

$get_db_ip="select ip,dbname,user,pwd,port from dbinfo where dbname='${get_dbname}'";

$result = mysqli_query($conn,$get_db_ip);      

list($ip,$dbname,$user,$pwd,$port) = mysqli_fetch_array($result);

$command = "./sql_helper_args -H $ip -P $port -u $user -p '$pwd' -d $dbname -q \"$get_sql\" --sample 100000";  //采集的数据越多，判断索引是否增加的概率就越高，默认采集10万条数据。

// 调用命令并获取输出结果
$output = shell_exec($command);

echo '<div class="card-header">SQL 查询结果</div>';

// 使用 <pre> 标签将输出保留原始格式
echo '<div class="container">';
echo '<br>';
echo '<pre>' . $output . '</pre>';

echo '<br><h6><a href="javascript:history.back(-1);">点击此处返回</a></h3></br>';
echo '</div>';

echo "</br>";
echo "<hr />";

?>

</body>
</html>
