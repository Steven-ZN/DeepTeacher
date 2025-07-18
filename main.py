import keyboard
import requests
import base64
import io
import asyncio
import mss
import os
import uuid
from PIL import Image
from edge_tts import Communicate
import playsound

# ---------- 截图模块 ----------
def take_screenshot():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # 全屏
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        return img

# ---------- Base64编码图像 ----------
def encode_image_to_base64(img):
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# ---------- LLaVA视觉模型推理 ----------
def query_llava(image):
    img_b64 = encode_image_to_base64(image)
    payload = {
        "model": "llava-phi3:3.8b",
        "prompt": "请描述这张图片的内容。",
        "images": [img_b64],
        "stream": False
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return response.json().get("response", "")

# ---------- DeepSeek深度讲解 ----------
def query_deepseek(text):
    prompt = f"你是一位富有耐心和智慧的老师，这段话是你的助教对学生屏幕的描述，请基于他描述的内容，解答学生的疑问：\n{text}"
    payload = {
        "model": "deepseek-llm:7b",
        "prompt": prompt,
        "stream": False
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return response.json().get("response", "")

# ---------- Edge TTS 播报 ----------
async def speak(text):
    temp_filename = f"output_{uuid.uuid4().hex}.mp3"
    try:
        communicator = Communicate(text, voice="zh-CN-XiaoxiaoNeural")
        await communicator.save(temp_filename)
        playsound.playsound(temp_filename)
    except Exception as e:
        print("[ERROR] 语音播报出错：", e)
    finally:
        if os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except Exception as e:
                print("[WARN] 删除临时文件失败：", e)

# ---------- 快捷键主函数 ----------
def on_hotkey():
    print("[INFO] F8 触发，开始截图...")
    screenshot = take_screenshot()
    print("[INFO] 图像发送至 LLaVA 进行识别...")
    caption = query_llava(screenshot)
    print("[LLaVA]", caption)

    print("[INFO] 文本发送至 DeepSeek 进行讲解...")
    explanation = query_deepseek(caption)
    print("[DeepSeek]", explanation)

    asyncio.run(speak(explanation))

# ---------- 主程序入口 ----------
if __name__ == '__main__':
    print("等待按下 F8 开始截图分析，ESC 退出")
    keyboard.add_hotkey('F8', on_hotkey)
    keyboard.wait('esc')
