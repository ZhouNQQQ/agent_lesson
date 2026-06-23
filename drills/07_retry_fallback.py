"""
手撕题 7：可靠性三件套——重试 + 降级 + 熔断（工程化/可靠性方向）

面试场景：LLM/工具调用会失败(限流/超时/5xx/格式错)。生产 Agent 必须容错。
三件套：①重试(指数退避+抖动,只重试可重试错误) ②降级(切备用,别用Mock顶) ③熔断(失败率超阈值快速失败防雪崩)。
能默写指数退避公式 + 讲清三者分工 + fail-open/closed 就过关。

注：call_primary / call_fallback / is_retryable 是约定省略的 helper。
"""

import time, random                                  # 退避 sleep + 抖动


# ① 重试：指数退避 + 抖动，只重试可重试错误
def with_retry(fn, max_attempts=3, base=0.5):
    for attempt in range(max_attempts):              # 最多尝试 max_attempts 次
        try:
            return fn()                              # 成功直接返回
        except Exception as e:
            if not is_retryable(e):                  # 关键：只重试瞬时/可重试错误(超时/限流/5xx)
                raise                                # 逻辑错误/4xx 重试无意义，直接抛(还会放大故障)
            if attempt == max_attempts - 1:          # 最后一次仍失败 → 抛出，交给上层降级
                raise
            backoff = base * (2 ** attempt)           # 指数退避：0.5, 1, 2 ... 给下游恢复时间
            backoff += random.uniform(0, base)        # 加抖动：避免大量请求同时重试造成"惊群"
            time.sleep(backoff)


# ③ 熔断器：下游持续故障时快速失败，防雪崩
class CircuitBreaker:
    def __init__(self, fail_threshold=5, reset_timeout=30):
        self.fail_count = 0                          # 连续失败计数
        self.fail_threshold = fail_threshold         # 失败超过它 → 打开熔断
        self.reset_timeout = reset_timeout           # 打开后多久进入半开试探
        self.opened_at = None                        # 熔断打开的时间戳

    def call(self, fn):
        # 打开状态：还没到试探时间 → 直接快速失败(不打下游)
        if self.opened_at and time.time() - self.opened_at < self.reset_timeout:
            raise Exception("circuit open: fail fast")  # 快速失败，保护下游也保护自己
        try:
            result = fn()                            # 半开/闭合状态：放行试探
            self.fail_count = 0                      # 成功 → 重置计数(恢复闭合)
            self.opened_at = None
            return result
        except Exception:
            self.fail_count += 1                     # 失败累加
            if self.fail_count >= self.fail_threshold:
                self.opened_at = time.time()         # 超阈值 → 打开熔断
            raise


# 组合入口：熔断包重试，主路径失败再降级
def reliable_call(breaker):
    try:
        # 熔断器 + 重试 包住主路径
        return breaker.call(lambda: with_retry(call_primary))
    except Exception:
        # ② 降级：主路径不可用 → 切备用模型/缓存/诚实报错(不要用 Mock 假数据硬顶)
        return call_fallback()


# ── 面试点（被考察什么）─────────────────────────────────────
# 1. 为什么指数退避+抖动：退避给下游恢复时间；抖动防大量请求同时重试的"惊群效应"。
# 2. 为什么不是所有错都重试：只重试瞬时错(超时/限流/5xx)；逻辑错/4xx 重试无用且放大故障。
# 3. 熔断解决什么：下游持续挂时，继续打它只会雪崩+浪费；快速失败保护双方，半开试探恢复。
# 4. 降级正确姿势：切备用模型/返回缓存/诚实报错转人工；Mock 基于关键词无法处理真实语言,不能顶生产。
# 5. fail-open vs fail-closed：非关键增强(记忆)失败 fail-open 保可用；安全/权限/扣费失败 fail-closed 保正确。
# 6. 三者分工：重试治瞬时抖动，熔断治持续故障防雪崩，降级保证总有兜底结果。
