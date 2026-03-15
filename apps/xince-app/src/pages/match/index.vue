<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import TabBuddy from "@/components/mascot/TabBuddy.vue";
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

const rankedCP = computed(() =>
  history.value.items
    .filter((item) => item.compatibility_score != null && item.partner)
    .sort((a, b) => (b.compatibility_score || 0) - (a.compatibility_score || 0))
    .slice(0, 3),
);

const featuredModes = computed(() => {
  const first = matchEnabledTests.value[0] || null;
  const second = matchEnabledTests.value[1] || first;
  return [
    {
      key: "exclusive",
      title: "专属匹配测试",
      desc: first
        ? `推荐「${first.name}」，做完即可生成专属双人报告`
        : "选择任意支持匹配的测试，生成专属报告",
      testCode: first?.test_code || "",
      button: "开始匹配",
      className: "mode-card--purple",
    },
    {
      key: "share",
      title: "分享匹配",
      desc: second
        ? `邀请好友挑战「${second.name}」，解锁双人徽章`
        : "发出邀请链接，好友加入后自动匹配",
      testCode: second?.test_code || "",
      button: "发起邀请",
      className: "mode-card--pink",
    },
  ];
});

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

function formatStatus(status: string) {
  if (status === "COMPLETED") {
    return "完成";
  }
  if (status === "WAITING_PARTNER") {
    return "等待中";
  }
  if (status === "RUNNING") {
    return "进行中";
  }
  return status;
}

function statusClass(status: string) {
  if (status === "WAITING_PARTNER") {
    return "status--waiting";
  }
  if (status === "RUNNING") {
    return "status--running";
  }
  return "status--done";
}

function tierBadge(tier?: string | null) {
  if (!tier) {
    return "默契搭档";
  }
  return tier;
}

function rankStyle(index: number) {
  if (index === 0) {
    return "rank--gold";
  }
  if (index === 1) {
    return "rank--silver";
  }
  return "rank--bronze";
}

function openSession(sessionId: number, status: string) {
  if (status === "COMPLETED") {
    uni.navigateTo({ url: `/pages/match/report?sessionId=${sessionId}` });
    return;
  }
  uni.navigateTo({ url: `/pages/match/waiting?sessionId=${sessionId}` });
}

async function createInvite(testCode: string) {
  if (!testCode || creatingTestCode.value) {
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
        <view class="hero__avatar">{{ history.items[0]?.partner?.avatar_value || "🧠" }}</view>
        <view class="hero__heart">❤</view>
        <view class="hero__avatar hero__avatar--alt">💫</view>
      </view>
      <text class="hero__title">灵魂匹配中心</text>
      <text class="hero__body">把同一套测试变成双人默契实验，看看你们是天作之合还是互补搭档。</text>
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
        <text class="section-head__title">匹配模式</text>
      </view>
      <view class="mode-grid">
        <view
          v-for="mode in featuredModes"
          :key="mode.key"
          class="mode-card"
          :class="mode.className"
        >
          <text class="mode-card__title">{{ mode.title }}</text>
          <text class="mode-card__desc">{{ mode.desc }}</text>
          <button
            class="mode-card__button"
            :loading="creatingTestCode === mode.testCode"
            @tap="createInvite(mode.testCode)"
          >
            {{ mode.button }}
          </button>
        </view>
      </view>

      <view v-if="rankedCP.length" class="section-head">
        <text class="section-head__title">最佳 CP 排行榜</text>
      </view>
      <view v-if="rankedCP.length" class="cp-list">
        <view v-for="(item, index) in rankedCP" :key="`cp-${item.session_id}`" class="cp-item">
          <text class="cp-item__rank" :class="rankStyle(index)">{{ index + 1 }}</text>
          <view class="cp-item__avatars">
            <text class="cp-item__avatar">🙂</text>
            <text class="cp-item__avatar">{{ item.partner?.avatar_value || "✨" }}</text>
          </view>
          <view class="cp-item__body">
            <text class="cp-item__name">{{ item.partner?.nickname || "匿名搭档" }}</text>
            <text class="cp-item__meta">{{ item.compatibility_score }} 分 · {{ tierBadge(item.tier) }}</text>
          </view>
        </view>
      </view>

      <view class="section-head">
        <text class="section-head__title">我的匹配记录</text>
        <text class="section-head__meta">{{ history.items.length }} 条</text>
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
            {{ item.partner?.nickname || "等待加入" }} · {{ tierBadge(item.tier) }}
          </text>
          <view class="history-card__foot">
            <text class="history-card__time">{{ formatTime(item.completed_at || item.created_at) }}</text>
            <text class="status" :class="statusClass(item.status)">{{ formatStatus(item.status) }}</text>
          </view>
        </view>
      </view>
      <view v-else class="panel">
        <text class="panel__text">还没有匹配记录。先发起一次邀请，和朋友一起完成测试吧。</text>
      </view>

      <view class="section-head">
        <text class="section-head__title">双人徽章</text>
        <text class="section-head__meta">{{ history.duo_badges.length }} 枚</text>
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
        <text class="panel__text">完成首次双人报告后，这里会点亮专属徽章。</text>
      </view>

      <button
        class="invite-cta"
        :loading="creatingTestCode === (featuredModes[0]?.testCode || '')"
        @tap="createInvite(featuredModes[0]?.testCode || '')"
      >
        <text class="invite-cta__shine" />
        邀请朋友来匹配
      </button>
    </template>
    <TabBuddy />
  </view>
</template>

<style lang="scss" scoped>
/* ── Page ── */
.page {
  padding: 28rpx 24rpx calc(48rpx + env(safe-area-inset-bottom, 0rpx));
}

/* ── Hero ── */
.hero {
  padding: 34rpx 28rpx;
  border-radius: 30rpx;
  @include gradient-hero;
  color: #fff;
  box-shadow: $xc-sh-lg;
  animation: fadeInUp 0.5s $xc-ease both;
}

.hero__avatars {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.hero__avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.82);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
  color: $xc-ink;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.95);
  }
}

.hero__avatar--alt {
  background: rgba(255, 255, 255, 0.68);
}

.hero__heart {
  font-size: 36rpx;
  animation: heartbeat 2s ease-in-out infinite;
}

.hero__title {
  display: block;
  margin-top: 18rpx;
  text-align: center;
  font-size: 40rpx;
  font-weight: 700;
}

.hero__body {
  display: block;
  margin-top: 12rpx;
  text-align: center;
  font-size: 24rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.92);
}

/* ── Section heads ── */
.section-head {
  margin: 28rpx 6rpx 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-head__title {
  font-size: 30rpx;
  font-weight: 700;
}

.section-head__meta {
  font-size: 22rpx;
  color: $xc-muted;
}

/* ── Glass card base ── */
.panel,
.mode-card,
.history-card,
.badge-card,
.cp-item {
  background: rgba(255, 255, 255, 0.72);
  // #ifdef H5
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  // #endif
  // #ifdef MP-WEIXIN
  background: rgba(255, 255, 255, 0.92);
  // #endif
  border: 1px solid rgba(155, 126, 216, 0.12);
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(155, 126, 216, 0.08);
  transition: transform $xc-fast $xc-spring, box-shadow $xc-fast $xc-ease;
}

.panel {
  padding: 26rpx;
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.05s;
}

.panel--error {
  border-color: rgba(232, 114, 154, 0.25);
}

.panel__text {
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__button {
  margin-top: 14rpx;
  border-radius: 999rpx;
  @include btn-primary;
}

/* ── Mode grid ── */
.mode-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.1s;
}

.mode-card {
  padding: 20rpx;
  // #ifdef H5
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  // #endif

  &:active {
    transform: scale(0.97);
    box-shadow: 0 1px 4px rgba(155, 126, 216, 0.12);
  }
}

.mode-card--purple {
  background:
    linear-gradient(135deg, rgba(155, 126, 216, 0.28), rgba(201, 181, 240, 0.15)),
    rgba(255, 255, 255, 0.72);
  border-color: rgba(155, 126, 216, 0.18);
}

.mode-card--pink {
  background:
    linear-gradient(135deg, rgba(232, 114, 154, 0.24), rgba(244, 165, 191, 0.13)),
    rgba(255, 255, 255, 0.72);
  border-color: rgba(232, 114, 154, 0.18);
}

.mode-card__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
}

.mode-card__desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.mode-card__button {
  margin-top: 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.85);
  color: $xc-purple;
  font-size: 22rpx;
  border: 1px solid rgba(155, 126, 216, 0.2);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.96);
  }
}

/* ── CP Ranking ── */
.cp-list,
.history-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.cp-list {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.15s;
}

.cp-item {
  padding: 16rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;

  &:active {
    transform: scale(0.98);
  }
}

.cp-item__rank {
  width: 48rpx;
  height: 48rpx;
  font-size: 24rpx;
  font-weight: 800;
  text-align: center;
  line-height: 48rpx;
  border-radius: 50%;
}

.rank--gold {
  background: linear-gradient(135deg, #fdf4de, #f5e4a8);
  color: $xc-gold;
  box-shadow: 0 2px 8px rgba(212, 168, 83, 0.25);
}

.rank--silver {
  background: linear-gradient(135deg, #f0f0f0, #dcdcdc);
  color: #8a8a8a;
  box-shadow: 0 2px 8px rgba(192, 192, 192, 0.25);
}

.rank--bronze {
  background: linear-gradient(135deg, #f8e8d6, #e8c9a8);
  color: #cd7f32;
  box-shadow: 0 2px 8px rgba(205, 127, 50, 0.2);
}

.cp-item__avatars {
  display: flex;
}

.cp-item__avatar {
  width: 42rpx;
  height: 42rpx;
  border-radius: 50%;
  background: rgba(155, 126, 216, 0.16);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: -6rpx;
}

.cp-item__body {
  flex: 1;
}

.cp-item__name {
  display: block;
  font-size: 24rpx;
  font-weight: 600;
}

.cp-item__meta {
  display: block;
  margin-top: 4rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

/* ── History cards ── */
.history-list {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.2s;
}

.history-card {
  padding: 20rpx;

  &:active {
    transform: scale(0.98);
    box-shadow: 0 1px 4px rgba(155, 126, 216, 0.12);
  }
}

.history-card__top,
.history-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14rpx;
}

.history-card__title {
  font-size: 28rpx;
  font-weight: 600;
}

.history-card__score {
  color: $xc-purple;
  font-size: 26rpx;
  font-weight: 700;
}

.history-card__meta,
.history-card__time {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

/* ── Status badges ── */
.status {
  margin-top: 8rpx;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
}

.status--waiting {
  background: $xc-gold-p;
  color: $xc-gold;
  animation: statusPulse 2s ease-in-out infinite;
}

.status--running {
  background: rgba(155, 126, 216, 0.14);
  color: $xc-purple;
}

.status--done {
  background: $xc-mint-p;
  color: $xc-mint;
}

/* ── Duo badge grid ── */
.badge-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.25s;
}

.badge-card {
  padding: 16rpx 10rpx;
  text-align: center;
  background: linear-gradient(160deg, rgba(253, 230, 239, 0.4), rgba(255, 255, 255, 0.72));
  border-color: $xc-pink-l;
  box-shadow: 0 0 12px rgba(232, 114, 154, 0.15);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.95);
  }
}

.badge-card--locked {
  opacity: 0.45;
  border-color: $xc-line;
  box-shadow: none;
  background: rgba(255, 255, 255, 0.5);
  filter: grayscale(0.6);
}

.badge-card__emoji {
  display: block;
  font-size: 38rpx;
}

.badge-card__name {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  font-weight: 600;
}

.badge-card__time {
  display: block;
  margin-top: 6rpx;
  font-size: 19rpx;
  color: $xc-muted;
}

/* ── Full-width CTA ── */
.invite-cta {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin-top: 22rpx;
  border-radius: $xc-r-btn;
  overflow: hidden;
  color: #fff;
  font-weight: 700;
  @include btn-primary;
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.3s;

  &:active {
    transform: scale(0.97);
    box-shadow: 0 4px 14px rgba(155, 126, 216, 0.28);
  }
}

.invite-cta__shine {
  content: "";
  position: absolute;
  top: 0;
  left: -120%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: shimmer 3s infinite;
}

/* ── Keyframes ── */
@keyframes heartbeat {
  0%,
  100% {
    transform: scale(1);
  }
  15% {
    transform: scale(1.15);
  }
  30% {
    transform: scale(1);
  }
  45% {
    transform: scale(1.08);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(420%);
  }
}

@keyframes statusPulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
