# Spider_XHS
![image](https://img.shields.io/badge/cv_cat-Spider_XHS-blue)

小红书个人主页图片和视频无水印爬取

## 效果图
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/ef8990bc-d568-4b63-9dfc-4e2e4f235f99)

![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/a5eb7df4-434a-4e6e-91e1-b60b40ca08e8)

![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/d8c2e84e-3e78-4ca8-8c93-406a3e74da91)

![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/7a0ea368-5507-469f-84f4-6dda59568b86)

## 运行环境
Python环境
NodeJS环境

运行方法：把你想要的id全部放到列表里
```

多用户下载（下载用户列表所有的笔记）(需登录cookie)
python muti-note.py
多笔记下载（下载笔记列表里所有的笔记）(需登录cookie)
python one-note.py
下载搜索内容(需登录cookie)
python search-note.py
```
## 日志
1. 23/08/08   first commit
2. 23/09/13 【api更改params增加两个字段】修复图片无法下载，有些页面无法访问导致报错。
3. 23/09/16 【较大视频出现编码问题】修复视频编码问题，加入异常处理。
4. 23/09/18   代码重构，加入失败重试。
5. 23/09/19   新增下载搜索结果功能

## 注意事项
**本项目仅供学习与交流，侵权必删**


关于muti-note和one-note
1. 这两个必须登录，获取cookie，不然无法获取所有笔记
2. muti-note处理的是个人主页 https://www.xiaohongshu.com/user/profile/6185ce66000000001000705b
3. one-note处理的是笔记详细页 https://www.xiaohongshu.com/explore/64d06670000000000800fb4a
4. search-note处理的是搜索结果

other
1. 自行将cookies放到目录下cookies.txt中，去设置里的应用程序里找或者网络请求里找，需要哪些可以参考cookie.txt文件。
2. 可采用以下方法获取cookie，并运行对应文件。
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/e2ceaa15-defc-4d41-a6db-4a9d3f3055e4)
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/78e791a6-ba51-455a-a438-3c829db5c387)

3. 欢迎star，不时更新。
4. 有问题可以加QQ或者微信交流（992822653）
