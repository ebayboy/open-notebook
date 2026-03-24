#!/usr/bin/env python3
"""
诊断脚本：检查源的状态并提供详细的错误信息
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from open_notebook.domain.notebook import Source
from open_notebook.database.repository import repo_query
from surreal_commands import get_command_status
from loguru import logger


async def diagnose_source(source_id: str):
    """诊断指定源的状态"""
    print(f"\n=== 诊断源: {source_id} ===\n")

    # 获取源对象
    source = await Source.get(source_id)
    if not source:
        print(f"❌ 源 {source_id} 不存在")
        return

    print(f"📄 源标题: {source.title or '未设置'}")
    print(f"📝 文本内容长度: {len(source.full_text) if source.full_text else 0} 字符")

    if source.full_text:
        # 显示文本内容预览
        preview = (
            source.full_text[:200] + "..."
            if len(source.full_text) > 200
            else source.full_text
        )
        print(f"📝 文本预览: {preview}")
    else:
        print("📝 文本内容: None (空)")

    # 检查资产信息
    if source.asset:
        print(f"📁 文件路径: {source.asset.file_path or '无'}")
        print(f"🔗 URL: {source.asset.url or '无'}")
    else:
        print("📁 资产信息: 无")

    # 检查命令状态
    if source.command:
        print(f"⚙️  命令ID: {source.command}")
        try:
            status = await source.get_status()
            print(f"📊 处理状态: {status}")

            processing_info = await source.get_processing_progress()
            if processing_info:
                print(f"⏱️  开始时间: {processing_info.get('started_at', '未知')}")
                print(f"✅ 完成时间: {processing_info.get('completed_at', '未知')}")
                if processing_info.get("error"):
                    print(f"❌ 错误信息: {processing_info['error']}")
        except Exception as e:
            print(f"⚠️  无法获取命令状态: {e}")
    else:
        print("⚙️  命令信息: 无 (可能是旧版源)")

    # 检查嵌入状态
    try:
        embedded_chunks = await source.get_embedded_chunks()
        print(f"📊 已嵌入块数: {embedded_chunks}")
    except Exception as e:
        print(f"⚠️  无法获取嵌入状态: {e}")

    # 检查关联的笔记本
    try:
        notebooks_query = await repo_query(
            "SELECT VALUE out FROM reference WHERE in = $source_id",
            {"source_id": source.id},
        )
        notebook_ids = (
            [str(nb_id) for nb_id in notebooks_query] if notebooks_query else []
        )
        print(f"📚 关联笔记本: {len(notebook_ids)} 个")
        for nb_id in notebook_ids[:3]:  # 显示前3个
            print(f"   - {nb_id}")
        if len(notebook_ids) > 3:
            print(f"   ... 还有 {len(notebook_ids) - 3} 个")
    except Exception as e:
        print(f"⚠️  无法获取笔记本关联: {e}")


async def main():
    if len(sys.argv) < 2:
        print("用法: python diagnose_source.py <source_id>")
        print("示例: python diagnose_source.py source:1umo8rals03hicui1azx")
        return

    source_id = sys.argv[1]
    await diagnose_source(source_id)


if __name__ == "__main__":
    asyncio.run(main())
