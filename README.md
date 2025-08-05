<p align="center">
  <a href="https://github.com/cv-cat/Spider_XHS" target="_blank" align="center" alt="Go to XHS_Spider Website">
    <picture>
      <img width="220" src="https://github.com/user-attachments/assets/b817a5d2-4ca6-49e9-b7b1-efb07a4fb325" alt="Spider_XHS logo">
    </picture>
  </a>
</p>


<div align="center">
    <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/python-3.7%2B-blue" alt="Python 3.7+">
    </a>
    <a href="https://nodejs.org/zh-cn/">
        <img src="https://img.shields.io/badge/nodejs-18%2B-blue" alt="NodeJS 18+">
    </a>
</div>



# Spider_XHS

**✨ 专业的小红书数据采集解决方案，支持笔记爬取，保存格式为excel或者media**

**✨ 小红书全域运营解决方法，AI一键改写笔记（图文，视频）直接上传**

## ⭐功能列表

**⚠️ 任何涉及数据注入的操作都是不被允许的，本项目仅供学习交流使用，如有违反，后果自负**

| 模块           | 已实现                                                                             |
|---------------|---------------------------------------------------------------------------------|
| 小红书创作者平台 | ✅ 二维码登录<br/>✅ 手机验证码登录<br/>✅ 上传（图集、视频）作品<br/>✅查看自己上传的作品      |
|    小红书PC    | ✅ 二维码登录<br/> ✅ 手机验证码登录<br/> ✅ 获取无水印图片<br/> ✅ 获取无水印视频<br/> ✅ 获取主页的所有频道<br/>✅ 获取主页推荐笔记<br/>✅ 获取某个用户的信息<br/>✅ 用户自己的信息<br/>✅ 获取某个用户上传的笔记<br/>✅ 获取某个用户所有的喜欢笔记<br/>✅ 获取某个用户所有的收藏笔记<br/>✅ 获取某个笔记的详细内容<br/>✅ 搜索笔记内容<br/>✅ 搜索用户内容<br/>✅ 获取某个笔记的评论<br/>✅ 获取未读消息信息<br/>✅ 获取收到的评论和@提醒信息<br/>✅ 获取收到的点赞和收藏信息<br/>✅ 获取新增关注信息|


## 🌟 功能特性

- ✅ **多维度数据采集**
  - 用户主页信息
  - 笔记详细内容
  - 智能搜索结果抓取
- 🚀 **高性能架构**
  - 自动重试机制
- 🔒 **安全稳定**
  - 小红书最新API适配
  - 异常处理机制
  - proxy代理
- 🎨 **便捷管理**
  - 结构化目录存储
  - 格式化输出（JSON/EXCEL/MEDIA）
  
## 🎨效果图
### 处理后的所有用户
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/00902dbd-4da1-45bc-90bb-19f5856a04ad)
### 某个用户所有的笔记
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/880884e8-4a1d-4dc1-a4dc-e168dd0e9896)
### 某个笔记具体的内容
![image](https://github.com/cv-cat/Spider_XHS/assets/94289429/d17f3f4e-cd44-4d3a-b9f6-d880da626cc8)
### 保存的excel
![image](https://github.com/user-attachments/assets/707f20ed-be27-4482-89b3-a5863bc360e7)

## 🛠️ 快速开始
### ⛳运行环境
- Python 3.7+
- Node.js 18+

### 🎯安装依赖
```
pip install -r requirements.txt
npm install
```

### 🎨配置文件
配置文件在项目根目录.env文件中，将下图自己的登录cookie放入其中，cookie获取➡️在浏览器f12打开控制台，点击网络，点击fetch，找一个接口点开
![image](https://github.com/user-attachments/assets/6a7e4ecb-0432-4581-890a-577e0eae463d)

复制cookie到.env文件中（注意！登录小红书后的cookie才是有效的，不登陆没有用）
![image](https://github.com/user-attachments/assets/5e62bc35-d758-463e-817c-7dcaacbee13c)

### 🚀运行项目
```
python main.py
```

### 🗝️注意事项
- main.py中的代码是爬虫的入口，可以根据自己的需求进行修改
- apis/xhs_pc_apis.py 中的代码包含了所有的api接口，可以根据自己的需求进行修改
- apis/xhs_creator_apis.py 中的代码包含了小红书创作者平台的api接口，可以根据自己的需求进行修改


## 🍥日志
   
| 日期       | 说明                                        |
|----------|-------------------------------------------|
| 23/08/09 | - 首次提交                                    |
| 23/09/13 | - api更改params增加两个字段，修复图片无法下载，有些页面无法访问导致报错 |
| 23/09/16 | - 较大视频出现编码问题，修复视频编码问题，加入异常处理              |
| 23/09/18 | - 代码重构，加入失败重试                             |
| 23/09/19 | - 新增下载搜索结果功能                              |
| 23/10/05 | - 新增跳过已下载功能，获取更详细的笔记和用户信息                 |
| 23/10/08 | - 上传代码☞Pypi，可通过pip install安装本项目           |
| 23/10/17 | - 搜索下载新增排序方式选项（1、综合排序 2、热门排序 3、最新排序）      |
| 23/10/21 | - 新增图形化界面,上传至release v2.1.0               |
| 23/10/28 | - Fix Bug 修复搜索功能出现的隐藏问题                   |
| 25/03/18 | - 更新API，修复部分问题                            |
| 25/06/07 | - 更新search接口，区分视频和图集下载，增加小红书创作者api        |
| 25/07/15 | - 更新 xs version56 & 小红书创作者接口              |


## 🧸额外说明
1. 感谢star⭐和follow📰！不时更新
2. 作者的联系方式在主页里，有问题可以随时联系我
3. 可以关注下作者的其他项目，欢迎 PR 和 issue
4. 感谢赞助！如果此项目对您有帮助，请作者喝一杯奶茶~~ （开心一整天😊😊）
5. thank you~~~

<div align="center">
  <img src="./author/wx_pay.png" width="400px" alt="微信赞赏码"> 
  <img src="./author/zfb_pay.jpg" width="400px" alt="支付宝收款码">
</div>


## 📈 Star 趋势
<a href="https://www.star-history.com/#cv-cat/Spider_XHS&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=cv-cat/Spider_XHS&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=cv-cat/Spider_XHS&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=cv-cat/Spider_XHS&type=Date" />
 </picture>
</a>


