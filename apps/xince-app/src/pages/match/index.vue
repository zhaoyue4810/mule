<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import type { MatchHistoryResponse } from "@/shared/models/match";
import type { PublishedTestSummary } from "@/shared/models/tests";
import { ensureAppSession } from "@/shared/services/auth";
import { createMatchInvite, fetchMatchHistory } from "@/shared/services/match";
import { fetchPublishedTests } from "@/shared/services/tests";

const loading = ref(false);
const creatingTestCode = ref("");
const error = ref("");
const history = ref<MatchHistoryResponse>({ items: [], duo_badges: [] });
const tests = ref<PublishedTestSummary[]>([]);

const matchEnabledTests = computed(() =>
  tests.value.filter((item) => item.is_match_enabled),
);

function formatTime(value?: string | null) {
  if (!value) {
    return "刚刚";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getMonth() + 1}/${date.getDate()} ${`${date.getHours()}`.padStart(2, "0")}:${`${date.getMinutes()}`.padStart(2, "0")}`;
}

function openSession(sessionId: number, status: string) {
  if (status === "COMPLETED") {
    uni.navigateTo({ url: `/pages/match/report?sessionId=${sessionId}` });
    return;
  }
  uni.navigateTo({ url: `/pages/match/waiting?sessionId=${sessionId}` });
}

async function createInvite(testCode: string) {
  if (creatingTestCode.value) {
    return;
  }
  creatingTestCode.value = testCode;
  try {
    const payload = await createMatchInvite(testCode);
    uni.navigateTo({
      url: `/pages/match/waiting?sessionId=${payload.session_id}&code=${payload.invite_code}`,
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "创建邀请失败",
      icon: "none",
    });
  } finally {
    creatingTestCode.value = "";
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    const [historyPayload, testsPayload] = await Promise.all([
      fetchMatchHistory(),
      fetchPublishedTests(),
    ]);
    history.value = historyPayload;
    tests.value = testsPayload;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "匹配中心加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
onShow(load);
</script>

<template>
  <view class="page">
    <view class="hero">
      <view class="hero__avatars">
        <view class="hero__avatar">🪐</view>
        <view class="hero__pulse">❤</view>
        <view class="hero__avatar hero__avatar--alt">🌙</view>
      </view>
      <text class="hero__eyebrow">Soul Match Hub</text>
      <text class="hero__title">把同一套测试，变成两个人的默契实验。</text>
      <text class="hero__body">
        发起邀请后，好友完成同一测试即可生成匹配报告，查看你们的共振与互补维度。
      </text>
    </view>

    <view v-if="loading" class="panel">
      <text class="panel__text">正在同步匹配中心...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__text">{{ error }}</text>
      <button class="panel__button" @tap="load">重新加载</button>
    </view>

    <template v-else>
      <view class="section-head">
        <text class="section-head__title">发起灵魂匹配</text>
        <text class="section-head__meta">{{ matchEnabledTests.length }} 套支持</text>
      </view>
      <view class="test-list">
        <view
          v-for="item in matchEnabledTests"
          :key="item.test_code"
          class="test-card"
        >
          <view>
            <text class="test-card__title">{{ item.name }}</text>
            <text class="test-card__meta">{{ item.question_count }} 题 · {{ item.duration_hint || "待补时长" }}</text>
          </view>
          <button
            class="test-card__button"
            :loading="creatingTestCode === item.test_code"
            @tap="createInvite(item.test_code)"
          >
            邀请好友
          </button>
        </view>
      </view>

      <view class="section-head">
        <text class="section-head__title">双人勋章</text>
        <text class="section-head__meta">{{ history.duo_badges.length }} 枚已点亮</text>
      </view>
      <view v-if="history.duo_badges.length" class="badge-grid">
        <view
          v-for="badge in history.duo_badges"
          :key="badge.badge_key"
          class="badge-card"
        >
          <text class="badge-card__emoji">{{ badge.emoji }}</text>
          <text class="badge-card__name">{{ badge.name }}</text>
          <text class="badge-card__time">{{ formatTime(badge.unlocked_at) }}</text>
        </view>
      </view>
      <view v-else class="panel">
        <text class="panel__text">完成第一次双人匹配后，这里会点亮属于你们的双人勋章。</text>
      </view>

      <view class="section-head">
        <text class="section-head__title">匹配历史</text>
        <text class="section-head__meta">{{ history.items.length }} 条记录</text>
      </view>
      <view v-if="history.items.length" class="history-list">
        <view
          v-for="item in history.items"
          :key="item.session_id"
          class="history-card"
          @tap="openSession(item.session_id, item.status)"
        >
          <view class="history-card__top">
            <text class="history-card__title">{{ item.test_name }}</text>
            <text class="history-card__score">
              {{ item.compatibility_score != null ? `${item.compatibility_score}分` : "等待中" }}
            </text>
          </view>
          <text class="history-card__meta">
            {{ item.partner?.nickname || "等待加入" }} · {{ item.tier || item.status }}
          </text>
          <text class="history-card__time">{{ formatTime(item.completed_at || item.created_at) }}</text>
        </view>
      </view>
      <view v-else class="panel">
        <text class="panel__text">还没有匹配记录。选一套支持匹配的测试，邀请好友一起完成吧。</text>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx 24rpx 40rpx;
}

.hero {
  padding: 34rpx 30rpx;
  border-radius: 30rpx;
  background:
    radial-gradient(circle at top, rgba(255, 238, 225, 0.95), rgba(255, 220, 197, 0.92)),
    linear-gradient(145deg, rgba(255, 252, 246, 0.96), rgba(255, 241, 226, 0.9));
  box-shadow: $xc-shadow;
}

.hero__avatars {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
}

.hero__avatar {
  width: 94rpx;
  height: 94rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  font-size: 42rpx;
}

.hero__avatar--alt {
  background: rgba(255, 248, 243, 0.9);
}

.hero__pulse {
  font-size: 34rpx;
  color: #d96f3d;
  animation: beat 1.5s ease-in-out infinite;
}

.hero__eyebrow,
.hero__body,
.section-head__meta,
.panel__text,
.test-card__meta,
.badge-card__time,
.history-card__meta,
.history-card__time {
  color: $xc-muted;
}

.hero__eyebrow {
  display: block;
  margin-top: 18rpx;
  font-size: 22rpx;
  letter-spacing: 3rpx;
  text-transform: uppercase;
  text-align: center;
}

.hero__title {
  display: block;
  margin-top: 16rpx;
  font-size: 40rpx;
  line-height: 1.35;
  font-weight: 700;
  text-align: center;
}

.hero__body {
  display: block;
  margin-top: 14rpx;
  font-size: 25rpx;
  line-height: 1.7;
  text-align: center;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 30rpx 6rpx 16rpx;
}

.section-head__title {
  font-size: 30rpx;
  font-weight: 700;
}

.section-head__meta {
  font-size: 22rpx;
}

.panel,
.test-card,
.badge-card,
.history-card {
  border-radius: 24rpx;
  background: rgba(255, 253, 248, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
}

.panel {
  padding: 28rpx;
}

.panel--error {
  background: rgba(255, 240, 235, 0.96);
}

.panel__button {
  margin-top: 18rpx;
  border-radius: 999rpx;
  background: #d96f3d;
  color: #fff;
}

.test-list,
.history-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.test-card,
.history-card {
  padding: 24rpx;
  box-shadow: $xc-shadow;
}

.test-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20rpx;
}

.test-card__title,
.history-card__title {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
}

.test-card__meta {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
}

.test-card__button {
  min-width: 180rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #e38b59, #d96f3d);
  color: #fff9f4;
  font-size: 24rpx;
}

.badge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.badge-card {
  padding: 22rpx;
  text-align: center;
}

.badge-card__emoji {
  display: block;
  font-size: 42rpx;
}

.badge-card__name {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  font-weight: 600;
}

.badge-card__time {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
}

.history-card__top {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}

.history-card__score {
  font-size: 28rpx;
  font-weight: 700;
  color: #d96f3d;
}

.history-card__meta,
.history-card__time {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
}

@keyframes beat {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.18);
  }
}
</style>
