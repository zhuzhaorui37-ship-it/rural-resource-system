# =====================================================
# product_resource.py
# 村庄资源 / 产品 / 人文综合展示模块（HTML 稳定输出版）
# =====================================================

import requests
import random
import folium
from folium import Icon
from folium.plugins import MarkerCluster
import tempfile
import os

# =====================================================
# 核心配置
# =====================================================
AMAP_API_KEY = "390d21c5790b69dbd0fa8cfd3cf03d05"

# =====================================================
# 1. 村庄名 → 经纬度
# =====================================================
def 村庄转经纬度(村庄名: str):
    url = (
        "https://restapi.amap.com/v3/geocode/geo"
        f"?address={村庄名}&output=json&key={AMAP_API_KEY}"
    )
    try:
        res = requests.get(url, timeout=5).json()
        if res.get("status") == "1" and res.get("geocodes"):
            lon, lat = res["geocodes"][0]["location"].split(",")
            return float(lon), float(lat)
    except Exception:
        pass

    return 103.8125, 30.8642


# =====================================================
# 2. 生成村庄综合信息（主体逻辑不动）
# =====================================================
def 生成村庄综合信息(村庄名, 村庄经纬度):
    lon_c, lat_c = 村庄经纬度

    资源类型列表 = [
        {"类型": "土地资源", "子类型": "耕地", "描述": "优质耕地", "指标": f"{random.randint(500, 2000)} 亩"},
        {"类型": "土地资源", "子类型": "林地", "描述": "天然林地", "指标": f"{random.randint(1000, 3000)} 亩"},
        {"类型": "水资源", "子类型": "河流", "描述": "常年河流", "指标": f"{random.randint(2, 8)} 公里"},
        {"类型": "水资源", "子类型": "水库", "描述": "小型水库", "指标": f"{random.randint(5, 20)} 万立方米"},
    ]

    产品类型列表 = [
        {"类型": "农产品", "子类型": "特色水果", "描述": "樱桃、枇杷", "指标": f"{random.randint(50, 200)} 吨/年"},
        {"类型": "农产品", "子类型": "粮油作物", "描述": "水稻、油菜", "指标": f"{random.randint(100, 500)} 吨/年"},
        {"类型": "手工艺品", "子类型": "竹编", "描述": "传统竹编", "指标": f"{random.randint(10, 50)} 万元/年"},
    ]

    人文类型列表 = [
        {"类型": "人口结构", "描述": f"人口约 {random.randint(800, 3000)} 人"},
        {"类型": "民俗文化", "描述": "农耕文化节"},
        {"类型": "历史古迹", "描述": "古桥、古树"},
        {"类型": "文旅设施", "描述": "农家乐、民宿"},
    ]

    def 偏移():
        return random.uniform(-0.02, 0.02)

    点位 = []

    for r in 资源类型列表:
        点位.append({
            "类别": "资源",
            "名称": f"{r['类型']} - {r['子类型']}",
            "描述": f"{r['描述']}（{r['指标']}）",
            "lon": lon_c + 偏移(),
            "lat": lat_c + 偏移(),
            "颜色": "green",
            "图标": "tree"
        })

    for p in 产品类型列表:
        点位.append({
            "类别": "产品",
            "名称": f"{p['类型']} - {p['子类型']}",
            "描述": f"{p['描述']}（{p['指标']}）",
            "lon": lon_c + 偏移(),
            "lat": lat_c + 偏移(),
            "颜色": "orange",
            "图标": "gift"
        })

    for h in 人文类型列表:
        点位.append({
            "类别": "人文",
            "名称": h["类型"],
            "描述": h["描述"],
            "lon": lon_c + 偏移(),
            "lat": lat_c + 偏移(),
            "颜色": "purple",
            "图标": "users"
        })

    summary = {
        "村庄名称": 村庄名,
        "地理坐标": f"经度 {lon_c:.4f}，纬度 {lat_c:.4f}",
        "资源概况": "；".join([f"{r['类型']}-{r['子类型']}" for r in 资源类型列表]),
        "产品概况": "；".join([f"{p['类型']}-{p['子类型']}" for p in 产品类型列表]),
        "人文概况": "；".join([h["类型"] for h in 人文类型列表]),
    }

    return summary, 点位


# =====================================================
# 3. 生成 Folium 地图（核心逻辑不动）
# =====================================================
def 生成村庄资源分布(村庄名: str):
    lon, lat = 村庄转经纬度(村庄名)
    summary, 点位列表 = 生成村庄综合信息(村庄名, (lon, lat))

    m = folium.Map(location=[lat, lon], zoom_start=13)

    layers = {
        "资源": MarkerCluster(name="资源分布").add_to(m),
        "产品": MarkerCluster(name="产品分布").add_to(m),
        "人文": MarkerCluster(name="人文分布").add_to(m),
    }

    for p in 点位列表:
        folium.Marker(
            [p["lat"], p["lon"]],
            popup=f"<b>{p['名称']}</b><br>{p['描述']}",
            tooltip=f"{p['类别']}：{p['名称']}",
            icon=Icon(color=p["颜色"], icon=p["图标"], prefix="fa")
        ).add_to(layers[p["类别"]])

    folium.LayerControl().add_to(m)
    return m, summary


# =====================================================
# 4️⃣ ⭐ Streamlit 专用：HTML 输出接口（已修复）
# =====================================================
def get_resource_map_for_streamlit(村庄名):
    """
    返回：
    - html 字符串
    - summary dict
    """
    m, summary = 生成村庄资源分布(村庄名)

    tmp = tempfile.NamedTemporaryFile(
        mode="w",           # ✅ 关键修复
        delete=False,
        suffix=".html",
        encoding="utf-8"
    )

    m.save(tmp.name)
    tmp.close()

    with open(tmp.name, "r", encoding="utf-8") as f:
        html = f.read()

    os.unlink(tmp.name)
    return html, summary


# =====================================================
# 本地测试
# =====================================================
if __name__ == "__main__":
    html, s = get_resource_map_for_streamlit("测试村庄")
    with open("测试村庄_资源分布.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(s)
