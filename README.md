# Spider_XHS
![image](https://img.shields.io/badge/cv_cat-Spider_XHS-blue)

小红书个人主页图片和视频无水印爬取

## 效果图
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/00902dbd-4da1-45bc-90bb-19f5856a04ad)

![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/880884e8-4a1d-4dc1-a4dc-e168dd0e9896)

![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/d17f3f4e-cd44-4d3a-b9f6-d880da626cc8)


## 运行环境
Python环境
NodeJS环境

运行方法：把你想要的笔记对应网址放到对应文件最下面的列表里
```
多用户下载（下载用户列表所有的笔记）
python home.py
多笔记下载（下载笔记列表里所有的笔记）
python one.py
下载搜索内容
python search.py
```
## 日志
1. 23/08/08   first commit
2. 23/09/13 【api更改params增加两个字段】修复图片无法下载，有些页面无法访问导致报错。
3. 23/09/16 【较大视频出现编码问题】修复视频编码问题，加入异常处理。
4. 23/09/18   代码重构，加入失败重试。
5. 23/09/19   新增下载搜索结果功能。
6. 23/10/05   新增跳过已下载功能，获取更详细的笔记和用户信息。

## 注意事项
**本项目仅供学习与交流，侵权必删**

1. home处理的是个人主页 https://www.xiaohongshu.com/user/profile/6185ce66000000001000705b
2. one处理的是笔记详细页 https://www.xiaohongshu.com/explore/64d06670000000000800fb4a
3. search处理的是搜索结果

other
1. 自行将cookies放到目录下cookies.txt中，去设置里的应用程序里找或者网络请求里找，需要哪些可以参考cookie.txt文件。
2. 可采用以下方法获取cookie，并运行对应文件。
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/e2ceaa15-defc-4d41-a6db-4a9d3f3055e4)
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/78e791a6-ba51-455a-a438-3c829db5c387)

3. 欢迎star，不时更新。
4. 有问题可以加QQ或者微信交流（992822653）
