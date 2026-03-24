#!/usr/bin/env python3
"""
调试脚本：检查数据库中是否有包含特定关键字的数据
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from open_notebook.database.repository import repo_query
from loguru import logger


async def check_content_with_keyword(keyword: str):
    """检查数据库中是否包含指定关键字的内容"""
    print(f"\n=== 检查数据库中是否包含关键字: {keyword} ===\n")

    try:
        # 检查源内容
        print("1. 检查源内容...")
        sources = await repo_query(
            "SELECT id, title, full_text FROM source WHERE full_text CONTAINS $keyword",
            {"keyword": keyword},
        )
        print(f"   找到 {len(sources)} 个源包含关键字")
        if sources:
            for source in sources[:3]:  # 显示前3个
                print(f"   - ID: {source['id']}, 标题: {source['title']}")
                if source["full_text"]:
                    # 显示包含关键字的上下文
                    index = source["full_text"].find(keyword)
                    if index >= 0:
                        start = max(0, index - 50)
                        end = min(len(source["full_text"]), index + len(keyword) + 50)
                        context = source["full_text"][start:end]
                        print(f"     上下文: ...{context}...")

        # 检查笔记内容
        print("\n2. 检查笔记内容...")
        notes = await repo_query(
            "SELECT id, title, content FROM note WHERE content CONTAINS $keyword",
            {"keyword": keyword},
        )
        print(f"   找到 {len(notes)} 个笔记包含关键字")
        if notes:
            for note in notes[:3]:  # 显示前3个
                print(f"   - ID: {note['id']}, 标题: {note['title']}")
                if note["content"]:
                    # 显示包含关键字的上下文
                    index = note["content"].find(keyword)
                    if index >= 0:
                        start = max(0, index - 50)
                        end = min(len(note["content"]), index + len(keyword) + 50)
                        context = note["content"][start:end]
                        print(f"     上下文: ...{context}...")

        # 检查嵌入块内容
        print("\n3. 检查嵌入块内容...")
        chunks = await repo_query(
            "SELECT id, content FROM chunk WHERE content CONTAINS $keyword",
            {"keyword": keyword},
        )
        print(f"   找到 {len(chunks)} 个嵌入块包含关键字")
        if chunks:
            for chunk in chunks[:3]:  # 显示前3个
                print(f"   - ID: {chunk['id']}")
                if chunk["content"]:
                    # 显示包含关键字的上下文
                    index = chunk["content"].find(keyword)
                    if index >= 0:
                        start = max(0, index - 50)
                        end = min(len(chunk["content"]), index + len(keyword) + 50)
                        context = chunk["content"][start:end]
                        print(f"     上下文: ...{context}...")

        # 检查是否有嵌入向量
        print("\n4. 检查嵌入向量...")
        embeddings = await repo_query(
            "SELECT id, content FROM chunk WHERE content != '' LIMIT 10"
        )
        print(f"   找到 {len(embeddings)} 个嵌入块")
        if embeddings:
            for embedding in embeddings[:3]:  # 显示前3个
                print(f"   - ID: {embedding['id']}")
                print(f"     内容预览: {embedding['content'][:100]}...")

        # 检查文本搜索函数是否存在
        print("\n5. 检查文本搜索函数...")
        try:
            text_results = await repo_query(
                "SELECT * FROM fn::text_search($keyword, 10, true, true)",
                {"keyword": keyword},
            )
            print(f"   文本搜索结果: {len(text_results)} 个")
            if text_results:
                for result in text_results[:3]:  # 显示前3个
                    print(
                        f"   - ID: {result.get('id', 'N/A')}, 标题: {result.get('title', 'N/A')}"
                    )
        except Exception as e:
            print(f"   文本搜索函数调用失败: {e}")

        # 检查向量搜索函数是否存在
        print("\n6. 检查向量搜索函数...")
        try:
            from open_notebook.utils.embedding import generate_embedding

            embed = await generate_embedding(keyword)
            vector_results = await repo_query(
                "SELECT * FROM fn::vector_search($embed, 10, true, true, 0.2)",
                {"embed": embed},
            )
            print(f"   向量搜索结果: {len(vector_results)} 个")
            if vector_results:
                for result in vector_results[:3]:  # 显示前3个
                    print(
                        f"   - ID: {result.get('id', 'N/A')}, 标题: {result.get('title', 'N/A')}"
                    )
        except Exception as e:
            print(f"   向量搜索函数调用失败: {e}")

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        logger.exception(e)


async def main():
    keyword = "安全"
    if len(sys.argv) > 1:
        keyword = sys.argv[1]

    await check_content_with_keyword(keyword)


if __name__ == "__main__":
    asyncio.run(main())
