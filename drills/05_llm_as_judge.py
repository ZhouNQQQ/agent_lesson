"""
手撕题 5：LLM-as-Judge 评分器（pairwise + 位置消偏）（评测方向）

面试场景：A/B 测两个 prompt/模型谁更好。主观质量没法 assert，用更强的模型当裁判。
关键考点：①pairwise 比 pointwise 稳；②必须消除位置偏差（模型偏爱第一个）——
交换 A/B 顺序各评一次取共识；③评分要先理由后结论(CoT)、输出结构化便于聚合。

注：llm.judge(prompt) 是约定省略的 helper，返回模型对评分 prompt 的回答（结构化 JSON）。
"""

import json                                          # 解析裁判模型返回的结构化结果


# 构造评分 prompt：给明确 rubric + 要求先理由后结论 + 输出 JSON
def build_judge_prompt(question, answer_1, answer_2):
    return f"""你是严格的评审。基于"忠实度、相关性、简洁性"评判哪个回答更好。
问题：{question}
回答1：{answer_1}
回答2：{answer_2}
先逐维度给理由，再给结论。只输出 JSON：{{"reason": "...", "winner": 1 或 2 或 0(平局)}}"""   # rubric 明确 + CoT + 结构化输出


# 单次裁判：把两个答案丢给裁判模型，解析出 winner
def judge_once(question, answer_a, answer_b):
    raw = llm.judge(build_judge_prompt(question, answer_a, answer_b))  # 调裁判模型
    return json.loads(raw)["winner"]                # 解析出胜者编号（1=第一个, 2=第二个, 0=平）


# 入口：pairwise 评分 + 位置消偏（核心）
def llm_as_judge(question, answer_a, answer_b):
    # 第一次：A 放前、B 放后
    w1 = judge_once(question, answer_a, answer_b)    # winner 用"位置编号"表示（1=前=A, 2=后=B）
    a_wins = (w1 == 1)                               # 把"位置编号"翻译回"是不是 A 赢"
    b_wins = (w1 == 2)

    # 第二次：交换顺序，B 放前、A 放后（消除位置偏差）
    w2 = judge_once(question, answer_b, answer_a)    # 此时位置1=B, 位置2=A
    a_wins_2 = (w2 == 2)                             # A 现在在位置2，w2==2 才是 A 赢
    b_wins_2 = (w2 == 1)                             # B 现在在位置1，w2==1 才是 B 赢

    # 取两次共识：两次都判 A 赢才算 A 赢，否则视为平局/不确定（保守）
    if a_wins and a_wins_2:                          # 两次一致选 A
        return "A"
    if b_wins and b_wins_2:                          # 两次一致选 B
        return "B"
    return "TIE"                                     # 两次不一致 → 说明有位置偏差/接近，判平局


# ── 面试点（被考察什么）─────────────────────────────────────
# 1. 为什么 pairwise 不用 pointwise：比较两者的一致性比给绝对分高，A/B 测优先 pairwise。
# 2. 为什么要交换顺序评两次：消除"位置偏差"（裁判倾向选第一个）。两次共识才算数。
# 3. 还有哪些偏差：冗长偏差(偏爱长答案,rubric强调简洁)、自我偏好(用不同厂商模型当裁判)。
# 4. 怎么保证可信：和人工打分做一致性校验(Kappa/相关系数)，偏差大就调评分 prompt。
# 5. 串联：这是评测三支柱里"LLM-as-Judge"的落地，配合离线 golden set 做质量门禁。
