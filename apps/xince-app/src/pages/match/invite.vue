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
    <view v-if="loading" class="panel">
      <text class="panel__text">正在核对这份匹配邀请...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__title">邀请加载失败</text>
      <text class="panel__text">{{ error }}</text>
      <button class="panel__button" @tap="loadInvite">重新加载</button>
    </view>

    <view v-else-if="invite" class="stack">
      <view class="invite-card">
        <text class="invite-card__title">{{ invite.test_name }}</text>
        <text class="invite-card__desc">{{ invite.initiator.nickname }} 邀请你参与双人灵魂匹配</text>
        <view class="invite-card__code-wrap">
          <text class="invite-card__code">{{ invite.invite_code }}</text>
          <button class="mini-btn" @tap="copyInviteCode">复制</button>
        </view>
        <text class="invite-card__countdown">24 小时内有效 · {{ countdownText }}</text>
      </view>

      <view class="panel">
        <text class="panel__title">分享方式</text>
        <view class="share-actions">
          <!-- #ifdef MP-WEIXIN -->
          <button class="share-btn" open-type="share">微信好友</button>
          <!-- #endif -->
          <button class="share-btn" @tap="copyInviteLink">复制链接</button>
          <button class="share-btn" @tap="openPoster">生成海报</button>
        </view>
      </view>

      <view class="panel" v-if="invite.partner_joined">
        <text class="panel__title">当前状态</text>
        <text class="panel__text">好友已加入，系统正在生成匹配报告，请稍候在等待页查看进度。</text>
      </view>

      <view class="panel" v-else-if="invite.requires_test_completion">
        <text class="panel__title">加入前先完成测试</text>
        <text class="panel__text">你还没有完成「{{ invite.test_name }}」，先做完同一套测试再回来加入。</text>
        <button class="panel__button" @tap="startTest">去完成测试</button>
      </view>

      <view class="panel" v-else-if="invite.can_join">
        <text class="panel__title">立即加入</text>
        <text class="panel__text">你的结果已就绪，加入后将自动进入匹配等待页。</text>
        <button class="panel__button" :loading="joining" @tap="joinInvite">加入匹配</button>
      </view>

      <view class="hint">
        <text>{{ invite.partner_joined ? "邀请已送达，对方正在作答中..." : "邀请已准备好，发送给朋友后等待对方加入。" }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx 24rpx 40rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.panel,
.invite-card {
  @include card-base;
  padding: 24rpx;
}

.panel--error {
  border-color: rgba(232, 114, 154, 0.26);
}

.panel__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
}

.panel__text {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__button {
  margin-top: 14rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #9b7ed8, #e8729a);
  color: #fff;
}

.invite-card {
  background:
    linear-gradient(140deg, rgba(155, 126, 216, 0.2), rgba(232, 114, 154, 0.16)),
    rgba(255, 255, 255, 0.9);
}

.invite-card__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.invite-card__desc {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  color: $xc-muted;
}

.invite-card__code-wrap {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  padding: 14rpx 16rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.88);
}

.invite-card__code {
  font-size: 54rpx;
  font-weight: 700;
  letter-spacing: 10rpx;
  color: $xc-purple;
}

.invite-card__countdown {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.mini-btn {
  margin: 0;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.14);
  color: $xc-purple;
  font-size: 22rpx;
  padding: 0 22rpx;
}

.share-actions {
  margin-top: 12rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
}

.share-btn {
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.88);
  color: $xc-ink;
  font-size: 22rpx;
  border: 1px solid rgba(155, 126, 216, 0.14);
}

.hint {
  padding: 18rpx 20rpx;
  border-radius: 16rpx;
  background: rgba(237, 229, 249, 0.5);
  font-size: 22rpx;
  color: $xc-purple;
}
</style>
