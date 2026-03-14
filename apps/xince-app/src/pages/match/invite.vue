<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { onLoad, onShareAppMessage, onShareTimeline } from "@dcloudio/uni-app";

import type { MatchInviteDetail } from "@/shared/models/match";
import { ensureAppSession } from "@/shared/services/auth";
import { fetchMatchInviteDetail, joinMatchInvite } from "@/shared/services/match";

const code = ref("");
const loading = ref(false);
const joining = ref(false);
const invite = ref<MatchInviteDetail | null>(null);
const error = ref("");

const inviteLink = computed(() => {
  if (!invite.value?.invite_link) {
    return "";
  }
  return invite.value.invite_link;
});

async function loadInvite() {
  if (!code.value) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    invite.value = await fetchMatchInviteDetail(code.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "加载邀请失败";
  } finally {
    loading.value = false;
  }
}

function copyInvite() {
  const text = inviteLink.value || code.value;
  if (!text) {
    return;
  }
  uni.setClipboardData({ data: text });
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
      <view class="hero">
        <text class="hero__eyebrow">Invite Preview</text>
        <text class="hero__title">{{ invite.test_name }}</text>
        <text class="hero__body">
          {{ invite.initiator.nickname }} 邀请你一起完成这套测试，看看你们的灵魂契合度。
        </text>
      </view>

      <view class="panel">
        <text class="panel__title">邀请码</text>
        <text class="code">{{ invite.invite_code }}</text>
        <text class="panel__text">复制后可直接发送给好友，或回到微信原生分享。</text>
        <button class="panel__button panel__button--ghost" @tap="copyInvite">复制邀请</button>
        <!-- #ifdef MP-WEIXIN -->
        <button class="panel__button" open-type="share">分享到微信</button>
        <!-- #endif -->
      </view>

      <view class="panel" v-if="invite.partner_joined">
        <text class="panel__title">当前状态</text>
        <text class="panel__text">这份邀请已经有人加入，系统正在整理匹配结果。</text>
      </view>

      <view class="panel" v-else-if="invite.requires_test_completion">
        <text class="panel__title">加入前先完成测试</text>
        <text class="panel__text">
          你还没有完成「{{ invite.test_name }}」，先做完同一套测试，再回来加入这次匹配。
        </text>
        <button class="panel__button" @tap="startTest">去完成测试</button>
      </view>

      <view class="panel" v-else-if="invite.can_join">
        <text class="panel__title">立即加入</text>
        <text class="panel__text">你的同一测试结果已就绪，加入后会立刻生成双人匹配报告。</text>
        <button class="panel__button" :loading="joining" @tap="joinInvite">加入匹配</button>
      </view>
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
.panel__text {
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
.panel__text {
  display: block;
  margin-top: 14rpx;
  font-size: 25rpx;
  line-height: 1.7;
}

.code {
  display: block;
  margin-top: 18rpx;
  font-size: 54rpx;
  letter-spacing: 10rpx;
  font-weight: 700;
  color: #9B7ED8;
  text-align: center;
}

.panel__button {
  margin-top: 18rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #E8729A, #9B7ED8);
  color: #fff8f2;
}

.panel__button--ghost {
  background: rgba(155, 126, 216, 0.12);
  color: #9B7ED8;
}
</style>
