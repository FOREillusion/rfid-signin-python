## Rfid-signin-python
RFID+Flask+Vue构造一个打卡系统

[项目演示地址](https://flask-serialshow.herokuapp.com/)部署在了Heroku上

[演示视频](https://www.bilibili.com/video/av34612101)

项目功能 | 完成情况 | 满意度
------------ | ---------- | -----------
动态显示签到情况|     :smiley: | 80%
构造在线用户（课堂）池 | :smiley: | 95%
查询签到记录 | :smiley: | 70%
用户注册 | :smiley: | 80%
课堂绑定学生 | :smiley: | 80%
URL加密 | :worried: | 0%
解除课堂与学生关系 | :worried: | 0%
页面优化 | :worried: | 0%

部署的是国外的服务器因此日期显示为国外的日期

### Getting Started
在本地的部署
### 准备工作
1. [硬件准备](https://github.com/zhazhalaila/rfid-signin-python/blob/master/docs/%E7%A1%AC%E4%BB%B6%E5%87%86%E5%A4%87.md)
1. [软件准备](https://github.com/zhazhalaila/rfid-signin-python/blob/master/docs/%E8%BD%AF%E4%BB%B6%E5%87%86%E5%A4%87.md)

### 安装
```
git clone https://github.com/zhazhalaila/rfid-signin-python.git
cd rfid-signin-python
pip install -r requirements.txt
```

### 运行与测试
运行
```
set FLASK_APP=serialshow.py
flask db init
flask db migrate -m "first"
flask db upgrade
flask run
```
测试数据库是否正确
```
python tests.py
```

### Built With
* [Redis](https://redis.io/) 主要用来构造在线用户（课堂）池
* [Flask](http://flask.pocoo.org/) Web框架
* [Vue](https://cn.vuejs.org/index.html) 动态查询

### API示例

查询学生签到情况，URL格式`http://127.0.0.1:5000/api/student_history?name=parameter`

返回数据格式
```
{"history":[{"active":true,"class_name":"RFID\u4f20\u611f\u5668","time":"2018-10-27 09:06:10"}]}
```

注意返回数据格式会出现`utf`编码的信息，我们可以不用管，JS会自动解析

查询当前签到情况，URL格式`http://127.0.0.1:5000/api/class_history?name=parameter&time=parameter`

返回数据格式
```
{"history":[{"active":true,"name":"\u6d4b\u8bd5\u8d26\u53f7","time":"2018-10-27 09:06:10"}]}
```

### 与硬件交互

使用的COM3/4接口，Python已经有库可以帮我们完成读取USB接口的功能

启动`spider.py`，就可以看到结果了

[原理](https://github.com/zhazhalaila/rfid-signin-python/blob/master/docs/%E7%AD%BE%E5%88%B0%E5%8E%9F%E7%90%86.md)

### 贡献代码
没有什么要求，只要能跑就行了，可以增加一些丰富的功能

### License
[MIT](https://opensource.org/licenses/MIT)
