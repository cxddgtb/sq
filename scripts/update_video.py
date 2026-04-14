import json
import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import os
from datetime import datetime

# ==================== 配置区（无需修改，可后续通过 candidates.txt 扩展）====================
CANDIDATES = [
    "https://www.msnii.com/api/xml.php",      # 美少女
    "https://www.xrbsp.com/api/xml.php",      # 淫水机
    "https://www.gdlsp.com/api/xml.php",      # 香奶儿
    "https://www.kxgav.com/api/xml.php",      # 白嫖
    "https://www.pgxdy.com/api/xml.php",      # 黄AV
    "https://www.52av.one/api/xml.php",       # 52AV
    "https://www.avtt.me/api/xml.php",        # AVTT
    # 如需更多接口，请在仓库根目录新建 candidates.txt（一行一个URL），无需修改本文件
]

# 官方模板地址（自动修复 JSON 损坏）
TEMPLATE_URL = "https://raw.githubusercontent.com/wwb521/live/refs/heads/main/video.json"

def load_template():
    """增强加载：本地损坏或不存在时自动从官方拉取完整模板"""
    if os.path.exists("video.json"):
        try:
            with open("video.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            print("✅ 从本地 video.json 加载模板成功")
            return data
        except json.JSONDecodeError as e:
            print(f"⚠️ 本地 video.json 损坏 ({e}) → 自动从官方模板拉取")
        except Exception as e:
            print(f"⚠️ 本地加载异常 ({e}) → 自动拉取")

    print("📥 从官方模板拉取最新 video.json...")
    try:
        resp = requests.get(TEMPLATE_URL, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # 写回本地，下次无需再拉
        with open("video.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ 已自动修复并保存官方模板")
        return data
    except Exception as e:
        raise RuntimeError(f"❌ 无法加载模板: {e}\n请手动下载 {TEMPLATE_URL} 并上传为 video.json") from e

def test_api(api_url: str) -> bool:
    """测试接口是否可用（TVBox 常用 XML/RSS 结构校验）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TVBox-Bot/1.0; +https://github.com/your-repo)"
    }
    try:
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return False
        content = resp.text.strip()
        if not content or not content.startswith("<"):
            return False

        # 严格 XML 解析
        try:
            root = ET.fromstring(content.encode("utf-8"))
            if (root.tag == "rss" or 
                root.find("channel") is not None or 
                root.findall(".//category") or 
                root.findall(".//video") or 
                root.findall(".//list")):
                return True
        except ParseError:
            # 非严格 XML 时关键词兜底
            lower = content.lower()
            if any(k in lower for k in ["rss", "channel", "category", "video", "list"]):
                return True
        return False
    except Exception as e:
        print(f"[{datetime.now()}] 测试失败 {api_url}: {e}")
        return False

# ==================== 主逻辑 ====================
print(f"[{datetime.now()}] 开始每日色情接口更新...")

# 1. 加载模板（自动修复 JSON 错误）
data = load_template()

# 2. 去重 + 测试所有候选 + 原有 sites
seen = set()
working_sites = []

for item in data.get("sites", []) + [{"api": url} for url in CANDIDATES]:
    api = item.get("api") if isinstance(item, dict) else item
    if not api or api in seen:
        continue
    seen.add(api)

    print(f"测试接口: {api}")
    if test_api(api):
        # 标准化 site 对象（完全匹配原始 video.json 格式）
        site_dict = {
            "key": api.split("/")[2].replace("www.", "").replace(".com", "").replace(".net", ""),
            "name": api.split("/")[2].replace("www.", ""),
            "type": 0,
            "api": api,
            "searchable": 1,
            "quickSearch": 1,
            "filterable": 1
        }
        # 保留原 item 中其他自定义字段
        if isinstance(item, dict):
            site_dict.update({k: v for k, v in item.items() if k not in ["key", "name", "api"]})
        working_sites.append(site_dict)
        print(f"✅ 可用: {api}")

# 3. 更新 sites（只保留可用）
data["sites"] = working_sites

# 4. 写回文件（保持原始格式）
with open("video.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 更新完成！当前可用色情接口数量: {len(working_sites)}")
