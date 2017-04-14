# 功能

- Monkey自动化测试
- 支持多种取包方式
	- 自动取包（需自行编写取包脚本）
	- 从指定URL取包
	- 指定测试本地路径包
- 支持多设备同时测试
- 支持选择安装apk前是否先卸载旧版本
- 加入[Wifi Manager](https://github.com/ntflc/WifiManager)、[simiasque](https://github.com/Orange-OpenSource/simiasque)以保证测试过程中网络畅通
- 支持测试完毕后分析Crash和ANR，将问题日志拆分成单个文件，通过邮件发送给指定收件人

# 使用方法

``` python
python -v VERSION [-u URL] [-p PATH] -s SN [-i UNINSTALL] [-t THROTTLE] [-c COUNT] -r RECIPIENT
```

- `-v/--version`，必填，项目版本。该项目版本必须为conf/project.json中的主key
- `-u/--url`，选填，apk网络地址。如果存在该项，则不自动取包，改用该地址的apk文件（优先级高于-p/--path）
- `-p/--path`，选填，apk本地路径。如果存在该项，则不自动取包，改用该路径的apk文件（优先级低于-u/--url）
- `-s/--sn`，必填，待测设备序列号。如果有多个，以空格隔开
- `-i/--uninstall`，选填，安装前是否卸载。参数取值为true时，安装apk之前会先执行卸载操作
- `-t/--throttle`，选填，monkey参数。默认值为700
- `-c/--count`，选填，monkey参数。默认值为10000
- `-r/--recipient`，必填，收件人。如果有多个，以空格隔开

# 配置参数

- `conf/mail.ini`为发件人邮箱信息
    - host为SMTP服务器地址
    - user为发件人账号（仅用于验证登录信息）
    - passwd为发件人密码（需进行base64处理）
    - name为发件人名称
    - sender为发件人邮箱（可与user不同，如同一公司邮箱拥有多个别名）
- `conf/project.json`为待测App项目信息
    - 为JSON格式
    - 一级key为项目版本或项目简称
    - 一级value为一个新的JSON，必须包括的二级key为name，即项目完整名称（用于邮件标题、内容）
    - 二级其他key可自行填充，一般用于自动取包的配置信息

# 测试步骤

- 初始化全局日志（本次测试的日志存在logs目录下）
- 获取项目信息
- 获取apk安装包
    - 如果包含`-u/--url`参数，则优先从该链接地址获取
    - 如果不包含`-u/--url`但包含`-p/--path`参数，则直接使用该本地路径
    - 如果不包含上述两个参数，则通过自动取包脚本，获取最新包
- 对每一个设备启动一个线程
    - 初始化设备日志（存在logs/device_sn目录下）
    - 卸载之前版本的apk（由参数`-i/--uninstall`决定）
    - 安装apk文件
    - 安装Wifi Manager并启动
    - 安装simiasque并启动
    - 执行Monkey测试
    - 关闭simiasque
    - 关闭屏幕
    - 生成dumpsys信息（存在logs/device_sn/dumpsys）
    - 分析设备日志（将每一个Crash日志存在logs/device_sn/crash目录下，每一个ANR日志存在logs/device_sn/anr目录下）
    - 如果存在Crash或ANR，则发送邮件
- 将本次测试的完整日志目录复制到历史日志（history_logs）目录下

# 注意事项

- `utils/get_apk.py`需要根据实际情况重新编写
    - `get_apk_from_url()`函数用于下载URL地址的apk文件
    - `get_latest_apk()`函数用于自动获取最新apk文件，需自行编写
- 建议将apk文件存放在apks目录下，可针对不同的项目创建对应目录
- 可将此项目与Jenkins平台相结合，配合Jenkins的参数化构建，非常方便
