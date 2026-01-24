import os
import sys
import asyncio
import logging

# 将 src 目录添加到 sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 确保 WORKSPACE_PATH 环境变量指向根目录
os.environ["WORKSPACE_PATH"] = os.path.dirname(src_dir)

from biz.rag_service import get_rag_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DIFY_DIR = os.path.join(os.path.dirname(src_dir), "dify")

async def sync_dify_documents():
    """同步 dify 文件夹中的文档到独立的知识库集合中"""
    rag_service = get_rag_service()
    
    if not os.path.exists(DIFY_DIR):
        logger.error(f"目录 {DIFY_DIR} 不存在")
        return

    # 获取现有集合
    try:
        existing_collections = rag_service.get_collection_names()
        logger.info(f"现有集合: {existing_collections}")
    except Exception as e:
        logger.error(f"获取集合列表失败: {e}")
        existing_collections = []

    files = [f for f in os.listdir(DIFY_DIR) if f.endswith(('.docx', '.pdf', '.txt', '.md'))]
    logger.info(f"发现 {len(files)} 个待同步文档")

    for filename in files:
        file_path = os.path.join(DIFY_DIR, filename)
        # 集合名称规则：文件名（去除扩展名）
        collection_name = os.path.splitext(filename)[0]
        
        # 如果集合已存在，可以选择跳过或重新入库
        if collection_name in existing_collections:
            logger.info(f"集合 {collection_name} 已存在，跳过同步")
            continue

        logger.info(f"正在同步文档 {filename} 到集合 {collection_name}...")
        try:
            result = await rag_service.ingest_file(
                file_path=file_path,
                metadata={"original_name": filename, "source_type": "dify_sync"},
                collection_name=collection_name
            )
            logger.info(f"成功同步 {filename}: {result}")
        except Exception as e:
            logger.error(f"同步 {filename} 失败: {e}")

if __name__ == "__main__":
    asyncio.run(sync_dify_documents())
