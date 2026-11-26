# 知健 2.0 · 竞赛演示版

知健提供简易评估与综合健康评估两条研究演示路径。演示数据来自内置的 11 个虚构案例。访客可以选择案例、模式和语言，案例的健康字段只读。应用不提供个人健康信息录入、文件上传或账户注册功能。

## 本地启动

在仓库根目录使用 Python 3.11。

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8517
```

## Streamlit Community Cloud

在 Community Cloud 选择此仓库、发布分支和 `streamlit_app.py`，并选择 Python 3.11。仓库根目录的 `requirements.txt` 和 `.streamlit/config.toml` 分别提供依赖和显示设置。应用无需填写 Secrets。`models/` 中的冻结模型、阈值与 SHAP 基准按文件字节校验，请保留原件。

## 研究用途

演示保留适用人群门槛、年龄证据限制和独立血压安全提醒。演示输出不用于医学诊断、排除异常或替代正规检查。SHAP 贡献用于说明模型输出，无法用于判断疾病原因或干预收益。模型尚未完成中国人群验证或临床验证。
