import json
import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import os
from datetime import datetime

# ==================== 配置区（可自行扩展）====================
CANDIDATES = [
    "https://www.msnii.com/api/xml.php",      # 美少女
    "https://www.xrbsp.com/api/xml.php",      # 淫水机
    "https://www.gdlsp.com/api/xml.php",      # 香奶儿
    "https://www.kxgav.com/api/xml.php",      # 白嫖
    "https://www.pgxdy.com/api/xml.php",      # 黄AV
    # === 在此继续添加你从全网收集的新接口（一行一个）===
    # 示例： "https://example.com/api/xml.php",
]

# 可选：从 candidates.txt 读取额外候选（支持动态扩展）
if os.path.exists("candidates.txt"):
    with open("candidates.txt", "r", encoding="utf-8") as f:
        extra = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    CANDIDATES.extend(extra)

def test_api(api_url: str) -> bool:
    """测试接口是否可用（核心测试逻辑）"""
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

        # 宽松 XML 校验（TVBox 常用 RSS 结构）
        try:
            root = ET.fromstring(content.encode("utf-8"))
            if (root.tag == "rss" or 
                root.find("channel") is not None or 
                root.findall(".//category") or 
                root.findall(".//video") or 
                root.findall(".//list")):
                return True
        except ParseError:
            # 非严格 XML 时，关键词兜底
            lower = content.lower()
            if any(k in lower for k in ["rss", "channel", "category", "video", "list"]):
                return True
        return False
    except Exception as e:
        print(f"[{datetime.now()}] 测试失败 {api_url}: {e}")
        return False

# ==================== 主逻辑 ====================
print(f"[{datetime.now()}] 开始每日色情接口更新...")

# 1. 加载现有 video.json 作为模板（保留 parses、rules、lives 等）
with open("video.json", "r", encoding="utf-8") as f:
    data = json.load(f)

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
        # 标准化 site 对象（保持与你示例一致）
        site_dict = {
            "key": api.split("/")[2].replace("www.", "").replace(".com", "").replace(".net", ""),
            "name": api.split("/")[2].replace("www.", ""),
            "type": 0,
            "api": api,
            "searchable": 1,
            "quickSearch": 1,
            "filterable": 1
        }
        # 保留原 item 中其他自定义字段（如 style、header）
        if isinstance(item, dict):
            site_dict.update({k: v for k, v in item.items() if k not in ["key", "name", "api"]})
        working_sites.append(site_dict)
        print(f"✅ 可用: {api}")

# 3. 更新 sites（只保留可用）
data["sites"] = working_sites

# 4. 可选：更新 lives（示例保留原有 selive.txt，可自行扩展测试 m3u8）
# data["lives"] = [...]  # 如需动态更新 lives，可在此扩展

# 5. 写回文件
with open("video.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 更新完成！当前可用色情接口数量: {len(working_sites)}")
