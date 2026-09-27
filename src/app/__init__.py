"""app 层：界面（只放 UI，不认识采集/检测细节）

    app.py      路由表 + 页面初始化（main() 里 page.render_views(App)）
    layout.py   壳：顶栏 + 路由出口 + 底部玻璃条（导航 + 按钮胶囊）
    theme.py    两套调色板 + 毛玻璃配方 + 尺寸常量

界面之外：core/（纯 Python 算法与常量）、models/（可观察状态）、services/（编排）、
components/ 与 pages/（叶子控件与路由页）。
"""
