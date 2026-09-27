"""core 层：纯 Python（不认识 flet）—— 运行时参数、检测算法、自相关引擎

    constants.py    采样率/帧长/门限/判定阈值等（改参数只改这里）
    pitch.py        六弦表 + 音分换算 + PitchAnalyzer（桌面 PitchYIN / 移动自相关）
    tuner_engine.py numpy 自相关引擎（pitch 的兜底分支）
"""
