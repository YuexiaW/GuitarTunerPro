import flet.testing as ftt


async def test_tuner_initial_state(flet_app: ftt.FletTestApp):
    """初始渲染: 标题、6 根琴弦按钮、开始按钮都在, 默认自动检测模式"""
    tester = flet_app.tester
    await tester.pump_and_settle()

    assert (await tester.find_by_text("吉他调音器")).count == 1
    assert (await tester.find_by_text("🔄 自动检测模式")).count == 1
    assert (await tester.find_by_text("开始调音")).count == 1
    assert (await tester.find_by_key("start_btn")).count == 1
    for i in range(6):
        assert (await tester.find_by_key(f"str_{i}")).count == 1


async def test_string_selection_locks_target(flet_app: ftt.FletTestApp):
    """点击琴弦按钮锁定目标弦, 再点一次回到自动检测"""
    tester = flet_app.tester
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("str_0"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("🎯 锁定 6弦 E2 · 82.4 Hz")).count == 1

    await tester.tap(await tester.find_by_key("str_0"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("🔄 自动检测模式")).count == 1


async def test_string_selection_switches_between_strings(flet_app: ftt.FletTestApp):
    """切换锁定目标: 6弦 → 1弦"""
    tester = flet_app.tester
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("str_5"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("🎯 锁定 1弦 E4 · 329.6 Hz")).count == 1
