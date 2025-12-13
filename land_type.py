import os
import requests
import pandas as pd
import random
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import folium
from folium import Icon
# 新增：导入聚类插件（标记密集时自动合并）
from folium.plugins import MarkerCluster

# ========== 核心配置 ==========
AMAP_API_KEY = "390d21c5790b69dbd0fa8cfd3cf03d05"  # 替换成你申请的Key
DEFAULT_SAMPLE_NUM = 50  # 标记点数量：从15改成50（可自定义）

# ========== 1. 村庄名转经纬度（不变） ==========
def 村庄转经纬度(村庄名):
    url = f"https://restapi.amap.com/v3/geocode/geo?address={村庄名}&output=json&key={AMAP_API_KEY}"
    try:
        response = requests.get(url)
        result = response.json()
        if result['status'] == '1' and len(result['geocodes']) > 0:
            lon, lat = result['geocodes'][0]['location'].split(',')
            return float(lon), float(lat)
        else:
            print(f"❌ 没找到{村庄名}的地理信息，使用默认坐标（成都郫都区）")
            return 103.8125, 30.8642
    except Exception as e:
        print(f"❌ 获取坐标失败：{e}，使用默认坐标")
        return 103.8125, 30.8642

# ========== 2. 生成更多、更真实的土地数据 ==========
def 生成村庄土地数据(村庄中心经纬度, 样本数=DEFAULT_SAMPLE_NUM):
    lon_center, lat_center = 村庄中心经纬度
    土地数据列表 = []
    # 把“sample数”改成“样本数”（和参数名一致）
    分类标签 = [0]*int(样本数/3) + [1]*int(样本数/3) + [2]*(样本数 - 2*int(样本数/3))
    random.shuffle(分类标签)  # 打乱分类，避免集中分布
    
    for i in range(样本数):  # 这里也是“样本数”
        分类 = 分类标签[i]
        # 后续代码不变...
        # 扩大分布范围（±0.03度，约3公里），避免标记重叠
        lon = lon_center + random.uniform(-0.03, 0.03)
        lat = lat_center + random.uniform(-0.03, 0.03)
        
        # 按分类生成更精准的特征值，符合真实逻辑
        if 分类 == 0:  # 适合种地
            土壤肥力 = round(random.uniform(0.8, 0.95), 2)
            坡度 = round(random.uniform(3, 8), 1)
            到公路距离 = round(random.uniform(0.3, 1.2), 2)
        elif 分类 == 1:  # 适合旅游
            土壤肥力 = round(random.uniform(0.4, 0.65), 2)
            坡度 = round(random.uniform(9, 16), 1)
            到公路距离 = round(random.uniform(1.5, 3.5), 2)
        else:  # 没法开发
            土壤肥力 = round(random.uniform(0.1, 0.35), 2)
            坡度 = round(random.uniform(17, 28), 1)
            到公路距离 = round(random.uniform(3.8, 5.0), 2)
        
        # 新增：模拟更多土地属性，让弹窗更详细
        土地面积 = round(random.uniform(0.5, 5.0), 1)  # 亩
        海拔 = round(random.uniform(500, 800), 0)       # 米
        灌溉条件 = random.choice(['完善', '一般', '缺失'])
        
        土地数据列表.append({
            'land_id': f"L{str(i+1).zfill(3)}",
            'soil_fertility': 土壤肥力,
            'slope': 坡度,
            'road_distance': 到公路距离,
            'lon': lon,
            'lat': lat,
            'area': 土地面积,       # 新增：土地面积
            'altitude': 海拔,       # 新增：海拔
            'irrigation': 灌溉条件  # 新增：灌溉条件
        })
    return pd.DataFrame(土地数据列表)

# ========== 3. 生成更详细的标记+更多标记点 ==========
def 生成村庄土地分析结果(村庄名):
    # Step1：获取村庄坐标
    村庄经纬度 = 村庄转经纬度(村庄名)
    print(f"✅ 获取{村庄名}中心坐标：{村庄经纬度}")
    
    # Step2：生成更多土地数据
    df = 生成村庄土地数据(村庄经纬度)
    df_complete = df.copy()
    
    # Step3：分类逻辑（不变）
    特征列 = ['soil_fertility', 'slope', 'road_distance']
    处理工具 = StandardScaler()
    处理后的数据 = 处理工具.fit_transform(df[特征列])
    分类工具 = KMeans(n_clusters=3, random_state=42)
    df_complete['分类结果'] = 分类工具.fit_predict(处理后的数据)
    
    # Step4：分类建议（不变）
    详细建议 = {
        0: {'类型': '适合种地','核心特征': '土壤肥力高、坡度小、离公路近',
            '详细发展方向': '''1. 粮食作物：小麦、水稻、玉米（规模化机械化种植）；
2. 经济作物：大棚蔬菜、草莓、蓝莓（高收益果蔬）；
3. 特色种植：有机杂粮、中药材（绿色认证溢价）；
落地建议：配套滴灌系统，对接本地农贸市场/社区团购，利用公路优势降低运输成本。'''},
        1: {'类型': '适合旅游','核心特征': '肥力中等、坡度适中、离公路距离适中',
            '详细发展方向': '''1. 休闲体验：农家乐、采摘园、亲子农场（季节性运营）；
2. 生态观光：梯田花海、森林步道、星空露营地（轻资产开发）；
3. 研学教育：自然课堂、农耕体验基地（对接中小学/培训机构）；
落地建议：修建简易停车场和休息区，控制开发强度，保留原生态景观。'''},
        2: {'类型': '没法开发','核心特征': '肥力极低、坡度极陡/过平、离公路过远',
            '详细发展方向': '''1. 生态修复：种植固土植被（如柠条、沙棘），治理水土流失；
2. 保护性利用：设为野生植物/动物栖息地，禁止开荒或工程建设；
3. 政策对接：申报生态保护地块，获取政府生态补贴；
落地建议：定期监测土壤和植被状态，仅开展低干扰的生态维护工作。'''}
    }
    df_complete['土地类型'] = df_complete['分类结果'].map(lambda x: 详细建议[x]['类型'])
    
    # Step5：生成地图（关键修改：更多标记+更详细弹窗+聚类）
    分类样式 = {0: {'color': 'green', 'icon': 'leaf'},
                 1: {'color': 'blue', 'icon': 'camera'},
                 2: {'color': 'red', 'icon': 'ban'}}
    
    # 地图中心设为村庄，缩放级别13（适配更多标记）
    land_map = folium.Map(location=[村庄经纬度[1], 村庄经纬度[0]],
                          zoom_start=13,
                          tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                          attr='高德地图')
    
    # 新增：添加聚类插件（标记密集时自动合并，点击展开）
    marker_cluster = MarkerCluster().add_to(land_map)
    
    # 遍历所有土地，添加更详细的标记
    for idx, row in df_complete.iterrows():
        # 弹窗内容：新增土地面积、海拔、灌溉条件等细节，格式更清晰
        popup_content = f"""
        <div style="font-size:14px; line-height:1.5;">
            <h4 style="margin:0; color:#333;">土地ID：{row['land_id']}</h4>
            <hr style="margin:5px 0; border:none; border-top:1px solid #eee;">
            <p><strong>分类结果：</strong>{详细建议[row['分类结果']]['类型']}</p>
            <p><strong>核心特征：</strong>{详细建议[row['分类结果']]['核心特征']}</p>
            <p><strong>具体属性：</strong><br>
               土壤肥力：{row['soil_fertility']}（0-1）<br>
               坡度：{row['slope']} 度<br>
               到公路距离：{row['road_distance']} 公里<br>
               土地面积：{row['area']} 亩<br>
               海拔：{row['altitude']} 米<br>
               灌溉条件：{row['irrigation']}
            </p>
            <p><strong>发展建议：</strong><br>
               {详细建议[row['分类结果']]['详细发展方向']}
            </p>
        </div>
        """
        # 把标记添加到聚类插件中（避免重叠）
        folium.Marker(
            location=[row['lat'], row['lon']],
            # 新增：hover时显示土地类型（不用点击就能看到）
            tooltip=f"{row['land_id']} - {详细建议[row['分类结果']]['类型']}",
            popup=folium.Popup(popup_content, max_width=500),  # 加宽弹窗，显示更多内容
            icon=Icon(
                color=分类样式[row['分类结果']]['color'],
                icon=分类样式[row['分类结果']]['icon'],
                icon_size=(20, 20)  # 稍微放大图标，更显眼
            )
        ).add_to(marker_cluster)  # 添加到聚类，而非直接添加到地图
    
    # Step6：保存结果
    地图文件名 = f"{村庄名}土地分类地图.html"
    land_map.save(地图文件名)
    print(f"\n==== {村庄名}土地分类结果（共{DEFAULT_SAMPLE_NUM}个地块） ====")
    print(df_complete[['land_id', 'soil_fertility', 'slope', 'road_distance', 'area', '土地类型']].head(10))  # 显示前10行
    print(f"\n✅ {村庄名}专属地图已生成：{地图文件名}")
    return df_complete, 地图文件名

# ========== 主程序 ==========
if __name__ == "__main__":
    村庄名 = input("请输入你要分析的村庄名称：")
    生成村庄土地分析结果(村庄名)