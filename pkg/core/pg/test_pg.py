import asyncio
import os
from loguru import logger
from datetime import datetime
from . import PostgresConfig, PostgresManager

async def test_postgres():
    """测试PostgreSQL功能"""
    try:
        # 创建配置
        config = PostgresConfig(
            host=os.getenv('PG_HOST', '47.116.173.33'),
            port=int(os.getenv('PG_PORT', 5432)),
            database=os.getenv('PG_DATABASE', 'travel'),
            user=os.getenv('PG_USER', 'postgres'),
            password=os.getenv('PG_PASSWORD', 'aqUPV0q-G.+ChJk=%Kna'),
        )
        
        # 创建管理器
        manager = PostgresManager(config)
        
        # 测试1: 初始化表
        logger.info("测试1: 初始化数据库表")
        await manager.init_tables()
        
        # 测试2: 保存笔记
        logger.info("测试2: 保存笔记信息")
        test_note = {
            'note_id': 'test_note_001',
            'note_url': 'https://example.com/note/001',
            'note_type': 'video',
            'user_id': 'user_001',
            'home_url': 'https://example.com/user/001',
            'nickname': '测试用户',
            'avatar': 'https://example.com/avatar/001.jpg',
            'title': '测试笔记标题',
            'desc': '这是一个测试笔记的描述',
            'liked_count': 100,
            'collected_count': 50,
            'comment_count': 30,
            'share_count': 20,
            'video_cover': 'https://example.com/cover/001.jpg',
            'video_addr': 'https://example.com/video/001.mp4',
            'image_list': [
                'https://example.com/image/001_1.jpg',
                'https://example.com/image/001_2.jpg'
            ],
            'tags': ['测试', '示例'],
            'upload_time': datetime.now().isoformat(),
            'ip_location': '杭州'
        }
        
        success = await manager.save_note(test_note)
        assert success, "保存笔记失败"
        logger.info("笔记保存成功")
        
        # 测试3: 保存媒体文件
        logger.info("测试3: 保存媒体文件信息")
        media_success = await manager.save_media_file(
            note_id='test_note_001',
            file_type='video',
            file_url='https://example.com/video/001.mp4',
            file_path='/data/media/video/001.mp4'
        )
        assert media_success, "保存媒体文件失败"
        logger.info("媒体文件保存成功")
        
        # 测试4: 查询笔记
        logger.info("测试4: 查询笔记信息")
        note = await manager.get_note('test_note_001')
        assert note is not None, "查询笔记失败"
        assert note['note_id'] == 'test_note_001', "笔记ID不匹配"
        logger.info(f"查询到笔记: {note['title']}")
        
        # 测试5: 查询媒体文件
        logger.info("测试5: 查询媒体文件信息")
        media_files = await manager.get_note_media_files('test_note_001')
        assert len(media_files) > 0, "查询媒体文件失败"
        logger.info(f"查询到媒体文件数量: {len(media_files)}")
        
        # 测试6: 清理测试数据
        logger.info("测试6: 清理测试数据")
        await manager.client.execute(f"DROP TABLE IF EXISTS {manager.client.table_name('media_files')}")
        await manager.client.execute(f"DROP TABLE IF EXISTS {manager.client.table_name('notes')}")
        logger.info("测试数据清理完成")
        
        # 关闭连接
        await manager.client.disconnect()
        logger.info("所有测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中出现错误: {str(e)}")
        raise

if __name__ == '__main__':
    # 配置日志
    logger.add("logs/pg_test_{time}.log", rotation="500 MB", encoding="utf-8", enqueue=True, retention="10 days")
    
    # 运行测试
    asyncio.run(test_postgres()) 