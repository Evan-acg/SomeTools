from .main import textParse


def test_text_end_with_comma() -> None:
    source: list[str] = [
        "你好呀，我是一个文本，",
        "我是第二个文本。",
    ]

    expected: str = "你好呀，我是一个文本，我是第二个文本。"
    result: str = textParse(source)
    assert expected == result


def test_text_end_with_str() -> None:
    source: list[str] = [
        "只见她裙下交错，修长的玉腿踮跳弹动，柔媚的腿部线条充满弹",
        "性，娇小的身影在亭中不住飞转，饱满的胸脯晃荡如波，柱中叮叮咚咚",
        "的乐音如奏扬琴，旋律连绵不绝。",
        "横疏影舞姿曼妙，虽一手拎着裙幅，另一手还要不时轻拍慢点、伴",
        "奏合音，却更显身段玲珑，宛若水上仙子。",
    ]

    expected: str = "只见她裙下交错，修长的玉腿踮跳弹动，柔媚的腿部线条充满弹性，娇小的身影在亭中不住飞转，饱满的胸脯晃荡如波，柱中叮叮咚咚的乐音如奏扬琴，旋律连绵不绝。\n横疏影舞姿曼妙，虽一手拎着裙幅，另一手还要不时轻拍慢点、伴奏合音，却更显身段玲珑，宛若水上仙子。"
    result: str = textParse(source)
    assert expected == result


def test_text_end_with_str_2() -> None:
    source: list[str] = [
        "风过韵收，穿着半湿薄纱的娇小丽人盈盈下拜，飘开缓落的裙幅在",
        "水面上摊成一个雪白的圆；奶白色的雪肌从湿透的白纱里透出来，姣好",
        "的胴体曲线若隐若现，眩目得令人无法逼视。",
        "直到推动人偶的水力机关渐止，舞俑越动越慢，接连停下，亭子里",
        "才爆出连串采声，独孤天威大声鼓掌叫好，举杯道：“好、好！不愧是",
        "我的小影儿！来来，本座赏酒！”",
    ]

    expected: str = "风过韵收，穿着半湿薄纱的娇小丽人盈盈下拜，飘开缓落的裙幅在水面上摊成一个雪白的圆；奶白色的雪肌从湿透的白纱里透出来，姣好的胴体曲线若隐若现，眩目得令人无法逼视。\n直到推动人偶的水力机关渐止，舞俑越动越慢，接连停下，亭子里才爆出连串采声，独孤天威大声鼓掌叫好，举杯道：“好、好！不愧是我的小影儿！来来，本座赏酒！”"
    result: str = textParse(source)
    assert expected == result
