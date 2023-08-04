def has_table_alias(table_alias):
    if isinstance(table_alias, dict):
        table_alias = {k.lower(): v.lower() for k, v in table_alias.items()}
        if 'join' in table_alias or 'on' in table_alias or 'where' in table_alias or 'group by' in table_alias or 'order by' in table_alias or 'limit' in table_alias or not table_alias:
           return False # 没有别名
        else:
           return True #有别名
    elif isinstance(table_alias, list):
        return False # 没有别名
    else:
        pass
