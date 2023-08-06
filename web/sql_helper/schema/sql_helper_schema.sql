CREATE DATABASE `sql_helper`;

USE `sql_helper`;

DROP TABLE IF EXISTS `dbinfo`;

CREATE TABLE `dbinfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ip` varchar(100) DEFAULT NULL,
  `dbname` varchar(100) DEFAULT NULL,
  `user` varbinary(500) DEFAULT NULL,
  `pwd` varbinary(500) DEFAULT NULL,
  `port` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY dbname (`dbname`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
