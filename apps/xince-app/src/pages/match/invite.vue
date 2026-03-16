<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { onLoad, onShareAppMessage, onShareTimeline } from "@dcloudio/uni-app";

import type { MatchInviteDetail } from "@/shared/models/match";
import { ensureAppSession } from "@/shared/services/auth";
import { fetchMatchInviteDetail, joinMatchInvite } from "@/shared/services/match";

const code = ref("");
const loading = ref(false);
const joining = ref(false);
const invite = ref<MatchInviteDetail | null>(null);
const error = ref("");
const remainSeconds = ref(24 * 3600);
let countdownTimer: ReturnType<typeof setInterval> | null = null;

const inviteLink = computed(() => invite.value?.invite_link || "");

const countdownText = computed(() => {
  const safe = Math.max(0, remainSeconds.value);
  const hour = `${Math.floor(safe / 3600)}`.padStart(2, "0");
  const minute = `${Math.floor((safe % 3600) / 60)}`.padStart(2, "0");
  const second = `${safe % 60}`.padStart(2, "0");
  return `${hour}:${minute}:${second}`;
});

const heroBadge = computed(() => {
  if (invite.value?.partner_joined) {
    return "对方已加入";
  }
  if (invite.value?.can_join) {
    return "你已准备就绪";
  }
  if (invite.value?.requires_test_completion) {
    return "先完成同套测试";
  }
  return "邀请 24 小时有效";
});

const heroTitle = computed(() => {
  if (!invite.value) {
    return "灵魂匹配邀请";
  }
  return `邀请你一起完成「${invite.value.test_name}」`;
});

const heroBody = computed(() => {
  if (!invite.value) {
    return "把这份邀请发给重要的人，对方完成同一套测试后，就会自动生成双人匹配报告。";
  }
  return `${invite.value.initiator.nickname} 已经准备好进入这场关系实验。你们完成同一套测试后，会直接生成专属匹配报告与双人徽章。`;
});

const statusTitle = computed(() => {
  if (invite.value?.partner_joined) {
    return "当前已经进入匹配流程";
  }
  if (invite.value?.requires_test_completion) {
    return "加入前需要先完成测试";
  }
  if (invite.value?.can_join) {
    return "你的加入资格已确认";
  }
  return "邀请链接已经准备好了";
});

const statusBody = computed(() => {
  if (invite.value?.partner_joined) {
    return "系统检测到对方已经加入，接下来会自动跳入等待页并持续同步匹配进度。";
  }
  if (invite.value?.requires_test_completion) {
    return `你还没有完成「${invite.value?.test_name || "当前测试"}」，先做完同一套题，再回来加入会更顺畅。`;
  }
  if (invite.value?.can_join) {
    return "你的结果已经就绪，点击加入后会立即进入等待页，系统开始生成双人匹配结果。";
  }
  return "把邀请码或链接发给想一起测试的人，对方进入后会自动接上这条关系链路。";
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
    error.value = "缺少邀请码";
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    invite.value = await fetchMatchInviteDetail(code.value);
    calcRemainSeconds();
    startCountdown();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载邀请失败";
  } finally {
    loading.value = false;
  }
}

function copyInviteCode() {
  if (!invite.value?.invite_code) {
    return;
  }
  uni.setClipboardData({ data: invite.value.invite_code });
}

function copyInviteLink() {
  const text = inviteLink.value || invite.value?.invite_code || code.value;
  if (!text) {
    return;
  }
  uni.setClipboardData({ data: text });
}

function openPoster() {
  uni.showToast({
    title: "挑战海报请在报告页生成",
    icon: "none",
  });
}

function startTest() {
  if (!invite.value) {
    return;
  }
  uni.navigateTo({
    url: `/pages/test/detail?testCode=${invite.value.test_code}`,
  });
}

async function joinInvite() {
  if (!code.value || joining.value) {
    return;
  }
  joining.value = true;
  try {
    const payload = await joinMatchInvite(code.value);
    if (payload.result_ready) {
      uni.redirectTo({
        url: `/pages/match/report?sessionId=${payload.session_id}`,
      });
      return;
    }
    uni.redirectTo({
      url: `/pages/match/waiting?sessionId=${payload.session_id}&code=${code.value}`,
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "加入失败",
      icon: "none",
    });
  } finally {
    joining.value = false;
  }
}

onLoad((query) => {
  code.value = typeof query?.code === "string" ? query.code : "";
});

onMounted(loadInvite);
onBeforeUnmount(stopCountdown);

onShareAppMessage(() => ({
  title: invite.value
    ? `${invite.value.initiator.nickname} 邀请你一起做「${invite.value.test_name}」匹配`
    : "来心测看看我们的灵魂匹配度",
  path: `/pages/match/invite?code=${code.value}`,
}));

onShareTimeline(() => ({
  title: invite.value
    ? `${invite.value.test_name} 灵魂匹配邀请`
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
      <view v-if="loading" class="surface-card panel">
        <text class="panel__eyebrow">INVITATION</text>
        <text class="panel__title">正在核对这份匹配邀请</text>
        <text class="panel__text">我们会同步测试信息、邀请码和你的加入资格。</text>
      </view>

      <view v-else-if="error" class="surface-card panel panel--error">
        <text class="panel__eyebrow">UNAVAILABLE</text>
        <text class="panel__title">邀请加载失败</text>
        <text class="panel__text">{{ error }}</text>
        <button class="panel__button" @tap="loadInvite">重新加载</button>
      </view>

      <view v-else-if="invite" class="stack">
        <view class="hero">
          <view class="hero__orb hero__orb--violet" />
          <view class="hero__orb hero__orb--pink" />
          <view class="hero__topline">
            <text class="hero__eyebrow">SOUL INVITATION</text>
            <text class="hero__badge">{{ heroBadge }}</text>
          </view>

          <view class="hero__avatars">
            <view class="hero__avatar-wrap">
              <view class="hero__avatar hero__avatar--primary">
                {{ invite.initiator.avatar_value }}
              </view>
              <text class="hero__avatar-name">{{ invite.initiator.nickname }}</text>
            </view>
            <view class="hero__connector">❤</view>
            <view class="hero__avatar-wrap">
              <view class="hero__avatar hero__avatar--secondary">
                {{ invite.partner?.avatar_value || "✨" }}
              </view>
              <text class="hero__avatar-name">{{ invite.partner?.nickname || "等待你加入" }}</text>
            </view>
          </view>

          <text class="hero__title">{{ heroTitle }}</text>
          <text class="hero__body">{{ heroBody }}</text>

          <view class="code-card">
            <text class="code-card__label">邀请码</text>
            <view class="code-card__main">
              <text class="code-card__value">{{ invite.invite_code }}</text>
              <button class="code-card__button" @tap="copyInviteCode">复制</button>
            </view>
            <text class="code-card__meta">24 小时内有效 · 倒计时 {{ countdownText }}</text>
          </view>
        </view>

        <view class="surface-card share-panel">
          <view class="section-head">
            <view>
              <text class="section-head__title">发送这份邀请</text>
              <text class="section-head__desc">把邀请码或链接发出去，对方完成同套测试后就会生成专属双人报告。</text>
            </view>
          </view>

          <view class="share-grid">
            <!-- #ifdef MP-WEIXIN -->
            <button class="share-card" open-type="share">
              <text class="share-card__emoji">💬</text>
              <text class="share-card__title">微信好友</text>
              <text class="share-card__body">直接分享给聊天对象</text>
            </button>
            <!-- #endif -->
            <button class="share-card" @tap="copyInviteLink">
              <text class="share-card__emoji">🔗</text>
              <text class="share-card__title">复制链接</text>
              <text class="share-card__body">适合发到任意社交平台</text>
            </button>
            <button class="share-card" @tap="openPoster">
              <text class="share-card__emoji">🖼</text>
              <text class="share-card__title">挑战海报</text>
              <text class="share-card__body">在报告页生成更完整的分享图</text>
            </button>
          </view>
        </view>

        <view class="surface-card status-card">
          <view class="section-head">
            <view>
              <text class="section-head__title">{{ statusTitle }}</text>
              <text class="section-head__desc">{{ statusBody }}</text>
            </view>
          </view>

          <view class="status-steps">
            <view class="status-step status-step--done">
              <text class="status-step__emoji">💌</text>
              <text class="status-step__label">邀请创建</text>
            </view>
            <view class="status-step" :class="{ 'status-step--done': invite.partner_joined || invite.can_join }">
              <text class="status-step__emoji">{{ invite.can_join ? "✅" : "🧩" }}</text>
              <text class="status-step__label">
                {{ invite.requires_test_completion ? "完成测试" : "确认资格" }}
              </text>
            </view>
            <view class="status-step" :class="{ 'status-step--done': invite.partner_joined }">
              <text class="status-step__emoji">{{ invite.partner_joined ? "🌙" : "⌛" }}</text>
              <text class="status-step__label">进入等待</text>
            </view>
          </view>

          <view v-if="invite.requires_test_completion" class="cta-card">
            <text class="cta-card__title">先完成这套测试，再回来加入</text>
            <text class="cta-card__body">你的个人结果准备好之后，系统才能为你们计算专属匹配度。</text>
            <button class="panel__button" @tap="startTest">去完成测试</button>
          </view>

          <view v-else-if="invite.can_join" class="cta-card">
            <text class="cta-card__title">现在就可以加入匹配</text>
            <text class="cta-card__body">点击后会自动进入等待页，系统开始拉起这场双人关系实验。</text>
            <button class="panel__button" :loading="joining" @tap="joinInvite">加入匹配</button>
          </view>

          <view v-else class="cta-card cta-card--soft">
            <text class="cta-card__title">邀请已准备就绪</text>
            <text class="cta-card__body">如果这是你自己打开的邀请页，现在可以继续把它转发给那位想一起测试的人。</text>
            <button class="panel__button panel__button--ghost" @tap="copyInviteLink">复制链接继续发送</button>
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
    radial-gradient(circle at top, rgba(255, 255, 255, 0.94), rgba(255, 246, 240, 0.8) 48%, #fffaf7 100%);
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
  right: -120rpx;
  background: rgba(155, 126, 216, 0.26);
}

.page__glow--pink {
  bottom: 120rpx;
  left: -120rpx;
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
  margin-top: 18rpx;
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
  padding: 30rpx 28rpx 28rpx;
  border-radius: 40rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.3), transparent 36%),
    linear-gradient(145deg, #7459bf 0%, #9b7ed8 36%, #f093b7 100%);
  color: #fff;
  box-shadow: 0 28rpx 72rpx rgba(124, 93, 191, 0.24);
}

.hero__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(14px);
  opacity: 0.26;
}

.hero__orb--violet {
  top: -28rpx;
  left: -18rpx;
  width: 170rpx;
  height: 170rpx;
  background: rgba(255, 255, 255, 0.42);
}

.hero__orb--pink {
  right: -34rpx;
  bottom: 64rpx;
  width: 170rpx;
  height: 170rpx;
  background: rgba(255, 220, 232, 0.42);
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

.hero__avatars {
  position: relative;
  z-index: 1;
  margin-top: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.hero__avatar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.hero__avatar {
  width: 116rpx;
  height: 116rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 50rpx;
  color: #47335f;
  border: 4rpx solid rgba(255, 255, 255, 0.72);
}

.hero__avatar--primary {
  background: rgba(255, 255, 255, 0.9);
}

.hero__avatar--secondary {
  background: rgba(255, 243, 247, 0.86);
}

.hero__avatar-name {
  font-size: 21rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero__connector {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.14);
  font-size: 26rpx;
}

.hero__title {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 22rpx;
  text-align: center;
  font-size: 48rpx;
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

.code-card {
  position: relative;
  z-index: 1;
  margin-top: 24rpx;
  padding: 20rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.14);
}

.code-card__label,
.code-card__meta {
  display: block;
}

.code-card__label {
  font-size: 21rpx;
  color: rgba(255, 255, 255, 0.8);
}

.code-card__main {
  margin-top: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.code-card__value {
  font-size: 56rpx;
  line-height: 1;
  letter-spacing: 10rpx;
  font-weight: 800;
}

.code-card__button {
  min-width: 122rpx;
  height: 68rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  border: none;
  background: rgba(255, 255, 255, 0.92);
  color: $xc-purple-d;
  font-size: 22rpx;
  font-weight: 700;
}

.code-card__meta {
  margin-top: 12rpx;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.76);
}

.share-panel,
.status-card {
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

.share-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.share-card {
  min-height: 176rpx;
  padding: 20rpx 18rpx;
  border-radius: 26rpx;
  border: 1px solid rgba(155, 126, 216, 0.1);
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.58), transparent 34%),
    rgba(255, 255, 255, 0.84);
  text-align: left;
}

.share-card__emoji {
  display: block;
  font-size: 34rpx;
}

.share-card__title {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  font-weight: 700;
  color: $xc-ink;
}

.share-card__body {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.status-steps {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.status-step {
  padding: 18rpx 14rpx;
  border-radius: 22rpx;
  background: rgba(124, 93, 191, 0.05);
  text-align: center;
}

.status-step--done {
  background: linear-gradient(145deg, rgba(124, 93, 191, 0.12), rgba(232, 114, 154, 0.1));
}

.status-step__emoji {
  display: block;
  font-size: 30rpx;
}

.status-step__label {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.5;
  color: $xc-ink;
  font-weight: 600;
}

.cta-card {
  margin-top: 18rpx;
  padding: 20rpx;
  border-radius: 26rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.62), transparent 34%),
    linear-gradient(145deg, rgba(124, 93, 191, 0.12), rgba(232, 114, 154, 0.1)),
    rgba(255, 255, 255, 0.84);
}

.cta-card--soft {
  background: rgba(255, 255, 255, 0.82);
}

.cta-card__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.cta-card__body {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}
</style>
