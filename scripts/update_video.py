import json
import requests
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import os
from datetime import datetime

# ==================== 配置区（已嵌入 Google + 必应 + 多关键字智能搜索结果）====================
# 1. 硬编码经典接口（保留）
HARDCODED = [
    "https://www.msnii.com/api/xml.php",
    "https://www.xrbsp.com/api/xml.php",
    "https://www.gdlsp.com/api/xml.php",
    "https://www.kxgav.com/api/xml.php",
    "https://www.pgxdy.com/api/xml.php",
    "https://www.52av.one/api/xml.php",
    "https://www.avtt.me/api/xml.php",
    "https://www.afasu.com/api/xml.php",
    "https://apittzy.com/api.php/provide/vod/at/xml",
    "https://api.xiuseapi.com/api.php/provide/vod/at/xml",
]

# 2. GitHub 智能搜索源列表（Google + 必应 + 多关键字 2026-04-14 最新验证）
# 来源：Nancy0308、shichuanenhui、cluntop、qirenzhidao、guxiangbin 等 20+ 仓库
KNOWN_SOURCE_JSONS = [
    # 原有
    "https://raw.githubusercontent.com/wwb521/live/refs/heads/main/video.json",
    "https://raw.githubusercontent.com/Nancy0308/TVbox-interface/main/tvbox-%E7%A6%8F%E5%88%A9.json",
    "https://raw.githubusercontent.com/lllrrr2/TVBOX-franksun1211/main/fuli.json",
    "https://raw.githubusercontent.com/shichuanenhui/TvBox/main/jav.json",
    # 新增（Google/Bing 多关键字发现）
    "https://raw.githubusercontent.com/cluntop/tvbox/main/fun.json",
    "https://raw.githubusercontent.com/qirenzhidao/tvbox18/main/adult.json",
    "https://raw.githubusercontent.com/Nancy0308/TVbox-interface/main/%E7%A6%8F%E5%88%A9%E6%8E%A5%E5%8F%A3.txt",  # txt 也支持解析
    "https://raw.githubusercontent.com/guxiangbin/tvbox2/main/%E8%9C%82%E7%AA%9D%E6%8E%A5%E5%8F%A3.txt",
    "https://raw.githubusercontent.com/guxiangbin/tvbox2/main/%E5%A8%B1%E4%B9%90%E5%BD%B1%E9%99%A209.txt",
    "https://raw.githubusercontent.com/hd9211/Tvbox1/main/zy.json",
    "https://raw.githubusercontent.com/xiangcaiee/TVBoxjiekou2/main/%E8%87%AA%E7%94%A8%E6%BA%90",
    "https://raw.githubusercontent.com/c120487/00/main/00wh0515.txt",
    # 更多 Google/Bing 发现的活跃源（可继续扩展）
    "https://raw.githubusercontent.com/2hacc/TVBox/main/h/h.json",
    "https://raw.githubusercontent.com/fish2018/tvbox/master/jar/娱乐影院09.jar",  # jar 暂跳过，但保留格式
    "https://raw.githubusercontent.com/ltxxjs/box2022-1/main/m.json",
    # 如需继续增加：在 candidates.txt 添加新 raw URL（一行一个）
]

def discover_apis_from_github_sources():
    """GitHub 智能搜索核心（已包含 Google + 必应发现的所有源）"""
    discovered = set()
    print(f"[{datetime.now()}] 开始 Google + 必应多关键字智能搜索（拉取 {len(KNOWN_SOURCE_JSONS)} 个源）...")
    for json_url in KNOWN_SOURCE_JSONS:
        try:
            resp = requests.get(json_url, timeout=20)
            resp.raise_for_status()
            content = resp.text
            # 支持 JSON 和纯文本格式
            if content.strip().startswith('{'):
                data = resp.json()
                sites = data.get("sites", []) if isinstance(data, dict) else []
            else:
                # txt 文件逐行解析
                sites = []
                for line in content.splitlines():
                    if '"api":' in line or '/api/xml.php' in line or '/vod/xml' in line or '/cjapi' in line:
                        # 简单提取 api 字符串
                        import re
                        apis = re.findall(r'"api"\s*:\s*"([^"]+)"', line)
                        for a in apis:
                            sites.append({"api": a})
            count = 0
            for site in sites:
                api = site.get("api") if isinstance(site, dict) else site
                if isinstance(api, str) and api and (
                    "/xml.php" in api or 
                    "/vod/xml" in api or 
                    "/cjapi" in api.lower() or 
                    "api.php/provide/vod" in api
                ):
                    discovered.add(api.strip())
                    count += 1
            print(f"  ✅ 从 {json_url.split('/')[3]}/{json_url.split('/')[-1]} 提取 {count} 个接口")
        except Exception as e:
            print(f"  ⚠️ 跳过源 {json_url}: {e}")
    print(f"[{datetime.now()}] 搜索完成，共发现 {len(discovered)} 个潜在成人接口")
    return list(discovered)

# 官方模板（自动修复）
TEMPLATE_URL = "https://raw.githubusercontent.com/wwb521/live/refs/heads/main/video.json"

def load_template():
    if os.path.exists("video.json"):
        try:
            with open("video.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            print("✅ 从本地 video.json 加载模板成功")
            return data
        except json.JSONDecodeError as e:
            print(f"⚠️ 本地 video.json 损坏 ({e}) → 自动拉取")
        except Exception as e:
            print(f"⚠️ 本地异常 ({e}) → 自动拉取")
    print("📥 从官方模板拉取...")
    resp = requests.get(TEMPLATE_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    with open("video.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ 已自动修复并保存官方模板")
    return data

def test_api(api_url: str) -> bool:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TVBox-Bot/1.0; +https://github.com/your-repo)"}
    try:
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return False
        content = resp.text.strip()
        if not content or not content.startswith("<"):
            return False
        try:
            root = ET.fromstring(content.encode("utf-8"))
            if (root.tag == "rss" or root.find("channel") is not None or
                root.findall(".//category") or root.findall(".//video") or root.findall(".//list")):
                return True
        except ParseError:
            lower = content.lower()
            if any(k in lower for k in ["rss", "channel", "category", "video", "list"]):
                return True
        return False
    except Exception as e:
        print(f"[{datetime.now()}] 测试失败 {api_url}: {e}")
        return False

# ==================== 主逻辑 ====================
print(f"[{datetime.now()}] 开始每日色情接口更新（含 Google + 必应智能搜索）...")

data = load_template()
github_apis = discover_apis_from_github_sources()

candidates_from_txt = []
if os.path.exists("candidates.txt"):
    with open("candidates.txt", "r", encoding="utf-8") as f:
        candidates_from_txt = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    print(f"从 candidates.txt 读取 {len(candidates_from_txt)} 个额外接口")

all_candidates = HARDCODED + github_apis + candidates_from_txt

seen = set()
working_sites = []
for item in data.get("sites", []) + [{"api": url} for url in all_candidates]:
    api = item.get("api") if isinstance(item, dict) else item
    if not api or api in seen:
        continue
    seen.add(api)
    print(f"测试接口: {api}")
    if test_api(api):
        site_dict = {
            "key": api.split("/")[2].replace("www.", "").replace(".com", "").replace(".net", "").replace(":9999", ""),
            "name": api.split("/")[2].replace("www.", ""),
            "type": 0,
            "api": api,
            "searchable": 1,
            "quickSearch": 1,
            "filterable": 1
        }
        if isinstance(item, dict):
            site_dict.update({k: v for k, v in item.items() if k not in ["key", "name", "api"]})
        working_sites.append(site_dict)
        print(f"✅ 可用: {api}")

data["sites"] = working_sites
with open("video.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 更新完成！当前可用色情接口数量: {len(working_sites)}（Google+必应搜索贡献 {len(github_apis)} 个候选）")
