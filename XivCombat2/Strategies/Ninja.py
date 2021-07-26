from FFxivPythonTrigger.Utils import circle
from ..Strategy import *
from .. import Define

"""
2240,双刃旋,1
2241,残影,2
2242,绝风,4
7541,内丹,8
2245,隐遁,10
7863,扫腿,10
7542,浴血,12
2247,飞刀,15
2248,夺取,15
2258,攻其不备,18
7549,牵制,22
2255,旋风刃,26
2257,影牙,30
2259,天之印,30
2260,忍术,30
2265,风魔手里剑,30
2272,通灵之术,30
18805,天之印,30
18873,风魔手里剑,30
18874,风魔手里剑,30
18875,风魔手里剑,30
7548,亲疏自行,32
2261,地之印,35
2266,火遁之术,35
2267,雷遁之术,35
18806,地之印,35
18876,火遁之术,35
18877,雷遁之术,35
2254,血雨飞花,38
2262,缩地,40
2263,人之印,45
2268,冰遁之术,45
2269,风遁之术,45
2270,土遁之术,45
2271,水遁之术,45
18807,人之印,45
18878,冰遁之术,45
18879,风遁之术,45
18880,土遁之术,45
18881,水遁之术,45
2264,生杀予夺,50
7546,真北,50
16488,八卦无刃杀,52
3563,强甲破点突,54
3566,梦幻三段,56
2246,断绝,60
7401,通灵之术·大虾蟆,62
7402,六道轮回,68
7403,天地人,70
16489,命水,72
16491,劫火灭却之术,76
16492,冰晶乱流之术,76
16493,分身之术,80
17413,双刃旋,80
17414,绝风,80
17415,旋风刃,80
17416,影牙,80
17417,强甲破点突,80
17418,飞刀,80
17419,血雨飞花,80
17420,八卦无刃杀,80
"""
"""
1955,"断绝预备","可以发动断绝"
496,"结印","结成手印准备发动忍术"
507,"水遁之术","不用隐遁身形也能够发动需要在隐遁状态下发动的技能"
501,"土遁之术","产生土属性攻击区域"
497,"生杀予夺","可以发动忍术并且忍术的威力提升"
1186,"天地人","可以连发忍术"
"""

TEN = 3  # 天
CHI = 2  # 地
JIN = 1  # 人


def get_mudra(effects: dict):
    if 496 not in effects:
        return ""
    p = effects[496].param
    s = ''
    for i in range(4):
        m = (p >> (i * 2)) & 0b11
        if m:
            s += str(m)
        else:
            break
    return s


m2s = {
    TEN: 2259,
    CHI: 2261,
    JIN: 2263,
}


def c(*mudras: int):
    # return sum(m << (i * 2) for i, m in enumerate(mudras))
    # return ''.join(map(str, mudras))
    return [m2s[m] for m in mudras]


combos = {
    'normal': c(TEN),
    'fire': c(CHI, TEN),
    'thunder': c(TEN, CHI),
    'ice': c(TEN, JIN),
    'wind': c(JIN, CHI, TEN),
    'ground': c(JIN, TEN, CHI),
    'water': c(TEN, CHI, JIN),
}


def count_enemy(data: LogicData, skill_type: int):
    """
    :param skill_type: 0:普通 1:蛤蟆 2:火遁
    """
    if data.config.single == Define.FORCE_SINGLE: return 1
    if data.config.single == Define.FORCE_MULTI: return 3
    if skill_type == 0:
        aoe = circle(data.me.pos.x, data.me.pos.y, 5)
    elif skill_type == 1:
        aoe = circle(data.target.pos.x, data.target.pos.y, 6)
    else:
        aoe = circle(data.target.pos.x, data.target.pos.y, 5)
    return sum(map(lambda x: aoe.intersects(x.hitbox), data.valid_enemies))


def res_lv(data: LogicData) -> int:
    if data.config.resource == Define.RESOURCE_SQUAND:
        return 2
    elif data.config.resource == Define.RESOURCE_NORMAL:
        return 1
    elif data.config.resource == Define.RESOURCE_STINGY:
        return 0
    return int(data.max_ttk > 5)


class NinjaLogic(Strategy):
    name = "ninja_logic"

    def __init__(self, config: 'CombatConfig'):
        super().__init__(config)
        self.combo = []

    def common(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        if self.combo:
            return UseAbility(self.combo.pop(0))
        elif 496 in data.effects:
            return UseAbility(2260)

    def global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        _res_lv = res_lv(data)
        use_res = _res_lv and (data[2258] > 45 or data.me.level < 45)
        cnt0 = count_enemy(data, 0)
        cnt2 = count_enemy(data, 2)
        if 497 in data.effects:
            if data.me.level >= 76:
                self.combo = combos['fire'].copy() if cnt2 > 1 else combos['ice'].copy()
            elif cnt2 > 1:
                self.combo = combos['ground'].copy() if data.max_ttk > 15 and 501 not in data.effects else combos['fire'].copy()
            else:
                self.combo = combos['thunder'].copy()
        elif 1186 in data.effects:
            self.combo = combos['ground'].copy() if cnt2 > 1 and 501 not in data.effects else combos['water'].copy()
        elif data[2259] <= 20:
            if data.me.level >= 45:
                if not data.gauge.hutonMilliseconds:
                    self.combo = combos['wind'].copy()
                elif _res_lv:
                    if data[2258] < 15 and 507 not in data.effects:
                        self.combo = combos['water'].copy()
                    elif cnt0 > 2 and data.max_ttk > 15 and 501 not in data.effects:
                        self.combo = combos['ground'].copy()
            if not self.combo and _res_lv and (use_res or data[2259] < 5):
                if data.me.level >= 35:
                    self.combo = combos['fire'].copy() if cnt2 > 1 else combos['thunder'].copy()
                else:
                    self.combo = combos['normal'].copy()
        if self.combo: return UseAbility(self.combo.pop(0))
        if cnt0 > 2 and data.me.level >= 38:
            return UseAbility(16488 if data.combo_id == 2254 and data.me.level >= 52 else 2254)
        if data.target_distance > 3: return
        if not data[2257] and use_res: return UseAbility(2257)
        if data.combo_id == 2242 and data.me.level >= 26:
            if data.me.level >= 54 and data.gauge.hutonMilliseconds and data.gauge.hutonMilliseconds/1000 < 30:
                return UseAbility(3563)
            return UseAbility(2255)
        if data.combo_id == 2240 and data.me.level >= 4:
            return UseAbility(2242)
        return UseAbility(2240)

    def non_global_cool_down_ability(self, data: LogicData) -> Optional[Union[UseAbility, UseItem, UseCommon]]:
        _res_lv = res_lv(data)
        if not _res_lv or not count_enemy(data, 0): return
        use_res = _res_lv and (data[2258] > 45 or data.me.level < 45)
        if not data[2248] and data.gauge.ninkiAmount <= 60:
            return UseAbility(2248)
        if data.gauge.ninkiAmount >= 50 and (use_res or data.gauge.ninkiAmount > (60 if not data[2248] else 80)):
            return UseAbility(7402) if data.me.level >= 68 and count_enemy(data, 1) > 1 else UseAbility(7401)
        if not data[16493] and data.gauge.ninkiAmount >= 50:
            return UseAbility(16493)
        if not data[2258] and data[16493] and 507 in data.effects:
            return UseAbility(2258)
        if not data[3566] and use_res:
            return UseAbility(3566)
        if data.me.level >= 60 and 1955 in data.effects:
            return UseAbility(2246)
        if not data[2264] and use_res:
            return UseAbility(2264)
        if not data[7403] and use_res and 497 not in data.effects:
            return UseAbility(7403)
        if not data[16489] and data[2258] > 20 and 507 in data.effects:
            return UseAbility(16489)