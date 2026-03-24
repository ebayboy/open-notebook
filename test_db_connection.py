#!/usr/bin/env python3
"""
测试数据库连接
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from open_notebook.database.repository import repo_query


async def test_db_connection():
    """测试数据库连接"""
    print("测试数据库连接...")

    try:
        # 测试简单查询
        result = await repo_query("SELECT * FROM source LIMIT 5")
        print(f"数据库连接成功，找到 {len(result)} 个源")

        # 检查源内容
        sources = await repo_query(
            "SELECT id, title, full_text FROM source WHERE full_text CONTAINS $keyword",
            {"keyword": "安全"},
        )
        print(f"找到 {len(sources)} 个源包含关键字 '安全'")

        # 显示前几个结果
        for source in sources[:3]:
            print(f"  - ID: {source['id']}, 标题: {source['title']}")
            if source["full_text"] and "安全" in source["full_text"]:
                index = source["full_text"].find("安全")
                start = max(0, index - 50)
                end = min(len(source["full_text"]), index + 10)
                context = source["full_text"][start:end]
                print(f"    上下文: ...{context}...")

        # 检查嵌入块
        chunks = await repo_query(
            "SELECT id, content FROM chunk WHERE content CONTAINS $keyword",
            {"keyword": "安全"},
        )
        print(f"找到 {len(chunks)} 个嵌入块包含关键字 '安全'")

        # 检查是否有嵌入向量
        embeddings = await repo_query(
            "SELECT id, content FROM chunk WHERE content != '' LIMIT 10"
        )
        print(f"找到 {len(embeddings)} 个嵌入块")

        # 显示前几个嵌入块内容
        for chunk in embeddings[:3]:
            print(f"  - ID: {chunk['id']}")
            print(f"    内容预览: {chunk['content'][:100]}...")

        # 查询数据库中的所有表
        print("\n查询数据库中的表...")
        try:
            db_info = await repo_query("INFO FOR DB")

            if db_info:
                # SurrealDB 返回的格式可能不同，我们需要提取表名
                print(f"原始查询结果: {db_info}")

                # 尝试从不同的可能格式中提取表名
                table_names = []

                # 情况1: 结果是一个包含字典的列表
                if isinstance(db_info, list) and len(db_info) > 0:
                    first_item = db_info[0]
                    if isinstance(first_item, dict):
                        # 检查是否有 'tables' 或 'tb' 键
                        if "tables" in first_item:
                            table_names = list(first_item["tables"].keys())
                        elif "tb" in first_item:
                            table_names = list(first_item["tb"].keys())
                        else:
                            # 直接查看字典中的键
                            table_names = list(first_item.keys())

                # 情况2: 结果直接是一个字典
                elif isinstance(db_info, dict):
                    if "tables" in db_info:
                        table_names = list(db_info["tables"].keys())
                    elif "tb" in db_info:
                        table_names = list(db_info["tb"].keys())
                    else:
                        # 直接查看字典中的键
                        table_names = list(db_info.keys())

                # 情况3: 结果是一个列表，其中包含表名
                elif isinstance(db_info, list):
                    # 假设列表中的每个元素是表名
                    table_names = [str(item) for item in db_info if item]

                # 过滤掉非表名的键
                filtered_table_names = []
                for name in table_names:
                    # 排除看起来像系统键的名称
                    if not name.startswith("_") and name not in [
                        "result",
                        "status",
                        "time",
                    ]:
                        filtered_table_names.append(name)

                print(f"数据库中共有 {len(filtered_table_names)} 张表：")
                for table_name in sorted(filtered_table_names):
                    print(f"  - {table_name}")

                    # 尝试获取表信息
                    try:
                        table_info = await repo_query(f"INFO FOR TABLE {table_name}")
                        if table_info:
                            print(f"    表信息: {table_info}")
                    except Exception as e:
                        print(f"    无法获取表信息: {e}")
            else:
                print("无法获取数据库信息")
        except Exception as e:
            print(f"查询表信息时出错: {e}")

            # 尝试使用另一种方法查询表
            try:
                print("尝试使用替代方法查询表...")
                # 尝试查询一些已知的表是否存在
                known_tables = [
                    "source",
                    "source_insight",
                    "source_embedding",
                    "chunk",
                    "notebook",
                    "note",
                ]
                existing_tables = []

                for table in known_tables:
                    try:
                        result = await repo_query(f"SELECT * FROM {table} LIMIT 1")
                        if result is not None:
                            existing_tables.append(table)
                    except Exception:
                        # 表不存在或查询失败
                        pass

                if existing_tables:
                    print(f"发现 {len(existing_tables)} 张表：")
                    for table in existing_tables:
                        print(f"  - {table}")
                else:
                    print("未找到任何表")
            except Exception as e2:
                print(f"替代方法也失败: {e2}")

    except Exception as e:
        print(f"数据库连接失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_db_connection())
