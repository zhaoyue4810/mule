<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { onLoad, onShareAppMessage, onShareTimeline } from "@dcloudio/uni-app";

import type { MatchInviteDetail } from "@/shared/models/match";
import { ensureAppSession } from "@/shared/services/auth";
import { fetchMatchInviteDetail } from "@/shared/services/match";
import { SoundManager } from "@/shared/utils/sound-manager";

const sessionId = ref(0);
const code = ref("");
const loading = ref(false);
const invite = ref<MatchInviteDetail | null>(null);
const error = ref("");
const successBurst = ref(false);
const successPlayed = ref(false);
const remainSeconds = ref(24 * 3600);
let pollTimer: ReturnType<typeof setInterval> | null = null;
let countdownTimer: ReturnType<typeof setInterval> | null = null;

const countdownText = computed(() => {
  const safe = Math.max(0, remainSeconds.value);
  const hour = `${Math.floor(safe / 3600)}`.padStart(2, "0");
  const minute = `${Math.floor((safe % 3600) / 60)}`.padStart(2, "0");
  const second = `${safe % 60}`.padStart(2, "0");
  return `${hour}:${minute}:${second}`;
});

const phasePercent = computed(() => {
  if (!invite.value) {
    return 18;
  }
  if (invite.value.status === "COMPLETED") {
    return 100;
  }
  if (invite.value.partner_joined) {
    return 76;
  }
  return 34;
});

const phaseBadge = computed(() => {
  if (!invite.value) {
    return "同步中";
  }
  if (invite.value.status === "COMPLETED") {
    return "结果已生成";
  }
  if (invite.value.partner_joined) {
    return "对方已加入";
  }
  return "等待好友加入";
});

const phaseTitle = computed(() => {
  if (!invite.value) {
    return "正在建立双人连接";
  }
  if (invite.value.status === "COMPLETED") {
    return "匹配完成，准备展开报告";
  }
  if (invite.value.partner_joined) {
    return "双方结果已汇合，报告正在显影";
  }
  return "这场关系实验已经发出邀请";
});

const phaseBody = computed(() => {
  if (!invite.value) {
    return "保持当前页面即可，我们会持续同步这场匹配的进度。";
  }
  if (invite.value.status === "COMPLETED") {
    return "系统已经完成匹配计算，页面会自动跳到你们的双人报告。";
  }
  if (invite.value.partner_joined) {
    return "对方已经进入流程，现在只需要等系统完成最后的匹配计算。";
  }
  return "还没有人加入这次邀请。你可以继续复制邀请码或打开邀请页去转发。";
});

function calcRemainSeconds() {
  if (!invite.value?.created_at) {
    remainSeconds.value = 24 * 3600;
    return;
  }
  const created = new Date(invite.value.created_at).getTime();
  if (Number.isNaN(created)) {
    remainSeconds.value = 24 * 3600;
    return;
  }
  const passed = Math.floor((Date.now() - created) / 1000);
  remainSeconds.value = Math.max(0, 24 * 3600 - passed);
}

function startCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
  }
  countdownTimer = setInterval(() => {
    remainSeconds.value = Math.max(0, remainSeconds.value - 1);
  }, 1000);
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
}

async function loadInvite() {
  if (!code.value) {
    error.value = "缺少邀请码，无法继续同步";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    const payload = await fetchMatchInviteDetail(code.value);
    invite.value = payload;
    calcRemainSeconds();
    startCountdown();
    if (payload.status === "COMPLETED") {
      stopPolling();
      if (!successPlayed.value && SoundManager.isSoundEnabled()) {
        SoundManager.play("chime");
        successPlayed.value = true;
      }
      successBurst.value = true;
      setTimeout(() => {
        uni.redirectTo({
          url: `/pages/match/report?sessionId=${payload.session_id}`,
        });
      }, 720);
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

function copyLink() {
  const text = invite.value?.invite_link || invite.value?.invite_code || code.value;
  if (!text) {
    return;
  }
  uni.setClipboardData({ data: text });
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
  successPlayed.value = false;
});

onMounted(() => {
  void loadInvite();
  startPolling();
});

onBeforeUnmount(() => {
  stopPolling();
  stopCountdown();
});

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
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--pink" />
    <view class="page__mesh" />

    <view class="page__content">
      <view v-if="loading && !invite" class="surface-card panel">
        <text class="panel__eyebrow">MATCHING</text>
        <text class="panel__title">正在等待对方进入这场灵魂匹配</text>
        <text class="panel__text">连接建立后，我们会自动同步匹配进度并跳转结果页。</text>
      </view>

      <view v-else-if="error" class="surface-card panel panel--error">
        <text class="panel__eyebrow">UNAVAILABLE</text>
        <text class="panel__title">同步失败</text>
        <text class="panel__text">{{ error }}</text>
        <button class="panel__button" @tap="loadInvite">重新同步</button>
      </view>

      <view v-else class="stack">
        <view class="hero" :class="{ 'hero--success': successBurst }">
          <view class="hero__topline">
            <text class="hero__eyebrow">WAITING ROOM</text>
            <text class="hero__badge">{{ phaseBadge }}</text>
          </view>

          <view class="hero__stage">
            <view class="hero__ring hero__ring--outer" />
            <view class="hero__ring hero__ring--inner" />
            <view class="hero__center">
              <text class="hero__center-label">{{ invite?.partner_joined ? "报告显影中" : "等待加入" }}</text>
              <text class="hero__center-value">{{ phasePercent }}%</text>
            </view>
            <view class="hero__orbit">
              <view class="hero__planet hero__planet--a">🧠</view>
              <view class="hero__planet hero__planet--b">
                {{ invite?.partner?.avatar_value || (invite?.partner_joined ? "🌙" : "✨") }}
              </view>
            </view>
            <view class="hero__burst" />
          </view>

          <text class="hero__title">{{ phaseTitle }}</text>
          <text class="hero__body">{{ phaseBody }}</text>

          <view class="hero__progress">
            <view class="hero__progress-track">
              <view class="hero__progress-fill" :style="{ width: `${phasePercent}%` }" />
            </view>
            <view class="hero__steps">
              <text class="hero__step hero__step--done">邀请已发出</text>
              <text class="hero__step" :class="{ 'hero__step--done': invite?.partner_joined }">对方加入</text>
              <text class="hero__step" :class="{ 'hero__step--done': invite?.status === 'COMPLETED' }">生成报告</text>
            </view>
          </view>
        </view>

        <view class="surface-card info-card">
          <view class="section-head">
            <view>
              <text class="section-head__title">邀请码与同步信息</text>
              <text class="section-head__desc">保持此页打开即可自动同步。如果想催一下，也可以继续转发邀请页。</text>
            </view>
          </view>

          <view class="code-strip">
            <text class="code-strip__value">{{ invite?.invite_code || code }}</text>
            <text class="code-strip__meta">剩余有效期 {{ countdownText }}</text>
          </view>

          <view class="info-grid">
            <view class="info-chip">
              <text class="info-chip__label">会话 ID</text>
              <text class="info-chip__value">{{ sessionId }}</text>
            </view>
            <view class="info-chip">
              <text class="info-chip__label">测试名称</text>
              <text class="info-chip__value">{{ invite?.test_name || "灵魂匹配" }}</text>
            </view>
            <view class="info-chip">
              <text class="info-chip__label">当前状态</text>
              <text class="info-chip__value">{{ invite?.partner_joined ? "已加入" : "等待中" }}</text>
            </view>
          </view>

          <view class="button-row">
            <button class="panel__button panel__button--ghost" @tap="copyCode">复制邀请码</button>
            <button class="panel__button panel__button--ghost" @tap="copyLink">复制链接</button>
            <button class="panel__button" @tap="openInvite">查看邀请页</button>
          </view>
        </view>

        <view class="surface-card sync-card">
          <text class="section-head__title">小测正在替你盯着进度</text>
          <text class="section-head__desc">
            {{ invite?.partner_joined ? "已经检测到对方加入，现在系统每轮同步都会检查是否可以出结果。" : "我们会每 3 秒自动刷新一次状态，等对方进入后就会继续往下走。" }}
          </text>
          <view class="sync-badges">
            <text class="sync-badge">自动刷新 3s</text>
            <text class="sync-badge">{{ invite?.partner_joined ? "已进入生成阶段" : "等待好友响应" }}</text>
            <text class="sync-badge">{{ successBurst ? "即将跳转报告" : "保持当前页即可" }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28rpx 24rpx calc(46rpx + env(safe-area-inset-bottom, 0rpx));
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.94), rgba(247, 240, 255, 0.8) 48%, #fffaf7 100%);
}

.page__content {
  position: relative;
  z-index: 1;
}

.page__glow,
.page__mesh {
  position: absolute;
  pointer-events: none;
}

.page__glow {
  width: 420rpx;
  height: 420rpx;
  border-radius: 50%;
  filter: blur(32px);
  opacity: 0.42;
}

.page__glow--violet {
  top: -120rpx;
  left: -120rpx;
  background: rgba(155, 126, 216, 0.24);
}

.page__glow--pink {
  right: -120rpx;
  bottom: 120rpx;
  background: rgba(232, 114, 154, 0.16);
}

.page__mesh {
  inset: 0;
  background-image:
    linear-gradient(rgba(155, 126, 216, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(232, 114, 154, 0.03) 1px, transparent 1px);
  background-size: 44rpx 44rpx;
  opacity: 0.42;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.surface-card {
  border-radius: 34rpx;
  border: 1px solid rgba(155, 126, 216, 0.12);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 24rpx 60rpx rgba(155, 126, 216, 0.1);

  // #ifdef H5
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  // #endif
}

.panel {
  padding: 28rpx;
}

.panel--error {
  border-color: rgba(232, 114, 154, 0.18);
}

.panel__eyebrow,
.hero__eyebrow {
  font-size: 20rpx;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.panel__eyebrow {
  color: rgba(124, 93, 191, 0.52);
}

.panel__title {
  display: block;
  margin-top: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.panel__text {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__button {
  border-radius: 999rpx;
  background: linear-gradient(135deg, #7c5dbf, #e8729a);
  color: #fff;
  font-size: 24rpx;
  font-weight: 700;
}

.panel__button--ghost {
  background: rgba(124, 93, 191, 0.08);
  color: $xc-purple-d;
}

.hero {
  position: relative;
  overflow: hidden;
  padding: 30rpx 28rpx;
  border-radius: 40rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.3), transparent 36%),
    linear-gradient(145deg, #7459bf 0%, #9b7ed8 36%, #f093b7 100%);
  color: #fff;
  box-shadow: 0 28rpx 72rpx rgba(124, 93, 191, 0.24);
}

.hero--success .hero__orbit {
  animation-duration: 0.8s;
}

.hero--success .hero__burst {
  animation: burst 0.7s ease-out both;
}

.hero__topline {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.hero__eyebrow {
  color: rgba(255, 255, 255, 0.8);
}

.hero__badge {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.92);
}

.hero__stage {
  position: relative;
  margin-top: 26rpx;
  height: 320rpx;
}

.hero__ring,
.hero__orbit {
  position: absolute;
  left: 50%;
  top: 50%;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.hero__ring--outer {
  width: 300rpx;
  height: 300rpx;
  border: 2rpx dashed rgba(255, 255, 255, 0.28);
}

.hero__ring--inner {
  width: 200rpx;
  height: 200rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.16);
}

.hero__center {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 2;
  width: 170rpx;
  height: 170rpx;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.hero__center-label {
  font-size: 19rpx;
  color: rgba(255, 255, 255, 0.78);
}

.hero__center-value {
  margin-top: 6rpx;
  font-size: 40rpx;
  font-weight: 800;
}

.hero__orbit {
  width: 300rpx;
  height: 300rpx;
  animation: orbitSpin 6s linear infinite;
}

.hero__planet {
  position: absolute;
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
  color: #47335f;
  box-shadow: 0 8rpx 24rpx rgba(155, 126, 216, 0.22);
}

.hero__planet--a {
  top: -10rpx;
  left: 50%;
  margin-left: -41rpx;
}

.hero__planet--b {
  bottom: -10rpx;
  left: 50%;
  margin-left: -41rpx;
}

.hero__burst {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.4);
  opacity: 0;
}

.hero__title {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 12rpx;
  text-align: center;
  font-size: 44rpx;
  line-height: 1.2;
  font-family: $xc-font-serif;
  font-weight: 700;
}

.hero__body {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 12rpx;
  text-align: center;
  font-size: 24rpx;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.92);
}

.hero__progress {
  position: relative;
  z-index: 1;
  margin-top: 22rpx;
}

.hero__progress-track {
  height: 12rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.16);
}

.hero__progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.96), rgba(255, 226, 237, 0.96));
}

.hero__steps {
  margin-top: 12rpx;
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
}

.hero__step {
  font-size: 19rpx;
  color: rgba(255, 255, 255, 0.58);
}

.hero__step--done {
  color: rgba(255, 255, 255, 0.96);
}

.info-card,
.sync-card {
  padding: 26rpx;
}

.section-head__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.section-head__desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.code-strip {
  margin-top: 18rpx;
  padding: 20rpx;
  border-radius: 26rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.62), transparent 34%),
    linear-gradient(145deg, rgba(124, 93, 191, 0.12), rgba(232, 114, 154, 0.1)),
    rgba(255, 255, 255, 0.84);
  text-align: center;
}

.code-strip__value {
  display: block;
  font-size: 54rpx;
  font-weight: 800;
  line-height: 1;
  letter-spacing: 10rpx;
  color: $xc-purple-d;
}

.code-strip__meta {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.info-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.info-chip {
  padding: 16rpx 12rpx;
  border-radius: 22rpx;
  background: rgba(124, 93, 191, 0.05);
  text-align: center;
}

.info-chip__label {
  display: block;
  font-size: 18rpx;
  color: $xc-hint;
}

.info-chip__value {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  line-height: 1.4;
  color: $xc-ink;
  font-weight: 600;
}

.button-row {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
}

.sync-badges {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.sync-badge {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(124, 93, 191, 0.08);
  font-size: 20rpx;
  color: $xc-purple-d;
}

@keyframes orbitSpin {
  from {
    transform: translate(-50%, -50%) rotate(0deg);
  }

  to {
    transform: translate(-50%, -50%) rotate(360deg);
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
