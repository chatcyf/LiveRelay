import asyncio
import json
import time
import traceback
import subprocess
import random
import ffmpeg
from streamlink.session import Streamlink

# ========== Streamlink 初始化（仅用于 Twitch） ==========
session = Streamlink()
session.set_option("twitch-disable-ads", True)
session.set_option("twitch-low-latency", True)
# session.set_option("http-proxy", "http://127.0.0.1:7890")


class LiveRelay:
    def __init__(self, config: dict, item: dict):
        self.index = item["index"]
        self.id = item["id"]
        self.platform = item["platform"].lower()
        self.name = item.get("name", self.id)
        self.flag = f"[{self.platform.upper()}][{self.name}]"
        self.rtmp_server = config["RTMPServer"]
        self.is_running = False

    # =========================
    # Twitch：Streamlink
    # =========================
    async def get_twitch_stream_url(self):
        url = f"https://www.twitch.tv/{self.id}"
        try:
            streams = await asyncio.to_thread(session.streams, url)
            if streams and "best" in streams:
                return streams["best"].url
        except Exception as e:
            if "No streams found" not in str(e):
                print(f"{self.flag} Twitch 检测失败: {e}")
        return None

    # =========================
    # YouTube：yt-dlp（核心）
    # =========================
    async def get_youtube_stream_url(self):
        url = f"https://www.youtube.com/channel/{self.id}/live"
        cmd = [
            "yt-dlp",
            "-f", "best",
            "--no-warnings",
            "--no-progress",
            "-g",
            url
        ]
        try:
            output = await asyncio.to_thread(
                subprocess.check_output,
                cmd,
                stderr=subprocess.DEVNULL,
                timeout=25
            )
            stream_url = output.decode().strip()
            if stream_url:
                return stream_url
        except subprocess.TimeoutExpired:
            print(f"{self.flag} yt-dlp 超时")
        except Exception:
            pass
        return None

    # =========================
    # 统一入口
    # =========================
    async def get_stream_url(self):
        if self.platform == "twitch":
            return await self.get_twitch_stream_url()
        elif self.platform == "youtube":
            return await self.get_youtube_stream_url()
        return None

    # =========================
    # FFmpeg 转推
    # =========================
    async def run_ffmpeg(self, stream_url):
        self.is_running = True
        print(f"{self.flag} 开始推流 -> {self.rtmp_server}")

        try:
            process = (
                ffmpeg
                .input(
                stream_url,
                http_multiple=1,
                reconnect=1,
                reconnect_streamed=1,
                reconnect_delay_max=5
             )
            .output(
            self.rtmp_server,
            vcodec="copy",
            acodec="copy",
            f="flv",
            loglevel="error"
            )
    .run_async(pipe_stdin=True)
)

            while process.poll() is None:
                await asyncio.sleep(5)

            print(f"{self.flag} 推流结束")
        except Exception as e:
            print(f"{self.flag} FFmpeg 异常: {e}")
        finally:
            self.is_running = False

    # =========================
    # 监控循环
    # =========================
    async def monitor_loop(self):
        print(f"{self.flag} 监控启动")
        while True:
            try:
                if not self.is_running:
                    stream_url = await self.get_stream_url()
                    if stream_url:
                        await self.run_ffmpeg(stream_url)

                # 随机轮询，降低风控特征
                await asyncio.sleep(random.randint(45, 90))

            except Exception as e:
                print(f"{self.flag} 监控异常: {e}")
                await asyncio.sleep(15)


# =========================
# 主程序
# =========================
async def main():
    CONFIG_FILE = "config.json"

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] 找不到配置文件 {CONFIG_FILE}")
        return

    tasks = []
    for item in config["streams"]:
        relay = LiveRelay(config, item)
        tasks.append(asyncio.create_task(relay.monitor_loop()))
        await asyncio.sleep(2)

    print(f"[INFO] 已加载 {len(tasks)} 个监控任务")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    while True:
        try:
            print(f"[INFO] 程序启动 {time.strftime('%Y-%m-%d %H:%M:%S')}")
            asyncio.run(main())
        except KeyboardInterrupt:
            print("[INFO] 用户终止程序")
            break
        except Exception as e:
            print(f"[CRITICAL] 主程序崩溃: {e}")
            traceback.print_exc()
            print("[INFO] 15 秒后重启")
            time.sleep(15)
