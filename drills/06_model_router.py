"""
手撕题 6：多模型级联路由（Cascade Routing）（工程化/成本方向）

面试场景：省钱——简单请求停在便宜小模型，难的才升级到贵的大模型。
核心是"级联+置信门控"：小模型先答，若置信度够 → 直接返回（省钱）；
不够 → 升级大模型重做。大部分简单请求停在便宜档，整体成本大降、质量不掉。

注：small_model.run / big_model.run 返回 (answer, confidence)，confidence∈[0,1]，约定省略。
"""


# 入口：请求、置信阈值（低于它就升级）
def cascade_route(request, confidence_threshold=0.7):
    # 第一级：便宜的小模型先跑
    answer, confidence = small_model.run(request)    # 小模型给出答案 + 自评置信度(logprob/自评分/校验是否通过)

    # 置信门控：够好就停在小模型（省钱省时的主路径）
    if confidence >= confidence_threshold:           # 大部分简单请求应命中这里
        return {
            "answer": answer,
            "model": "small",                        # 记录走了哪个模型 → 可观测，用于事后调阈值
            "escalated": False,
        }

    # 第二级：小模型不自信 → 升级到大模型重做（用少量成本换质量）
    answer_big, _ = big_model.run(request)           # 大模型重新回答
    return {
        "answer": answer_big,
        "model": "big",
        "escalated": True,                           # 标记升级了，便于统计升级率/成本
    }


# 进阶：按"能力/类型"先做一次规则路由，再在档内级联
def route_by_type(request):
    if request.type == "code":                       # 代码任务 → 代码专长模型
        return code_model.run(request)
    if request.tokens > 100_000:                     # 超长上下文 → 长上下文模型
        return long_ctx_model.run(request)
    return cascade_route(request)                    # 普通文本 → 走级联（小→大）


# ── 面试点（被考察什么）─────────────────────────────────────
# 1. 级联怎么判断要不要升级：用置信信号——小模型 logprob / 自评分 / 答案是否通过校验(如 Faithfulness)，
#    低于阈值就升级。本质用一点延迟+成本换整体质量。
# 2. 为什么省钱：简单请求(占多数)停在便宜小模型，只有少数难的才烧大模型。
# 3. 阈值怎么定：不是拍脑袋——记录每请求走了哪个模型+成本+质量(可观测)，用评测集找"成本↓但质量不掉"的拐点。
# 4. 路由 vs 降级别混：路由是正常按需分发；降级是故障时兜底切换。触发条件不同。
# 5. 串联：配合可观测性(模块5)记录路由分布，配合成本优化(模块7)。
