# 🎀Spider_XHS

**联系作者获取小红书稳定Api源码（登录，上传笔记...）、小红书专业号、小红书千帆、小红书蒲公英，定制需求**

小红书个人主页无水印图片、无水印视频、个人信息和搜索爬取。


## 🎨效果图
### 处理后的所有用户
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/00902dbd-4da1-45bc-90bb-19f5856a04ad)
### 某个用户所有的笔记
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/880884e8-4a1d-4dc1-a4dc-e168dd0e9896)
### 某个笔记具体的内容
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/d17f3f4e-cd44-4d3a-b9f6-d880da626cc8)
### 图形化界面
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/f836698c-0b00-40bb-914d-64f1107330ff)


## ⛳运行环境
Python环境>=3.7
NodeJS环境>=16

## 🎯运行方法
```
多用户下载（下载用户列表所有的笔记）
python home.py
多笔记下载（下载笔记列表里所有的笔记）
python one.py
下载搜索内容
python search.py
```

## 🍥日志
   
| 日期       | 说明                                   |
| -------- | ------------------------------------ |
| 23/08/09 | - 首次提交。 |
| 23/09/13 | - api更改params增加两个字段，修复图片无法下载，有些页面无法访问导致报错。 |
| 23/09/16 | - 较大视频出现编码问题，修复视频编码问题，加入异常处理。 |
| 23/09/18 | - 代码重构，加入失败重试。 |
| 23/09/19 | - 新增下载搜索结果功能。 |
| 23/10/05 | - 新增跳过已下载功能，获取更详细的笔记和用户信息。|
| 23/10/08 | - 上传代码☞Pypi，可通过pip install安装本项目。|
| 23/10/17 | - 搜索下载新增排序方式选项（1、综合排序 2、热门排序 3、最新排序）。|
| 23/10/21 | - 新增图形化界面,上传至release v2.1.0。|
| 23/10/28 | - Fix Bug 修复搜索功能出现的隐藏问题。|


## 🧸注意事项
**本项目仅供学习与交流，侵权必删**

1. home处理的是个人主页 https://www.xiaohongshu.com/user/profile/6185ce66000000001000705b
2. one处理的是笔记详细页 https://www.xiaohongshu.com/explore/64d06670000000000800fb4a
3. search处理的是搜索结果

🛹额外说明
1. 自行将cookie放到static目录下cookies.txt中，去设置里的应用程序里找或者网络请求里找，需要哪些可以参考cookies.txt文件。
2. 可采用以下方法获取cookie，并运行对应文件，只有登陆后的cookies是有用的。
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/e2ceaa15-defc-4d41-a6db-4a9d3f3055e4)
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/78e791a6-ba51-455a-a438-3c829db5c387)

3. 感谢star⭐！不时更新。
4. 有问题可以加QQ（992822653）或者微信（CVZC15751076989）交流！
5. 感谢赞助！如果此项目对您有帮助，请作者喝一杯奶茶~~ （开心一整天😊😊）
6. thank you~~~

![mm_facetoface_collect_qrcode_1696839915907](https://github.com/cv-cat/Spider_XHS/assets/94289429/f8bac4e2-88f1-440c-987a-9803c0a2bbd5)![1696832397](https://github.com/cv-cat/Spider_XHS/assets/94289429/fb7fee7d-7394-4353-b202-165d74a87f54)




