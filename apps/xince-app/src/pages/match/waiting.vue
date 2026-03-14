<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { onLoad, onShareAppMessage, onShareTimeline } from "@dcloudio/uni-app";

import type { MatchInviteDetail } from "@/shared/models/match";
import { ensureAppSession } from "@/shared/services/auth";
import { fetchMatchInviteDetail } from "@/shared/services/match";

const sessionId = ref(0);
const code = ref("");
const loading = ref(false);
const invite = ref<MatchInviteDetail | null>(null);
const error = ref("");
let pollTimer: ReturnType<typeof setInterval> | null = null;

async function loadInvite() {
  if (!code.value) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    const payload = await fetchMatchInviteDetail(code.value);
    invite.value = payload;
    if (payload.status === "COMPLETED") {
      stopPolling();
      uni.redirectTo({
        url: `/pages/match/report?sessionId=${payload.session_id}`,
      });
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "等待页加载失败";
  } finally {
    loading.value = false;
  }
}

function copyCode() {
  if (!invite.value?.invite_code) {
    return;
  }
  uni.setClipboardData({
    data: invite.value.invite_code,
  });
}

function openInvite() {
  if (!code.value) {
    return;
  }
  uni.navigateTo({
    url: `/pages/match/invite?code=${code.value}`,
  });
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => {
    void loadInvite();
  }, 3000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

onLoad((query) => {
  sessionId.value = Number(query?.sessionId || 0);
  code.value = typeof query?.code === "string" ? query.code : "";
});

onMounted(() => {
  void loadInvite();
  startPolling();
});

onBeforeUnmount(stopPolling);

onShareAppMessage(() => ({
  title: invite.value
    ? `我在心测发起了「${invite.value.test_name}」灵魂匹配`
    : "来心测看看我们的灵魂匹配度",
  path: `/pages/match/invite?code=${code.value}`,
}));

onShareTimeline(() => ({
  title: invite.value
    ? `${invite.value.test_name} 灵魂匹配进行中`
    : "心测灵魂匹配邀请",
  query: `code=${code.value}`,
}));
</script>

<template>
  <view class="page">
    <view v-if="loading && !invite" class="panel">
      <text class="panel__text">正在等待对方进入这场灵魂匹配...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__title">同步失败</text>
      <text class="panel__text">{{ error }}</text>
      <button class="panel__button" @tap="loadInvite">重新同步</button>
    </view>

    <view v-else class="stack">
      <view class="hero">
        <text class="hero__eyebrow">Waiting Room</text>
        <text class="hero__title">邀请已发出，正在等待另一颗星靠近。</text>
        <text class="hero__body">
          {{ invite?.partner_joined ? "好友已加入，正在生成匹配结果。" : "把邀请码发给好友，等 TA 完成同一测试后就会自动点亮匹配结果。" }}
        </text>
      </view>

      <view class="panel panel--code">
        <text class="panel__title">邀请码</text>
        <text class="code">{{ invite?.invite_code || code }}</text>
        <view class="button-row">
          <button class="panel__button" @tap="copyCode">复制邀请码</button>
          <button class="panel__button panel__button--ghost" @tap="openInvite">查看邀请页</button>
        </view>
        <!-- #ifdef MP-WEIXIN -->
        <button class="panel__button panel__button--share" open-type="share">分享到微信</button>
        <!-- #endif -->
      </view>

      <view class="panel">
        <text class="panel__title">当前状态</text>
        <text class="panel__text">
          {{ invite?.partner_joined ? "已检测到对方进入匹配，结果整理完成后会自动跳转。" : "还没有人加入这次匹配，我们会每 3 秒自动同步一次。" }}
        </text>
      </view>

      <view class="orbit">
        <view class="orbit__ring" />
        <view class="orbit__planet orbit__planet--left">🪐</view>
        <view class="orbit__planet orbit__planet--right">{{ invite?.partner_joined ? "🌙" : "✨" }}</view>
      </view>

      <text class="footnote">会话 ID：{{ sessionId }}</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx 24rpx 40rpx;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.hero,
.panel {
  padding: 28rpx;
  border-radius: 26rpx;
  background: rgba(255, 252, 247, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  box-shadow: $xc-shadow;
}

.panel--error {
  background: rgba(255, 240, 235, 0.96);
}

.hero__eyebrow,
.hero__body,
.panel__text,
.footnote {
  color: $xc-muted;
}

.hero__eyebrow {
  display: block;
  font-size: 22rpx;
  letter-spacing: 3rpx;
  text-transform: uppercase;
}

.hero__title,
.panel__title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
}

.hero__title {
  margin-top: 14rpx;
}

.hero__body,
.panel__text,
.footnote {
  display: block;
  margin-top: 14rpx;
  font-size: 25rpx;
  line-height: 1.7;
}

.code {
  display: block;
  margin-top: 18rpx;
  text-align: center;
  font-size: 54rpx;
  letter-spacing: 10rpx;
  font-weight: 700;
  color: #9B7ED8;
}

.button-row {
  display: flex;
  gap: 16rpx;
  margin-top: 18rpx;
}

.panel__button {
  flex: 1;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #E8729A, #9B7ED8);
  color: #fff8f2;
  font-size: 24rpx;
}

.panel__button--ghost {
  background: rgba(155, 126, 216, 0.12);
  color: #9B7ED8;
}

.panel__button--share {
  margin-top: 16rpx;
}

.orbit {
  position: relative;
  height: 280rpx;
  border-radius: 26rpx;
  background: linear-gradient(180deg, rgba(255, 245, 233, 0.9), rgba(255, 251, 246, 0.98));
  overflow: hidden;
}

.orbit__ring {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 360rpx;
  height: 160rpx;
  margin-left: -180rpx;
  margin-top: -80rpx;
  border: 3rpx dashed rgba(155, 126, 216, 0.18);
  border-radius: 50%;
}

.orbit__planet {
  position: absolute;
  top: 50%;
  width: 86rpx;
  height: 86rpx;
  margin-top: -43rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  box-shadow: 0 12rpx 28rpx rgba(155, 126, 216, 0.12);
}

.orbit__planet--left {
  left: 150rpx;
  animation: floatLeft 2.6s ease-in-out infinite;
}

.orbit__planet--right {
  right: 150rpx;
  animation: floatRight 2.8s ease-in-out infinite;
}

@keyframes floatLeft {
  0%,
  100% {
    transform: translateY(-6rpx);
  }
  50% {
    transform: translateY(8rpx);
  }
}

@keyframes floatRight {
  0%,
  100% {
    transform: translateY(8rpx);
  }
  50% {
    transform: translateY(-8rpx);
  }
}
</style>
