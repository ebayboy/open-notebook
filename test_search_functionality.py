#!/usr/bin/env python3
"""
测试搜索功能
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
from open_notebook.domain.notebook import text_search, vector_search
from open_notebook.utils.embedding import generate_embedding


async def test_search_functionality():
    """测试搜索功能"""
    print("=== 测试搜索功能 ===\n")

    try:
        # 1. 检查数据库中的内容
        print("1. 检查数据库内容...")

        # 检查源内容
        sources = await repo_query(
            "SELECT id, title, full_text FROM source WHERE full_text CONTAINS $keyword",
            {"keyword": "安全"},
        )
        print(f"   找到 {len(sources)} 个源包含关键字 '安全'")

        # 显示前几个结果
        for source in sources[:3]:
            print(f"   - ID: {source['id']}, 标题: {source['title']}")
            if source["full_text"] and "安全" in source["full_text"]:
                index = source["full_text"].find("安全")
                start = max(0, index - 50)
                end = min(len(source["full_text"]), index + 10)
                context = source["full_text"][start:end]
                print(f"     上下文: ...{context}...")

        # 检查嵌入块
        chunks = await repo_query(
            "SELECT id, content FROM chunk WHERE content CONTAINS $keyword",
            {"keyword": "安全"},
        )
        print(f"   找到 {len(chunks)} 个嵌入块包含关键字 '安全'")

        # 检查是否有嵌入向量
        embeddings = await repo_query(
            "SELECT id, content FROM chunk WHERE content != '' LIMIT 10"
        )
        print(f"   找到 {len(embeddings)} 个嵌入块")

        # 2. 测试文本搜索
        print("\n2. 测试文本搜索...")
        try:
            text_results = await text_search("安全", 10, True, True)
            print(f"   文本搜索结果: {len(text_results)} 个")
            for result in text_results[:3]:
                print(
                    f"   - ID: {result.get('id', 'N/A')}, 标题: {result.get('title', 'N/A')}"
                )
        except Exception as e:
            print(f"   文本搜索失败: {e}")

        # 3. 测试向量搜索
        print("\n3. 测试向量搜索...")
        try:
            embed = await generate_embedding("安全")
            vector_results = await vector_search("安全", 10, True, True, 0.2)
            print(f"   向量搜索结果: {len(vector_results)} 个")
            for result in vector_results[:3]:
                print(
                    f"   - ID: {result.get('id', 'N/A')}, 标题: {result.get('title', 'N/A')}"
                )
        except Exception as e:
            print(f"   向量搜索失败: {e}")

        # 4. 检查数据库函数是否存在
        print("\n4. 检查数据库函数...")
        try:
            # 检查文本搜索函数
            text_func_results = await repo_query(
                "SELECT * FROM fn::text_search($keyword, 10, true, true)",
                {"keyword": "安全"},
            )
            print(f"   文本搜索函数结果: {len(text_func_results)} 个")

            # 检查向量搜索函数
            embed = await generate_embedding("安全")
            vector_func_results = await repo_query(
                "SELECT * FROM fn::vector_search($embed, 10, true, true, 0.2)",
                {"embed": embed},
            )
            print(f"   向量搜索函数结果: {len(vector_func_results)} 个")
        except Exception as e:
            print(f"   数据库函数测试失败: {e}")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_search_functionality())
