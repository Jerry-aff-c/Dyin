# -*- encoding: utf-8 -*-
"""
测试脚本：获取关注用户的近三天视频数据并查看数据结构
"""

import sys
import os
from datetime import datetime, timedelta
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.lib.douyin import Douyin
from backend.settings import settings


def test_get_following_videos():
    """测试获取关注用户的近三天视频数据"""
    
    # 配置参数
    SEC_USER_ID = "MS4wLjABAAAABF-5EvorTy_tdI7eYmL2Mf0JdDQX6SHUtTkbgsfx13uJHWbiIftkY5Dh6je5brJ4"  # 替换为你的抖音 sec_user_id
    COOKIE = settings.get("cookie", "").strip()  # 从配置文件获取 cookie
    
    print("=" * 80)
    print("开始测试：获取关注用户的近三天视频数据")
    print("=" * 80)
    
    # 步骤1：获取关注列表
    print("\n步骤1：获取关注列表...")
    print("-" * 80)
    
    try:
        following_crawler = Douyin(
            target=SEC_USER_ID,
            type="following",
            limit=0,  # 不设限制，获取所有关注账号
            cookie=COOKIE
        )
        
        # 运行关注列表采集
        following_crawler.run()
        
        following_list = following_crawler.results
        print(f"✓ 成功获取到 {len(following_list)} 个关注账号")
        
        if len(following_list) == 0:
            print("⚠ 没有获取到关注账号，请检查 sec_user_id 和 cookie 是否正确")
            return
        
        # 打印前3个关注账号的信息
        print("\n前3个关注账号的信息：")
        for i, account in enumerate(following_list[:3], 1):
            print(f"{i}. 昵称: {account.get('nickname', 'Unknown')}")
            print(f"   sec_uid: {account.get('sec_uid', 'N/A')}")
            print(f"   粉丝数: {account.get('follower_count', 0)}")
            print()
        
        # 步骤2：获取每个关注账号的视频数据
        print("\n步骤2：获取每个关注账号的视频数据...")
        print("-" * 80)
        
        # 只测试前3个关注账号
        test_accounts = following_list[:3]
        
        all_videos = []
        three_days_ago = datetime.now() - timedelta(days=3)
        
        for idx, account in enumerate(test_accounts, 1):
            account_sec_uid = account.get('sec_uid')
            account_name = account.get('nickname', 'Unknown')
            
            print(f"\n[{idx}/{len(test_accounts)}] 正在采集账号: {account_name}")
            print(f"    sec_uid: {account_sec_uid}")
            
            try:
                # 创建爬虫实例
                crawler = Douyin(
                    target=account_sec_uid,
                    type="post",
                    limit=10,  # 每个账号最多10个视频
                    cookie=COOKIE
                )
                
                # 运行采集
                crawler.run()
                
                # 直接使用所有视频（不限制时间）
                recent_videos = crawler.results
                
                # 过滤近三天的视频用于统计
                recent_videos_filtered = []
                for video in crawler.results:
                    create_time = video.get('create_time')
                    if create_time:
                        video_time = datetime.fromtimestamp(create_time)
                        if video_time > three_days_ago:
                            recent_videos_filtered.append(video)
                
                print(f"    ✓ 采集到 {len(crawler.results)} 个视频")
                print(f"    ✓ 近三天视频: {len(recent_videos_filtered)} 个")
                
                # 添加账号信息到视频数据
                for video in recent_videos:
                    video['account_info'] = {
                        'nickname': account_name,
                        'sec_uid': account_sec_uid,
                        'follower_count': account.get('follower_count', 0)
                    }
                
                all_videos.extend(recent_videos)
                
            except Exception as e:
                print(f"    ✗ 采集失败: {e}")
        
        # 步骤3：显示数据结构
        print("\n" + "=" * 80)
        print("步骤3：数据结构分析")
        print("=" * 80)
        
        print(f"\n总共获取到 {len(all_videos)} 个近三天的视频")
        
        if len(all_videos) > 0:
            # 显示第一个视频的完整数据结构
            print("\n第一个视频的完整数据结构：")
            print("-" * 80)
            print(json.dumps(all_videos[0], indent=2, ensure_ascii=False))
            
            # 分析视频数据的关键字段
            print("\n" + "=" * 80)
            print("视频数据关键字段分析")
            print("=" * 80)
            
            first_video = all_videos[0]
            print("\n视频基本信息：")
            print(f"  视频ID: {first_video.get('id', 'N/A')}")
            print(f"  描述: {first_video.get('desc', 'N/A')[:50]}...")
            print(f"  创建时间: {datetime.fromtimestamp(first_video.get('time', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  视频类型: {first_video.get('type', 'N/A')}")
            print(f"  时长: {first_video.get('duration', 'N/A')} 秒")
            
            print("\n视频统计数据：")
            print(f"  点赞数: {first_video.get('digg_count', 0)}")
            print(f"  评论数: {first_video.get('comment_count', 0)}")
            print(f"  分享数: {first_video.get('share_count', 0)}")
            print(f"  收藏数: {first_video.get('collect_count', 0)}")
            
            print("\n视频媒体信息：")
            print(f"  封面: {first_video.get('cover', 'N/A')[:50]}...")
            print(f"  视频地址: {first_video.get('play_addr', 'N/A')[:50]}..." if 'play_addr' in first_video else "  视频地址: N/A")
            
            print("\n作者信息：")
            print(f"  昵称: {first_video.get('author_nickname', 'N/A')}")
            print(f"  UID: {first_video.get('author_uid', 'N/A')}")
            print(f"  头像: {first_video.get('author_avatar', 'N/A')[:50]}...")
            
            if 'account_info' in first_video:
                print("\n账号信息（我们添加的）：")
                print(f"  昵称: {first_video['account_info']['nickname']}")
                print(f"  sec_uid: {first_video['account_info']['sec_uid']}")
                print(f"  粉丝数: {first_video['account_info']['follower_count']}")
            
            # 统计所有视频的数据
            print("\n" + "=" * 80)
            print("所有视频统计信息")
            print("=" * 80)
            
            total_likes = sum(v.get('digg_count', 0) for v in all_videos)
            total_comments = sum(v.get('comment_count', 0) for v in all_videos)
            total_shares = sum(v.get('share_count', 0) for v in all_videos)
            
            print(f"  总视频数: {len(all_videos)}")
            print(f"  总点赞数: {total_likes}")
            print(f"  总评论数: {total_comments}")
            print(f"  总分享数: {total_shares}")
            print(f"  平均点赞数: {total_likes / len(all_videos):.1f}")
            print(f"  平均评论数: {total_comments / len(all_videos):.1f}")
            print(f"  平均分享数: {total_shares / len(all_videos):.1f}")
            
            # 按点赞数排序
            sorted_videos = sorted(all_videos, key=lambda x: x.get('digg_count', 0), reverse=True)
            print(f"\n点赞最多的前3个视频：")
            for i, video in enumerate(sorted_videos[:3], 1):
                print(f"  {i}. {video.get('desc', 'N/A')[:30]}... - {video.get('digg_count', 0)} 赞")
            
        else:
            print("\n⚠ 没有获取到近三天的视频数据")
        
        # 保存数据到文件
        print("\n" + "=" * 80)
        print("保存数据到文件")
        print("=" * 80)
        
        output_file = os.path.join(os.path.dirname(__file__), 'following_videos.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_videos, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 数据已保存到: {output_file}")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_get_following_videos()