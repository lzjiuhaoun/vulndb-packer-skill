DROP TABLE IF EXISTS `va_library`;
CREATE TABLE `va_library`  (
  `va_id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `va_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞名称',
  `va_time` datetime(0) NULL DEFAULT NULL COMMENT '漏洞发布时间',
  `db_type` tinyint(2) NOT NULL COMMENT '漏洞数据库类型',
  `va_type` tinyint(1) NOT NULL COMMENT '漏洞类型',
  `va_rule` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞检查规则',
  `va_check_way` tinyint(1) NULL DEFAULT NULL COMMENT '漏洞检查方式 1jdbc查询 2对比版本',
  `va_desc` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞描述',
  `va_sql` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞sql修复语句',
  `va_level` tinyint(1) NOT NULL COMMENT '漏洞级别',
  `va_verify` tinyint(1) NULL DEFAULT NULL COMMENT '漏洞校验方式 1-YES_NO  2-RESULT_SET  3-PROCEDURE 4-UNIX_YES_NO',
  `va_suggest` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞修复建议',
  `va_cve` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞cve号',
  `va_cnnvd` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞cnnvd号',
  `va_db_version` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞影响的DB版本',
  `va_lib_version` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT '' COMMENT '漏洞库版本',
  `public_poc_exp` tinyint(1) NOT NULL DEFAULT 0 COMMENT '此漏洞是否有公开的poc或exp，0代表无，1代表有',
  PRIMARY KEY (`va_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '漏洞库信息表' ROW_FORMAT = Dynamic;
