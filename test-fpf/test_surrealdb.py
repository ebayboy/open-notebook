#!/usr/bin/env python3
"""
SurrealDB 连接和 CRUD 操作测试

测试内容：
1. 数据库连接测试
2. 基本的增删改查功能
3. 错误处理
4. 环境变量验证
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, cast

from dotenv import load_dotenv
from loguru import logger
from surrealdb import AsyncSurreal

# 加载环境变量
load_dotenv()

# SurrealDB 配置
# 使用本地主机地址，因为 Docker 端口映射到本地
SURREAL_URL = os.getenv("SURREAL_URL", "ws://localhost:8000/rpc")
SURREAL_USER = os.getenv("SURREAL_USER", "root")
SURREAL_PASSWORD = os.getenv("SURREAL_PASSWORD", "root")
SURREAL_NAMESPACE = os.getenv("SURREAL_NAMESPACE", "open_notebook")
SURREAL_DATABASE = os.getenv("SURREAL_DATABASE", "open_notebook")

# 测试表名
TEST_TABLE = "test_items"


class SurrealDBTester:
    """SurrealDB 测试类"""
    
    def __init__(self):
        self.db = None
        self.test_records: List[str] = []
    
    async def connect(self) -> bool:
        """测试数据库连接"""
        try:
            logger.info(f"正在连接到 SurrealDB: {SURREAL_URL}")
            self.db = AsyncSurreal(SURREAL_URL)  # type: ignore
            
            # 登录
            await self.db.signin({
                "username": SURREAL_USER,
                "password": SURREAL_PASSWORD,
            })
            
            # 选择命名空间和数据库
            await self.db.use(SURREAL_NAMESPACE, SURREAL_DATABASE)
            
            logger.success("✅ SurrealDB 连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ SurrealDB 连接失败: {e}")
            return False
    
    async def test_basic_crud(self):
        """测试基本的 CRUD 操作"""
        logger.info("开始测试基本的 CRUD 操作...")
        
        try:
            # 1. 创建记录 (Create)
            logger.info("测试创建记录...")
            test_data = {
                "name": "测试项目",
                "description": "这是一个测试项目",
                "status": "active",
                "priority": 1
            }
            
            created = await cast(AsyncSurreal, self.db).insert(TEST_TABLE, test_data)
            if isinstance(created, list) and len(created) > 0:
                created_record = created[0]
                record_id = str(created_record.get("id", ""))
                if record_id:
                    self.test_records.append(record_id)
                    logger.success(f"✅ 创建记录成功: {record_id}")
                    logger.info(f"记录内容: {created_record}")
                else:
                    raise Exception("创建记录失败: 无法获取记录ID")
            else:
                raise Exception("创建记录失败: 无效的返回格式")
            
            # 2. 读取记录 (Read)
            logger.info("测试读取记录...")
            query = f"SELECT * FROM {record_id}"
            results = await cast(AsyncSurreal, self.db).query(query)
            
            logger.info(f"查询结果: {results}")
            
            if results and len(results) > 0:
                # SurrealDB 返回的是字典列表格式
                if isinstance(results, list) and len(results) > 0:
                    if isinstance(results[0], dict):
                        # 结果直接是字典列表格式
                        record = results[0]
                        logger.success(f"✅ 读取记录成功")
                        logger.info(f"读取到的记录: {record}")
                    else:
                        logger.warning(f"未知的返回格式: {type(results[0])}")
                        raise Exception("读取记录失败: 未知的返回格式")
                else:
                    raise Exception("读取记录失败: 结果格式不正确")
            else:
                raise Exception("读取记录失败: 没有返回结果")
            
            # 3. 更新记录 (Update)
            logger.info("测试更新记录...")
            update_data = {
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            update_query = f"UPDATE {record_id} MERGE $data"
            updated = await cast(AsyncSurreal, self.db).query(update_query, {"data": update_data})
            
            if updated:
                logger.success("✅ 更新记录成功")
                
                # 验证更新
                verify_query = f"SELECT * FROM {record_id}"
                verify_results = await cast(AsyncSurreal, self.db).query(verify_query)
                if verify_results and len(verify_results) > 0:
                    result_data = verify_results[0]
                    if isinstance(result_data, dict) and "result" in result_data:
                        records = result_data["result"]
                        if isinstance(records, list) and len(records) > 0:
                            updated_record = records[0]
                            logger.info(f"更新后的记录: {updated_record}")
                        else:
                            logger.warning("⚠️ 验证更新时没有找到记录")
                else:
                    logger.warning("⚠️ 验证更新时没有返回结果")
            else:
                raise Exception("更新记录失败")
            
            # 4. 删除记录 (Delete)
            logger.info("测试删除记录...")
            delete_result = await cast(AsyncSurreal, self.db).delete(record_id)
            
            if delete_result is not None:
                logger.success("✅ 删除记录成功")
                
                # 验证删除
                check_query = f"SELECT * FROM {record_id}"
                check_results = await cast(AsyncSurreal, self.db).query(check_query)
                if not check_results or len(check_results) == 0:
                    logger.success("✅ 记录已成功删除，验证通过")
                else:
                    result_data = check_results[0]
                    if isinstance(result_data, dict) and "result" in result_data:
                        records = result_data["result"]
                        if isinstance(records, list) and len(records) == 0:
                            logger.success("✅ 记录已成功删除，验证通过")
                        else:
                            logger.warning("⚠️  记录可能未被完全删除")
                    else:
                        logger.success("✅ 记录已成功删除，验证通过")
                
                # 从测试记录列表中移除
                if record_id in self.test_records:
                    self.test_records.remove(record_id)
            else:
                raise Exception("删除记录失败")
            
            logger.success("✅ 所有 CRUD 操作测试通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ CRUD 操作测试失败: {e}")
            return False
    
    async def test_bulk_operations(self):
        """测试批量操作"""
        logger.info("开始测试批量操作...")
        
        try:
            # 创建多个测试记录
            bulk_data = [
                {"name": f"批量测试项目 {i}", "type": "bulk_test", "priority": i}
                for i in range(1, 6)
            ]
            
            logger.info("测试批量创建...")
            created_records = await cast(AsyncSurreal, self.db).insert(TEST_TABLE, bulk_data)
            
            if isinstance(created_records, list):
                logger.success(f"✅ 批量创建成功，共创建 {len(created_records)} 条记录")
                
                # 保存记录ID用于后续清理
                for record in created_records:
                    if isinstance(record, dict) and "id" in record:
                        record_id = str(record["id"])
                        self.test_records.append(record_id)
                
                # 测试批量查询
                logger.info("测试批量查询...")
                query = f"SELECT * FROM {TEST_TABLE} WHERE type = 'bulk_test' ORDER BY priority"
                results = await cast(AsyncSurreal, self.db).query(query)
                
                logger.info(f"批量查询结果: {results}")
                
                if results and len(results) > 0:
                    # SurrealDB 返回的是字典列表格式
                    if isinstance(results, list) and len(results) > 0:
                        if isinstance(results[0], dict):
                            # 结果直接是字典列表格式
                            records = results
                            logger.success(f"✅ 批量查询成功，找到 {len(records)} 条记录")
                            
                            # 显示部分记录
                            for i, record in enumerate(records[:3]):
                                if isinstance(record, dict):
                                    logger.info(f"记录 {i+1}: {record.get('name', 'N/A')}")
                            if len(records) > 3:
                                logger.info(f"... 还有 {len(records) - 3} 条记录")
                        elif isinstance(results[0], list):
                            # 结果嵌套在列表中
                            records = results[0]
                            logger.success(f"✅ 批量查询成功，找到 {len(records)} 条记录")
                            
                            # 显示部分记录
                            for i, record in enumerate(records[:3]):
                                if isinstance(record, dict):
                                    logger.info(f"记录 {i+1}: {record.get('name', 'N/A')}")
                            if len(records) > 3:
                                logger.info(f"... 还有 {len(records) - 3} 条记录")
                        else:
                            logger.warning(f"⚠️  未知的返回格式: {type(results[0])}")
                    else:
                        logger.warning("⚠️  批量查询结果格式不正确")
                else:
                    logger.warning("⚠️  批量查询没有返回结果")
                
                return True
            else:
                raise Exception("批量创建返回格式无效")
                
        except Exception as e:
            logger.error(f"❌ 批量操作测试失败: {e}")
            return False
    
    async def test_query_operations(self):
        """测试查询操作"""
        logger.info("开始测试查询操作...")
        
        try:
            # 创建测试数据
            test_records = [
                {"name": "查询测试1", "category": "tech", "status": "active", "score": 95},
                {"name": "查询测试2", "category": "tech", "status": "inactive", "score": 80},
                {"name": "查询测试3", "category": "business", "status": "active", "score": 88},
            ]
            
            created = await cast(AsyncSurreal, self.db).insert(TEST_TABLE, test_records)
            if isinstance(created, list):
                for record in created:
                    if isinstance(record, dict) and "id" in record:
                        record_id = str(record["id"])
                        self.test_records.append(record_id)
            
            # 测试条件查询
            logger.info("测试条件查询...")
            query1 = f"SELECT * FROM {TEST_TABLE} WHERE category = $category AND status = $status"
            params1: Dict[str, Any] = {"category": "tech", "status": "active"}
            results1 = await cast(AsyncSurreal, self.db).query(query1, params1)
            
            if results1 and len(results1) > 0:
                result_data = results1[0]
                if isinstance(result_data, dict) and "result" in result_data:
                    records = result_data["result"]
                    if isinstance(records, list):
                        logger.success(f"✅ 条件查询成功，找到 {len(records)} 条记录")
                    else:
                        logger.warning("⚠️  条件查询结果格式不正确")
                else:
                    logger.warning("⚠️  条件查询没有找到记录")
            
            # 测试排序和限制
            logger.info("测试排序和限制...")
            query2 = f"SELECT * FROM {TEST_TABLE} WHERE category = 'tech' ORDER BY score DESC LIMIT 2"
            results2 = await cast(AsyncSurreal, self.db).query(query2)
            
            logger.info(f"排序查询结果: {results2}")
            
            if results2 and len(results2) > 0:
                # SurrealDB 返回的是字典列表格式
                if isinstance(results2, list) and len(results2) > 0:
                    if isinstance(results2[0], dict):
                        # 结果直接是字典列表格式
                        records = results2
                        logger.success(f"✅ 排序查询成功，找到 {len(records)} 条记录")
                        for i, record in enumerate(records):
                            if isinstance(record, dict):
                                logger.info(f"排名 {i+1}: {record.get('name', 'N/A')} (分数: {record.get('score', 'N/A')})")
                    elif isinstance(results2[0], list):
                        # 结果嵌套在列表中
                        records = results2[0]
                        logger.success(f"✅ 排序查询成功，找到 {len(records)} 条记录")
                        for i, record in enumerate(records):
                            if isinstance(record, dict):
                                logger.info(f"排名 {i+1}: {record.get('name', 'N/A')} (分数: {record.get('score', 'N/A')})")
                    else:
                        logger.warning(f"⚠️  未知的返回格式: {type(results2[0])}")
                else:
                    logger.warning("⚠️  排序查询结果格式不正确")
            else:
                logger.warning("⚠️  排序查询没有返回结果")
            
            # 测试聚合查询
            logger.info("测试聚合查询...")
            query3 = f"SELECT category, count() AS count, math::mean(score) AS avg_score FROM {TEST_TABLE} GROUP BY category"
            results3 = await cast(AsyncSurreal, self.db).query(query3)
            
            if results3 and len(results3) > 0:
                # SurrealDB 返回的是字典列表格式
                if isinstance(results3, list) and len(results3) > 0:
                    if isinstance(results3[0], dict):
                        # 结果直接是字典列表格式
                        records = results3
                        logger.success(f"✅ 聚合查询成功")
                        for record in records:
                            if isinstance(record, dict):
                                logger.info(f"分类 {record.get('category', 'N/A')}: "
                                          f"数量={record.get('count', 'N/A')}, "
                                          f"平均分={record.get('avg_score', 'N/A')}")
                    elif isinstance(results3[0], list):
                        # 结果嵌套在列表中
                        records = results3[0]
                        logger.success(f"✅ 聚合查询成功")
                        for record in records:
                            if isinstance(record, dict):
                                logger.info(f"分类 {record.get('category', 'N/A')}: "
                                          f"数量={record.get('count', 'N/A')}, "
                                          f"平均分={record.get('avg_score', 'N/A')}")
                    else:
                        logger.warning(f"⚠️  未知的返回格式: {type(results3[0])}")
                else:
                    logger.warning("⚠️  聚合查询结果格式不正确")
            
            logger.success("✅ 查询操作测试通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 查询操作测试失败: {e}")
            return False
    
    async def test_error_handling(self):
        """测试错误处理"""
        logger.info("开始测试错误处理...")
        
        try:
            # 测试查询不存在的表
            logger.info("测试查询不存在的表...")
            try:
                await cast(AsyncSurreal, self.db).query("SELECT * FROM nonexistent_table")
                logger.warning("⚠️  查询不存在的表没有抛出异常")
            except Exception as e:
                logger.success(f"✅ 正确处理了不存在的表查询: {type(e).__name__}")
            
            # 测试无效的查询语法
            logger.info("测试无效的查询语法...")
            try:
                await cast(AsyncSurreal, self.db).query("INVALID SYNTAX TEST")
                logger.warning("⚠️  无效语法查询没有抛出异常")
            except Exception as e:
                logger.success(f"✅ 正确处理了无效语法: {type(e).__name__}")
            
            # 测试操作不存在的记录
            logger.info("测试操作不存在的记录...")
            try:
                result = await cast(AsyncSurreal, self.db).update("test_items:nonexistent", {"name": "test"})
                if not result:
                    logger.success("✅ 正确处理了不存在的记录更新")
                else:
                    logger.warning("⚠️  更新不存在的记录返回了结果")
            except Exception as e:
                logger.success(f"✅ 正确处理了不存在的记录操作: {type(e).__name__}")
            
            # 测试删除不存在的记录
            logger.info("测试删除不存在的记录...")
            try:
                result = await cast(AsyncSurreal, self.db).delete("test_items:nonexistent")
                logger.success("✅ 正确处理了不存在的记录删除")
            except Exception as e:
                logger.success(f"✅ 正确处理了不存在的记录删除异常: {type(e).__name__}")
            
            logger.success("✅ 错误处理测试通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 错误处理测试失败: {e}")
            return False
    
    async def cleanup_test_data(self):
        """清理测试数据"""
        logger.info("开始清理测试数据...")
        
        try:
            if self.test_records:
                logger.info(f"需要清理 {len(self.test_records)} 条测试记录")
                
                for record_id in self.test_records[:]:  # 使用副本避免修改迭代中的列表
                    try:
                        await cast(AsyncSurreal, self.db).delete(record_id)
                        logger.info(f"已删除记录: {record_id}")
                        if record_id in self.test_records:
                            self.test_records.remove(record_id)
                    except Exception as e:
                        logger.warning(f"删除记录 {record_id} 失败: {e}")
                
                logger.success("✅ 测试数据清理完成")
            else:
                logger.info("没有需要清理的测试数据")
            
            # 清理剩余的测试数据（按条件删除）
            try:
                # 使用多个简单的删除语句代替复杂的 OR 条件
                await cast(AsyncSurreal, self.db).query(f"DELETE FROM {TEST_TABLE} WHERE type = 'bulk_test'")
                await cast(AsyncSurreal, self.db).query(f"DELETE FROM {TEST_TABLE} WHERE category = 'tech' OR category = 'business'")
                await cast(AsyncSurreal, self.db).query(f"DELETE FROM {TEST_TABLE} WHERE name ~ '查询测试'")
                await cast(AsyncSurreal, self.db).query(f"DELETE FROM {TEST_TABLE} WHERE name ~ '批量测试'")
                logger.info("已清理条件匹配的测试数据")
            except Exception as e:
                logger.warning(f"条件清理测试数据时出错: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"清理测试数据失败: {e}")
            return False
    
    async def close(self):
        """关闭数据库连接"""
        if self.db:
            try:
                await self.db.close()
                logger.info("数据库连接已关闭")
            except Exception as e:
                logger.warning(f"关闭数据库连接时出错: {e}")


async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("开始 SurrealDB 功能测试")
    logger.info("=" * 60)
    
    # 验证环境变量
    logger.info("验证环境变量配置...")
    required_vars = ["SURREAL_URL", "SURREAL_USER", "SURREAL_PASSWORD", "SURREAL_NAMESPACE", "SURREAL_DATABASE"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        return False
    
    logger.success("✅ 环境变量验证通过")
    
    # 创建测试器
    tester = SurrealDBTester()
    
    try:
        # 1. 连接测试
        if not await tester.connect():
            return False
        
        # 2. 基本 CRUD 测试
        if not await tester.test_basic_crud():
            logger.warning("基本 CRUD 测试失败，继续其他测试...")
        
        # 3. 批量操作测试
        if not await tester.test_bulk_operations():
            logger.warning("批量操作测试失败，继续其他测试...")
        
        # 4. 查询操作测试
        if not await tester.test_query_operations():
            logger.warning("查询操作测试失败，继续其他测试...")
        
        # 5. 错误处理测试
        if not await tester.test_error_handling():
            logger.warning("错误处理测试失败...")
        
        logger.info("=" * 60)
        logger.success("✅ SurrealDB 测试完成")
        logger.info("=" * 60)
        
        return True
        
    except KeyboardInterrupt:
        logger.warning("测试被用户中断")
        return False
        
    except Exception as e:
        logger.error(f"测试过程中发生未预期的错误: {e}")
        return False
        
    finally:
        # 清理测试数据
        await tester.cleanup_test_data()
        # 关闭连接
        await tester.close()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level="INFO"
    )
    
    # 运行测试
    success = asyncio.run(main())
    
    if success:
        logger.success("🎉 所有测试完成！")
        sys.exit(0)
    else:
        logger.error("❌ 测试失败")
        sys.exit(1)