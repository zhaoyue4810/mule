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
const successBurst = ref(false);
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
      successBurst.value = true;
      setTimeout(() => {
        uni.redirectTo({
          url: `/pages/match/report?sessionId=${payload.session_id}`,
        });
      }, 680);
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
      <view class="orbit-stage" :class="{ 'orbit-stage--success': successBurst }">
        <view class="orbit-stage__ring" />
        <view class="orbit-stage__loader">
          <text>等待中...</text>
        </view>
        <view class="orbit-stage__track">
          <view class="orbit-stage__planet orbit-stage__planet--a">🧠</view>
          <view class="orbit-stage__planet orbit-stage__planet--b">{{ invite?.partner_joined ? "🌙" : "✨" }}</view>
        </view>
        <view class="orbit-stage__burst" />
      </view>

      <view class="panel panel--code">
        <text class="panel__title">邀请码</text>
        <text class="code">{{ invite?.invite_code || code }}</text>
        <view class="button-row">
          <button class="panel__button" @tap="copyCode">复制邀请码</button>
          <button class="panel__button panel__button--ghost" @tap="openInvite">查看邀请页</button>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">当前状态</text>
        <text class="panel__text">
          {{ invite?.partner_joined ? "已检测到对方加入，正在生成匹配结果。" : "还没有人加入，我们会每 3 秒自动同步一次。" }}
        </text>
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
  gap: 16rpx;
}

.panel {
  @include card-base;
  padding: 24rpx;
}

.panel--error {
  border-color: rgba(232, 114, 154, 0.24);
}

.panel__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
}

.panel__text,
.footnote {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__button {
  flex: 1;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #9b7ed8, #e8729a);
  color: #fff;
  font-size: 24rpx;
}

.panel__button--ghost {
  background: rgba(155, 126, 216, 0.12);
  color: $xc-purple;
}

.code {
  display: block;
  margin-top: 14rpx;
  text-align: center;
  font-size: 52rpx;
  letter-spacing: 10rpx;
  font-weight: 700;
  color: $xc-purple;
}

.button-row {
  margin-top: 14rpx;
  display: flex;
  gap: 12rpx;
}

.orbit-stage {
  position: relative;
  height: 320rpx;
  border-radius: 26rpx;
  overflow: hidden;
  background:
    radial-gradient(circle at top, rgba(201, 181, 240, 0.28), transparent 58%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(237, 229, 249, 0.54));
  border: 2rpx solid rgba(155, 126, 216, 0.12);
}

.orbit-stage__ring {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 360rpx;
  height: 360rpx;
  margin-left: -180rpx;
  margin-top: -180rpx;
  border-radius: 50%;
  border: 2rpx dashed rgba(155, 126, 216, 0.24);
}

.orbit-stage__loader {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 26rpx;
  color: $xc-purple;
  animation: pulse 1.5s ease-in-out infinite;
}

.orbit-stage__track {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 360rpx;
  height: 360rpx;
  margin-left: -180rpx;
  margin-top: -180rpx;
  animation: orbitSpin 6s linear infinite;
}

.orbit-stage__planet {
  position: absolute;
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  box-shadow: 0 8rpx 24rpx rgba(155, 126, 216, 0.2);
}

.orbit-stage__planet--a {
  top: -12rpx;
  left: 50%;
  margin-left: -41rpx;
}

.orbit-stage__planet--b {
  bottom: -12rpx;
  left: 50%;
  margin-left: -41rpx;
}

.orbit-stage__burst {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(232, 114, 154, 0.4);
  transform: translate(-50%, -50%);
  opacity: 0;
}

.orbit-stage--success .orbit-stage__track {
  animation-duration: 0.7s;
}

.orbit-stage--success .orbit-stage__burst {
  animation: burst 0.65s ease-out both;
}

@keyframes orbitSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes burst {
  from {
    width: 0;
    height: 0;
    opacity: 0.8;
  }
  to {
    width: 420rpx;
    height: 420rpx;
    opacity: 0;
  }
}
</style>
