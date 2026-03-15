<script setup lang="ts">
import { computed, ref } from "vue";
import { onHide, onShow, onUnload } from "@dcloudio/uni-app";

import TimeCapsuleReveal from "@/components/feedback/TimeCapsuleReveal.vue";
import TabBuddy from "@/components/mascot/TabBuddy.vue";
import XiaoCe from "@/components/mascot/XiaoCe.vue";
import XcBubble from "@/components/mascot/XcBubble.vue";
import PersonaRadarCanvas from "@/components/profile/PersonaRadarCanvas.vue";
import type { TimeCapsuleItem } from "@/shared/models/capsule";
import type { MemoryGreetingPayload, MemorySuggestPayload } from "@/shared/models/memory";
import type { DailyQuestionStatePayload } from "@/shared/models/profile";
import type { PersonaCardDimensionItem } from "@/shared/models/persona";
import { checkRevealableCapsules, revealTimeCapsule } from "@/shared/services/capsule";
import { ensureAppSession, getSessionUser } from "@/shared/services/auth";
import { fetchMemoryGreeting, fetchMemorySuggest } from "@/shared/services/memory";
import { fetchMyDailyQuestion, fetchMyProfileOverview, submitMyDailyQuestion } from "@/shared/services/profile";
import { SoundManager } from "@/shared/utils/sound-manager";
import { useTestCatalogStore } from "@/stores/test-catalog";

const store = useTestCatalogStore();

const greeting = ref<MemoryGreetingPayload | null>(null);
const suggest = ref<MemorySuggestPayload | null>(null);
const dailyQuestion = ref<DailyQuestionStatePayload | null>(null);
const revealItem = ref<TimeCapsuleItem | null>(null);
const revealVisible = ref(false);
const selectedCategory = ref("全部");
const topTab = ref("热门");
const bannerCountDown = ref(5 * 60 + 21);
const dailySubmitting = ref(false);
const overviewDimensions = ref<PersonaCardDimensionItem[]>([]);
const loading = computed(() => store.loading);
const error = computed(() => store.error);
let bannerTimer: ReturnType<typeof setInterval> | null = null;

function playIfEnabled(type: "chime" | "ding" | "whoosh" | "ambient") {
  if (SoundManager.isSoundEnabled()) {
    SoundManager.play(type);
  }
}

const categoryTabs = [
  "全部",
  "性格测试",
  "情感探索",
  "关系匹配",
  "职业测评",
  "趣味测试",
];

const tests = computed(() => store.tests);
const userAvatar = computed(() => getSessionUser()?.avatar_value || "🫧");
const unreadCount = computed(() => Math.min(99, Math.max(1, Math.floor((greeting.value?.know_level || 0) / 7) || 3)));
const memoryPercent = computed(() => Math.min(100, Math.max(0, greeting.value?.know_level || 0)));
const memoryLevel = computed(() => {
  const value = greeting.value?.know_level || 0;
  if (value >= 80) {
    return "灵魂熟友";
  }
  if (value >= 50) {
    return "默契升温";
  }
  return "初次相识";
});
const heroParticipants = computed(() => {
  const fallback = tests.value[0]?.participant_count || 0;
  return (suggest.value?.items?.[0]?.participant_count || fallback) + 1200;
});
const heroRecommended = computed(() => suggest.value?.items?.[0] || tests.value[0] || null);
const friendTests = computed(() => tests.value.filter((item) => item.is_match_enabled).slice(0, 2));
const filteredTests = computed(() => {
  if (selectedCategory.value === "全部") {
    return tests.value;
  }
  if (selectedCategory.value === "关系匹配") {
    return tests.value.filter((item) => item.is_match_enabled);
  }
  return tests.value.filter((item) => item.category.includes(selectedCategory.value.slice(0, 2)));
});
const hotTests = computed(() =>
  filteredTests.value
    .slice()
    .sort((a, b) => b.participant_count - a.participant_count)
    .slice(0, 6),
);
const tickerItems = computed(() => {
  const name = greeting.value?.greeting || "今天也要闪闪发光";
  const firstTest = tests.value[0]?.name || "MBTI 快速测试";
  const totalParticipants = tests.value.reduce((sum, item) => sum + item.participant_count, 0);
  return [
    `小鱼 刚完成了 ${firstTest}`,
    `${Math.max(1800, totalParticipants)}人正在测MBTI`,
    `${name.slice(0, 12)}… 小测记住你了`,
  ];
});
const soulCardState = computed(() => {
  const count = greeting.value?.test_count || 0;
  if (count <= 0) {
    return "locked";
  }
  if (count < 2) {
    return "seed";
  }
  return "full";
});
const soulLevel = computed(() => Math.min(99, Math.max(1, 10 + (greeting.value?.test_count || 0) * 8)));
const soulKeywords = computed(() => {
  const tags = greeting.value?.behavior_tags || [];
  return tags.length ? tags.slice(0, 4) : ["温柔", "洞察", "共情"];
});
const dailyResultLabel = computed(() => {
  if (!dailyQuestion.value?.answered) {
    return "";
  }
  const index = dailyQuestion.value.selected_index || 0;
  return dailyQuestion.value.options[index] || "";
});
const testCards = computed(() =>
  filteredTests.value.map((item, index) => ({
    ...item,
    emoji: iconForCategory(item.category, index),
    gradient: item.cover_gradient || fallbackGradient(index),
  })),
);

function formatCountDown(seconds: number) {
  const minute = `${Math.floor(seconds / 60)}`.padStart(2, "0");
  const second = `${seconds % 60}`.padStart(2, "0");
  return `${minute}:${second}`;
}

function fallbackGradient(index: number) {
  const presets = [
    "linear-gradient(135deg,#9B7ED8,#E8729A)",
    "linear-gradient(135deg,#E8729A,#F2A68B)",
    "linear-gradient(135deg,#7CC5B2,#9B7ED8)",
    "linear-gradient(135deg,#D4A853,#F2A68B)",
  ];
  return presets[index % presets.length];
}

function iconForCategory(category: string, index: number) {
  if (category.includes("性格")) {
    return "🧠";
  }
  if (category.includes("情感")) {
    return "💗";
  }
  if (category.includes("关系")) {
    return "🤝";
  }
  if (category.includes("职业")) {
    return "💼";
  }
  return ["✨", "🌙", "🎯", "🔮"][index % 4];
}

function mapDimensionsForRadar() {
  const dimensions = overviewDimensions.value;
  if (dimensions.length) {
    return dimensions;
  }
  return [
    { dim_code: "A", label: "开放", score: 68 },
    { dim_code: "B", label: "情绪", score: 72 },
    { dim_code: "C", label: "外向", score: 61 },
    { dim_code: "D", label: "宜人", score: 76 },
    { dim_code: "E", label: "责任", score: 66 },
  ];
}

function openDetail(testCode: string) {
  uni.navigateTo({
    url: `/pages/test/detail?testCode=${testCode}`,
  });
}

function openSoulCard() {
  uni.switchTab({ url: "/pages/profile/index" });
}

function openNotifications() {
  uni.navigateTo({
    url: "/pages/profile/notifications",
  });
}

function openSearch() {
  uni.navigateTo({
    url: "/pages/discover/search",
  });
}

function openDailyPanel() {
  uni.switchTab({ url: "/pages/profile/index" });
}

function goMatch(testCode: string) {
  uni.switchTab({ url: "/pages/match/index" });
  if (testCode) {
    uni.showToast({ title: "可在匹配页发起该测试邀请", icon: "none" });
  }
}

async function answerDaily(index: number) {
  if (!dailyQuestion.value || dailyQuestion.value.answered || dailySubmitting.value) {
    return;
  }
  dailySubmitting.value = true;
  try {
    dailyQuestion.value = await submitMyDailyQuestion(dailyQuestion.value.question_id, index);
    playIfEnabled("ding");
    uni.showToast({ title: "今日回答已记录", icon: "success" });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "提交失败",
      icon: "none",
    });
  } finally {
    dailySubmitting.value = false;
  }
}

async function load() {
  try {
    await ensureAppSession();
    const [testsPayload, greetingPayload, suggestPayload, capsulePayload, dailyPayload, overviewPayload] = await Promise.all([
      store.loadTests(true),
      fetchMemoryGreeting(),
      fetchMemorySuggest(),
      checkRevealableCapsules(),
      fetchMyDailyQuestion(),
      fetchMyProfileOverview(),
    ]);
    void testsPayload;
    greeting.value = greetingPayload;
    suggest.value = suggestPayload;
    dailyQuestion.value = dailyPayload;
    const topDimensions = overviewPayload.dominant_dimensions.slice(0, 5);
    const maxScore = Math.max(...topDimensions.map((item) => item.total_score), 1);
    overviewDimensions.value = topDimensions.map((item) => ({
      dim_code: item.dim_code,
      label: item.dim_code.toUpperCase(),
      score: Math.round((item.total_score / maxScore) * 100),
    }));

    if (capsulePayload.has_revealable && capsulePayload.items.length) {
      revealItem.value = capsulePayload.items[0];
      revealVisible.value = true;
      playIfEnabled("chime");
    }
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "首页加载失败，请稍后重试",
      icon: "none",
    });
  }
}

async function closeReveal() {
  if (revealItem.value) {
    try {
      await revealTimeCapsule(revealItem.value.id);
    } catch (err) {
      uni.showToast({
        title: err instanceof Error ? err.message : "胶囊揭示失败",
        icon: "none",
      });
    }
  }
  revealVisible.value = false;
  revealItem.value = null;
}

function startCountdown() {
  if (bannerTimer) {
    clearInterval(bannerTimer);
  }
  bannerTimer = setInterval(() => {
    if (bannerCountDown.value <= 1) {
      bannerCountDown.value = 5 * 60 + 21;
      return;
    }
    bannerCountDown.value -= 1;
  }, 1000);
}

function clearCountdown() {
  if (bannerTimer) {
    clearInterval(bannerTimer);
    bannerTimer = null;
  }
}

onShow(() => {
  void load();
  startCountdown();
});

onHide(() => {
  clearCountdown();
});

onUnload(() => {
  clearCountdown();
});
</script>

<template>
  <view class="page">
    <view class="topbar glass-strong d1">
      <view class="brand">
        <view class="brand__logo">心</view>
        <view>
          <text class="brand__name">心测</text>
          <text class="brand__sub">灵魂说明书</text>
        </view>
      </view>
      <view class="topbar__actions">
        <view class="bell" @tap="openNotifications">
          <text>🔔</text>
          <text class="bell__badge">{{ unreadCount }}</text>
        </view>
        <view class="avatar">{{ userAvatar }}</view>
      </view>
    </view>

    <view class="search glass d1" @tap="openSearch">
      <text class="search__icon">🔍</text>
      <text class="search__placeholder">搜索测试、话题...</text>
    </view>

    <view class="ticker d2">
      <view class="ticker__inner">
        <text v-for="item in tickerItems" :key="item" class="ticker__item">{{ item }}</text>
      </view>
    </view>

    <view class="hero d2">
      <view class="hero__bg" />
      <view class="hero__body">
        <view class="hero__left">
          <XiaoCe expression="happy" size="lg" :animated="true" />
          <XcBubble
            :text="greeting?.greeting || '今天一起探索你的灵魂坐标吧'"
            :persistent="true"
            :typing="true"
          />
        </view>
        <view class="hero__right">
          <text class="hero__hint">推荐你先测</text>
          <text class="hero__title">{{ heroRecommended?.name || "今日灵魂快测" }}</text>
          <button class="hero__cta" @tap="heroRecommended && openDetail(heroRecommended.test_code)">
            开始测试
          </button>
        </view>
      </view>
      <view class="hero__foot">
        <view class="hero__avatars">
          <text>🦊</text>
          <text>🐱</text>
          <text>🐰</text>
          <text>🦄</text>
        </view>
        <text>{{ heroParticipants }}人参与中</text>
      </view>
    </view>

    <view class="section d3" @tap="openSoulCard">
      <view class="soul-card xc-card">
        <view class="section__head">
          <text class="section__title">灵魂画像</text>
          <text class="section__more">查看详情 ›</text>
        </view>
        <view v-if="soulCardState === 'locked'" class="soul-locked">
          <text class="soul-locked__icon">🔒</text>
          <text class="soul-locked__text">完成首次测试解锁灵魂画像</text>
        </view>
        <view v-else-if="soulCardState === 'seed'" class="soul-seed">
          <text class="soul-seed__title">画像正在发芽</text>
          <text class="soul-seed__meta">再完成一次测试，即可解锁完整五维雷达</text>
          <view class="soul-seed__tags">
            <text v-for="item in soulKeywords" :key="item">{{ item }}</text>
          </view>
        </view>
        <view v-else class="soul-full">
          <PersonaRadarCanvas :dimensions="mapDimensionsForRadar()" />
          <view class="soul-full__meta">
            <text>灵魂等级 Lv.{{ soulLevel }}</text>
            <view class="soul-full__tags">
              <text v-for="item in soulKeywords" :key="item">{{ item }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view class="section d3">
      <view class="daily" @tap="openDailyPanel">
        <text class="daily__title">今日灵魂提问</text>
        <text class="daily__question">{{ dailyQuestion?.question_text || "今天，你最像哪种天气？" }}</text>
        <view v-if="dailyQuestion && !dailyQuestion.answered" class="daily__options">
          <button
            v-for="(item, index) in dailyQuestion.options.slice(0, 4)"
            :key="`${dailyQuestion.question_id}-${item}`"
            class="daily__option"
            :disabled="dailySubmitting"
            @tap.stop="answerDaily(index)"
          >
            <text>{{ ["🙂", "🤩", "🌧️", "🔥"][index] || "✨" }}</text>
            <text>{{ item }}</text>
          </button>
        </view>
        <view v-else-if="dailyQuestion" class="daily__result">
          <text>今日选择：{{ dailyResultLabel }}</text>
          <text>{{ dailyQuestion.insight || "今天也在认真探索自己。" }}</text>
          <text class="daily__badge">连续 {{ dailyQuestion.current_streak }} 天</text>
        </view>
      </view>
    </view>

    <view class="section d4">
      <view class="memory xc-glass">
        <view class="section__head">
          <text class="section__title">小测记忆栏</text>
          <text class="section__more">{{ memoryLevel }}</text>
        </view>
        <text class="memory__text">{{ greeting?.greeting || "小测已经开始记住你啦" }}</text>
        <view class="memory__track">
          <view class="memory__fill" :style="{ width: `${memoryPercent}%` }" />
        </view>
        <text class="memory__meta">熟悉度 {{ memoryPercent }}%</text>
        <text class="memory__suggest">
          下一个推荐：{{ suggest?.items?.[0]?.name || "去看看今日热门测试" }}
        </text>
      </view>
    </view>

    <scroll-view scroll-x class="cats d4">
      <view class="cats__list">
        <text
          v-for="item in categoryTabs"
          :key="item"
          class="cats__item"
          :class="{ 'cats__item--active': selectedCategory === item }"
          @tap="selectedCategory = item"
        >
          {{ item }}
        </text>
      </view>
    </scroll-view>

    <view class="section d4">
      <view class="section__head">
        <text class="section__title">热门测试</text>
        <text class="section__more">为你精选</text>
      </view>
      <scroll-view scroll-x class="hot">
        <view class="hot__list">
          <view
            v-for="(item, index) in hotTests"
            :key="item.test_code"
            class="hot-card"
            :style="{ background: item.cover_gradient || fallbackGradient(index) }"
            @tap="openDetail(item.test_code)"
          >
            <text class="hot-card__tag">热门</text>
            <text class="hot-card__emoji">{{ iconForCategory(item.category, index) }}</text>
            <text class="hot-card__title">{{ item.name }}</text>
            <text class="hot-card__desc">{{ item.category }} · {{ item.duration_hint || "约5分钟" }}</text>
            <text class="hot-card__meta">{{ item.participant_count }}人参与</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <view class="limited d5">
      <view class="limited__glint" />
      <view>
        <text class="limited__title">限时热测：MBTI 快速版</text>
        <text class="limited__meta">今日完成可解锁限定徽章</text>
      </view>
      <view class="limited__time">{{ formatCountDown(bannerCountDown) }}</view>
    </view>

    <view class="section d5">
      <view class="section__head">
        <text class="section__title">全部测试</text>
        <text class="section__more">{{ filteredTests.length }}项</text>
      </view>
      <view v-if="loading" class="panel">
        <text class="panel__text">正在加载测试列表...</text>
      </view>
      <view v-else-if="error" class="panel panel--error">
        <text class="panel__text">{{ error }}</text>
      </view>
      <view v-else class="all-list">
        <view
          v-for="(item, index) in testCards"
          :key="item.test_code"
          class="all-item"
          @tap="openDetail(item.test_code)"
        >
          <view class="all-item__icon" :style="{ background: item.gradient }">{{ item.emoji }}</view>
          <view class="all-item__body">
            <text class="all-item__title">{{ item.name }}</text>
            <text class="all-item__desc">{{ item.category }}</text>
            <text class="all-item__meta">{{ item.question_count }}题 · {{ item.duration_hint || "约5分钟" }}</text>
          </view>
          <text class="all-item__arrow">›</text>
        </view>
      </view>
    </view>

    <view v-if="friendTests.length" class="section d5">
      <view class="friend">
        <text class="friend__title">好友一起测更有趣</text>
        <text class="friend__meta">支持匹配报告 · 专属双人洞察</text>
        <view class="friend__list">
          <view
            v-for="item in friendTests"
            :key="item.test_code"
            class="friend__item"
            @tap="goMatch(item.test_code)"
          >
            <text>{{ item.name }}</text>
            <text>匹配专属</text>
          </view>
        </view>
      </view>
    </view>

    <TimeCapsuleReveal :visible="revealVisible" :item="revealItem" @close="closeReveal" />
    <TabBuddy />
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 20rpx 24rpx 40rpx;
}

.glass {
  @include glass;
}

.glass-strong {
  @include glass-strong;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 18rpx;
  border-radius: $xc-r-lg;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.brand__logo {
  width: 56rpx;
  height: 56rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  color: $xc-white;
  font-size: 30rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand__name {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
}

.brand__sub {
  display: block;
  margin-top: 2rpx;
  color: $xc-muted;
  font-size: 20rpx;
}

.topbar__actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.bell {
  position: relative;
  width: 54rpx;
  height: 54rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.75);
}

.bell__badge {
  position: absolute;
  right: -4rpx;
  top: -6rpx;
  min-width: 28rpx;
  padding: 2rpx 6rpx;
  border-radius: 999rpx;
  background: $xc-pink;
  color: $xc-white;
  font-size: 18rpx;
  text-align: center;
}

.avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, $xc-purple-p, $xc-pink-p);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
}

.search {
  margin-top: 16rpx;
  border-radius: 999rpx;
  padding: 18rpx 22rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.search__placeholder {
  color: $xc-muted;
  font-size: 24rpx;
}

.ticker {
  margin-top: 14rpx;
  border-radius: 20rpx;
  padding: 0 18rpx;
  height: 56rpx;
  overflow: hidden;
  background: $xc-purple-p;
  color: $xc-purple-d;
}

.ticker__inner {
  display: flex;
  flex-direction: column;
  animation: tickerY 9s ease-in-out infinite;
}

.ticker__item {
  height: 56rpx;
  line-height: 56rpx;
  font-size: 22rpx;
}

.hero {
  margin-top: 18rpx;
  border-radius: $xc-r-lg;
  overflow: hidden;
  position: relative;
}

.hero__bg {
  position: absolute;
  inset: 0;
  @include gradient-hero;
}

.hero__body {
  position: relative;
  z-index: 1;
  padding: 24rpx;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16rpx;
}

.hero__left :deep(.xc-bubble) {
  margin-top: 10rpx;
}

.hero__right {
  color: $xc-white;
}

.hero__hint {
  display: block;
  font-size: 20rpx;
  opacity: 0.85;
}

.hero__title {
  display: block;
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.4;
}

.hero__cta {
  margin-top: 18rpx;
  height: 64rpx;
  line-height: 64rpx;
  border-radius: 999rpx;
  background: $xc-white;
  color: $xc-purple-d;
  font-size: 24rpx;
  font-weight: 700;
}

.hero__foot {
  position: relative;
  z-index: 1;
  padding: 0 24rpx 18rpx;
  color: rgba(255, 255, 255, 0.92);
  font-size: 22rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.hero__avatars {
  display: flex;
}

.hero__avatars text {
  margin-left: -8rpx;
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.24);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18rpx;
}

.hero__avatars text:first-child {
  margin-left: 0;
}

.section {
  margin-top: 28rpx;
}

.section__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section__title {
  font-size: 30rpx;
  font-weight: 700;
}

.section__more {
  color: $xc-muted;
  font-size: 22rpx;
}

.soul-card {
  padding: 20rpx;
}

.soul-locked,
.soul-seed {
  margin-top: 14rpx;
  border-radius: 20rpx;
  padding: 24rpx;
  background: linear-gradient(145deg, rgba(58, 46, 66, 0.9), rgba(95, 75, 119, 0.82));
  color: $xc-white;
}

.soul-locked__icon {
  font-size: 48rpx;
}

.soul-locked__text,
.soul-seed__meta {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  opacity: 0.9;
}

.soul-seed__title {
  font-size: 28rpx;
  font-weight: 700;
}

.soul-seed__tags,
.soul-full__tags {
  margin-top: 12rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.soul-seed__tags text,
.soul-full__tags text {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 20rpx;
}

.soul-full {
  margin-top: 8rpx;
}

.soul-full__meta {
  margin-top: 8rpx;
  font-size: 24rpx;
}

.daily {
  padding: 24rpx;
  border-radius: $xc-r-lg;
  background: linear-gradient(160deg, rgba(58, 46, 66, 0.95), rgba(80, 62, 100, 0.85));
  color: $xc-white;
}

.daily__title {
  color: $xc-gold-l;
  font-size: 24rpx;
  font-weight: 700;
}

.daily__question {
  display: block;
  margin-top: 12rpx;
  font-size: 30rpx;
  line-height: 1.45;
}

.daily__options {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
}

.daily__option {
  height: 72rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.16);
  color: $xc-white;
  font-size: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
}

.daily__result {
  margin-top: 16rpx;
  font-size: 23rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.daily__badge {
  display: inline-block;
  align-self: flex-start;
  padding: 5rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(212, 168, 83, 0.3);
  color: $xc-gold-l;
}

.memory {
  padding: 22rpx;
  border-radius: $xc-r-lg;
}

.memory__text,
.memory__meta,
.memory__suggest {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  color: $xc-muted;
}

.memory__track {
  margin-top: 12rpx;
  height: 12rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  overflow: hidden;
}

.memory__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, $xc-purple, $xc-pink);
}

.cats {
  margin-top: 22rpx;
}

.cats__list {
  display: flex;
  gap: 10rpx;
}

.cats__item {
  flex-shrink: 0;
  padding: 12rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.9);
  color: $xc-muted;
  font-size: 22rpx;
  border: 1px solid rgba(155, 126, 216, 0.08);
}

.cats__item--active {
  background: $xc-purple;
  color: $xc-white;
}

.hot {
  margin-top: 12rpx;
}

.hot__list {
  display: flex;
  gap: 14rpx;
}

.hot-card {
  flex-shrink: 0;
  width: 280rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  color: $xc-white;
  position: relative;
}

.hot-card__tag {
  position: absolute;
  right: 16rpx;
  top: 14rpx;
  font-size: 18rpx;
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  background: rgba(255, 70, 90, 0.88);
}

.hot-card__emoji {
  font-size: 38rpx;
}

.hot-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 27rpx;
  font-weight: 700;
}

.hot-card__desc,
.hot-card__meta {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  opacity: 0.9;
}

.limited {
  margin-top: 26rpx;
  border-radius: 22rpx;
  padding: 18rpx 20rpx;
  background: linear-gradient(135deg, $xc-purple-p, $xc-pink-p, $xc-peach-p);
  border: 2rpx solid rgba(155, 126, 216, 0.16);
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.limited__glint {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.45), transparent);
  background-size: 200% 100%;
  animation: shimmer 2.4s linear infinite;
}

.limited__title,
.limited__meta {
  display: block;
  position: relative;
  z-index: 1;
}

.limited__title {
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-purple-d;
}

.limited__meta {
  margin-top: 6rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

.limited__time {
  position: relative;
  z-index: 1;
  font-size: 26rpx;
  color: $xc-purple-d;
  font-weight: 800;
}

.panel {
  padding: 24rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.88);
}

.panel__text {
  color: $xc-muted;
  font-size: 24rpx;
}

.panel--error {
  background: rgba(255, 240, 245, 0.88);
}

.all-list {
  margin-top: 12rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.all-item {
  @include card-base;
  padding: 18rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
  position: relative;
  overflow: hidden;
}

.all-item::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: 1px solid transparent;
  animation: rainbow 5s linear infinite;
  pointer-events: none;
}

.all-item__icon {
  width: 74rpx;
  height: 74rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
}

.all-item__body {
  flex: 1;
  min-width: 0;
}

.all-item__title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}

.all-item__desc,
.all-item__meta {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.all-item__arrow {
  color: $xc-muted;
  font-size: 34rpx;
}

.friend {
  border-radius: 24rpx;
  border: 2rpx solid rgba(232, 114, 154, 0.32);
  background: rgba(255, 255, 255, 0.86);
  padding: 20rpx;
}

.friend__title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}

.friend__meta {
  display: block;
  margin-top: 6rpx;
  color: $xc-muted;
  font-size: 22rpx;
}

.friend__list {
  margin-top: 12rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.friend__item {
  border-radius: 16rpx;
  padding: 14rpx 16rpx;
  background: rgba(253, 230, 239, 0.62);
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
}

.d1,
.d2,
.d3,
.d4,
.d5 {
  animation: fadeInUp 0.5s $xc-ease both;
}

.d1 {
  animation-delay: 0.06s;
}

.d2 {
  animation-delay: 0.12s;
}

.d3 {
  animation-delay: 0.18s;
}

.d4 {
  animation-delay: 0.24s;
}

.d5 {
  animation-delay: 0.3s;
}

::v-deep(::-webkit-scrollbar) {
  display: none;
  width: 0;
  height: 0;
}

@keyframes tickerY {
  0%,
  24% {
    transform: translateY(0);
  }
  33%,
  57% {
    transform: translateY(-56rpx);
  }
  66%,
  90% {
    transform: translateY(-112rpx);
  }
  100% {
    transform: translateY(0);
  }
}

@keyframes rainbow {
  0% {
    border-color: rgba(201, 181, 240, 0.85);
  }
  25% {
    border-color: rgba(244, 165, 191, 0.85);
  }
  50% {
    border-color: rgba(242, 166, 139, 0.85);
  }
  75% {
    border-color: rgba(168, 221, 208, 0.85);
  }
  100% {
    border-color: rgba(201, 181, 240, 0.85);
  }
}
</style>
