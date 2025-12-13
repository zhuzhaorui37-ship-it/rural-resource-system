import pickle
from pathlib import Path

Path("models").mkdir(exist_ok=True)

dummy = {
    "type": "demo",
    "desc": "展示级土地模型"
}

with open("models/土地处理工具.pkl", "wb") as f:
    pickle.dump(dummy, f)

with open("models/土地分类类型工具.pkl", "wb") as f:
    pickle.dump(dummy, f)

print("✅ 已生成干净的 pickle 模型")

