# LiveRelay
陈一发儿的直播转播工具

需要使用ip比较干净的vps，推荐用debian 12或者更高的版本

主要使用的代码

```screen -S restream```

```pip3 install -r requirements.txt```

```python3 main.py```


各种前置需求和推荐搭配的工具们

推荐安装docker，因为二次转推建议用 restreamer 

```apt-get update -y && apt-get install curl -y```

```sudo apt install ffmpeg -y```

```sudo apt install screen -y```

```sudo apt install -y python3-pip -y```

```python3 -m pip install --upgrade pip```

```pip3 install you-get```

```pip3 install --upgrade yt-dlp```

```pip3 install --upgrade yt-dlp-ejs```

```pip3 install --upgrade streamlink```

```curl -fsSL https://deno.land/install.sh | sh```

debian 12 安装docker的部分




更新系统

```sudo apt update -y && sudo apt upgrade -y```

