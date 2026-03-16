<script setup lang="ts">
import { computed, ref } from "vue";
import { onHide, onShow, onUnload } from "@dcloudio/uni-app";

import TimeCapsuleReveal from "@/components/feedback/TimeCapsuleReveal.vue";
import TabBuddy from "@/components/mascot/TabBuddy.vue";
import XiaoCe from "@/components/mascot/XiaoCe.vue";
// XcBubble available for future use
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

function openMatchCenter() {
  uni.switchTab({ url: "/pages/match/index" });
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
  <view class="page xc-enter">
    <view class="topbar glass-strong d1 xc-card-lift">
      <view class="brand">
        <view class="brand__logo">
          <text class="brand__logo-text">心</text>
          <view class="brand__logo-shimmer" />
        </view>
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
        <view class="avatar" :style="{ border: '2px solid #fff', boxShadow: '0 2px 8px rgba(155,126,216,0.15)' }">{{ userAvatar }}</view>
      </view>
    </view>

    <view class="search glass d1 xc-card-lift" @tap="openSearch">
      <text class="search__icon">🔍</text>
      <text class="search__placeholder">搜索测试、话题...</text>
    </view>

    <view class="ticker d2">
      <view class="ticker__dot" />
      <view class="ticker__wrap">
        <view class="ticker__inner">
          <text v-for="item in tickerItems" :key="item" class="ticker__item">{{ item }}</text>
        </view>
      </view>
    </view>

    <view class="hero d2 xc-card-lift">
      <view class="hero__bg">
        <view class="hero__bg-overlay" />
      </view>
      <view class="hero__content">
        <view class="hero__badge-tag">
          <text>✨</text>
          <text>每日精选</text>
        </view>
        <text class="hero__title">{{ heroRecommended?.name || "今日灵魂快测" }}</text>
        <text class="hero__desc">{{ heroRecommended?.description || "用15种创新互动方式，探索你的灵魂坐标" }}</text>
        <button class="hero__cta" @tap="heroRecommended && openDetail(heroRecommended.test_code)">
          <text>开始探索</text>
          <text class="hero__cta-arrow">→</text>
        </button>
        <view class="hero__foot">
          <view class="hero__avatars">
            <text>🦊</text>
            <text>🐱</text>
            <text>🐰</text>
            <text>🦄</text>
          </view>
          <text class="hero__count">{{ heroParticipants }}人参与中</text>
        </view>
      </view>
      <view class="hero__mascot xc-float-soft">
        <XiaoCe expression="happy" size="lg" :animated="true" />
      </view>
    </view>

    <view class="quick-grid d3">
      <view class="quick-item xc-card-lift" @tap="openSoulCard">
        <view class="quick-item__icon" style="background: linear-gradient(135deg, #9B7ED8, #C9B5F0)">🧬</view>
        <text class="quick-item__label">灵魂画像</text>
      </view>
      <view class="quick-item xc-card-lift" @tap="openMatchCenter">
        <view class="quick-item__icon" style="background: linear-gradient(135deg, #E8729A, #F4A5BF)">💞</view>
        <text class="quick-item__label">灵魂匹配</text>
      </view>
      <view class="quick-item xc-card-lift" @tap="openDailyPanel">
        <view class="quick-item__icon" style="background: linear-gradient(135deg, #7CC5B2, #A8DDD0)">📅</view>
        <text class="quick-item__label">运势日历</text>
      </view>
      <view class="quick-item xc-card-lift" @tap="openSoulCard">
        <view class="quick-item__icon" style="background: linear-gradient(135deg, #D4A853, #E5C97E)">🏅</view>
        <text class="quick-item__label">成就勋章</text>
      </view>
    </view>

    <view class="section d3" @tap="openSoulCard">
      <view class="soul-card xc-card xc-card-lift">
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
            @tap="openDetail(item.test_code)"
          >
            <view class="hot-card__img" :style="{ background: item.cover_gradient || fallbackGradient(index) }">
              <text class="hot-card__tag">🔥 热门</text>
              <text class="hot-card__emoji">{{ iconForCategory(item.category, index) }}</text>
            </view>
            <view class="hot-card__body">
              <text class="hot-card__title">{{ item.name }}</text>
              <text class="hot-card__desc">{{ item.description || item.category }}</text>
              <view class="hot-card__meta">
                <text>📝 {{ item.question_count }}题</text>
                <text>⏱️ {{ item.duration_hint || "约5分钟" }}</text>
                <text>👥 {{ item.participant_count }}</text>
              </view>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <view class="limited d5" @tap="tests.length && openDetail(tests[0].test_code)">
      <view class="limited__glint" />
      <text class="limited__icon">⏰</text>
      <view class="limited__body">
        <text class="limited__title">限时热测：MBTI 快速版</text>
        <text class="limited__meta">今日完成可解锁限定徽章</text>
      </view>
      <view class="limited__timer">
        <text class="limited__timer-val">{{ formatCountDown(bannerCountDown) }}</text>
        <text class="limited__timer-label">剩余时间</text>
      </view>
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
  padding: 20rpx 24rpx calc(#{$xc-tab-h} + 40rpx);
}

.glass {
  @include glass;
}

.glass-strong {
  @include glass-strong;
}

/* --- Topbar --- */
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
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  color: $xc-white;
  font-size: 28rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(155, 126, 216, 0.35);
  position: relative;
  overflow: hidden;
}

.brand__logo-text {
  position: relative;
  z-index: 1;
}

.brand__logo-shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, transparent 40%, rgba(255, 255, 255, 0.25) 50%, transparent 60%);
  animation: shimmer 3s infinite;
  background-size: 200% 100%;
}

.brand__name {
  display: block;
  font-family: $xc-font-serif;
  font-size: 32rpx;
  font-weight: 900;
  @include text-gradient;
}

.brand__sub {
  display: block;
  margin-top: 2rpx;
  color: $xc-hint;
  font-size: 18rpx;
  letter-spacing: 1px;
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
  transition: transform 0.2s $xc-spring;

  &:active {
    transform: scale(0.9);
  }
}

.bell__badge {
  position: absolute;
  right: -6rpx;
  top: -6rpx;
  min-width: 28rpx;
  padding: 2rpx 7rpx;
  border-radius: 999rpx;
  background: $xc-pink;
  color: $xc-white;
  font-size: 18rpx;
  text-align: center;
  font-weight: 600;
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

/* --- Search --- */
.search {
  margin-top: 16rpx;
  border-radius: 999rpx;
  padding: 18rpx 22rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  transition: box-shadow 0.3s;

  &:active {
    box-shadow: $xc-sh-md;
  }
}

.search__placeholder {
  color: $xc-hint;
  font-size: 24rpx;
}

/* --- Ticker --- */
.ticker {
  margin-top: 14rpx;
  border-radius: 20rpx;
  padding: 0 18rpx;
  height: 56rpx;
  overflow: hidden;
  background: linear-gradient(90deg, $xc-purple-p, $xc-pink-p);
  color: $xc-purple-d;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.ticker__dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: $xc-pink;
  flex-shrink: 0;
  animation: pulse 1.5s infinite;
}

.ticker__wrap {
  flex: 1;
  height: 56rpx;
  overflow: hidden;
  position: relative;
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
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* --- Hero --- */
.hero {
  margin-top: 18rpx;
  border-radius: $xc-r-lg;
  overflow: hidden;
  position: relative;
  min-height: 340rpx;
}

.hero__bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #7C5DBF 0%, #B57FE0 30%, #E8729A 60%, #F2A68B 100%);
  z-index: 0;
}

.hero__bg-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.15), transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.12), transparent 40%);
}

.hero__content {
  position: relative;
  z-index: 2;
  padding: 36rpx 28rpx 20rpx;
  color: $xc-white;
}

.hero__badge-tag {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  padding: 8rpx 16rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  letter-spacing: 0.5px;
  // #ifdef H5
  backdrop-filter: blur(8px);
  // #endif
}

.hero__title {
  display: block;
  margin-top: 16rpx;
  font-family: $xc-font-serif;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.35;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.hero__desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  opacity: 0.85;
  line-height: 1.6;
}

.hero__cta {
  margin-top: 24rpx;
  display: inline-flex;
  align-items: center;
  gap: 10rpx;
  padding: 16rpx 36rpx;
  background: $xc-white;
  color: $xc-purple-d;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s $xc-spring;

  &:active {
    transform: scale(0.95);
  }
}

.hero__cta-arrow {
  font-size: 26rpx;
}

.hero__foot {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-top: 18rpx;
}

.hero__avatars {
  display: flex;
}

.hero__avatars text {
  margin-left: -10rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18rpx;
}

.hero__avatars text:first-child {
  margin-left: 0;
}

.hero__count {
  font-size: 22rpx;
  opacity: 0.85;
}

.hero__mascot {
  position: absolute;
  right: 24rpx;
  top: 24rpx;
  z-index: 3;
  animation: gentleBounce 2s infinite;
}

/* --- Quick Grid --- */
.quick-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14rpx;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
  padding: 18rpx 10rpx;
  border-radius: $xc-r;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid $xc-line;
  box-shadow: $xc-sh-sm;
  transition: transform 0.2s $xc-spring;

  &:active {
    transform: scale(0.95);
    box-shadow: $xc-sh-md;
  }
}

.quick-item__icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  color: $xc-white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.quick-item__label {
  font-size: 20rpx;
  font-weight: 600;
  color: $xc-ink;
}

/* --- Sections --- */
.section {
  margin-top: 28rpx;
}

.section__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14rpx;
}

.section__title {
  font-size: 30rpx;
  font-weight: 800;
}

.section__more {
  color: $xc-hint;
  font-size: 22rpx;
  display: flex;
  align-items: center;
  gap: 4rpx;
}

/* --- Soul Card --- */
.soul-card {
  padding: 24rpx;
}

.soul-locked,
.soul-seed {
  margin-top: 14rpx;
  border-radius: 20rpx;
  padding: 28rpx;
  background: linear-gradient(145deg, rgba(58, 46, 66, 0.92), rgba(95, 75, 119, 0.85));
  color: $xc-white;
}

.soul-locked__icon {
  font-size: 48rpx;
  animation: hiddenShake 2s infinite;
}

.soul-locked__text,
.soul-seed__meta {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  opacity: 0.9;
  line-height: 1.6;
}

.soul-seed__title {
  font-size: 30rpx;
  font-weight: 700;
}

.soul-seed__tags,
.soul-full__tags {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.soul-seed__tags text,
.soul-full__tags text {
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 20rpx;
}

.soul-full {
  margin-top: 10rpx;
}

.soul-full__meta {
  margin-top: 12rpx;
  font-size: 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* --- Daily Soul Question --- */
.daily {
  padding: 28rpx;
  border-radius: $xc-r-lg;
  background: linear-gradient(160deg, rgba(58, 46, 66, 0.95), rgba(80, 62, 100, 0.85));
  color: $xc-white;
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: -30rpx;
    right: -30rpx;
    width: 120rpx;
    height: 120rpx;
    border-radius: 50%;
    background: rgba(212, 168, 83, 0.12);
  }
}

.daily__title {
  color: $xc-gold-l;
  font-size: 24rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.daily__question {
  display: block;
  margin-top: 14rpx;
  font-size: 30rpx;
  font-weight: 500;
  line-height: 1.5;
}

.daily__options {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12rpx;
}

.daily__option {
  height: 76rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.14);
  color: $xc-white;
  font-size: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  transition: all 0.2s $xc-spring;
  // #ifdef H5
  backdrop-filter: blur(4px);
  // #endif

  &:active {
    background: rgba(155, 126, 216, 0.45);
    transform: scale(0.96);
  }
}

.daily__result {
  margin-top: 18rpx;
  font-size: 23rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  animation: fadeInUp 0.4s $xc-ease;
}

.daily__badge {
  display: inline-block;
  align-self: flex-start;
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(212, 168, 83, 0.3);
  color: $xc-gold-l;
  font-size: 22rpx;
  font-weight: 600;
}

/* --- Memory Bar --- */
.memory {
  padding: 24rpx;
  border-radius: $xc-r-lg;
}

.memory__text,
.memory__meta,
.memory__suggest {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  color: $xc-muted;
  line-height: 1.5;
}

.memory__track {
  margin-top: 14rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  overflow: hidden;
}

.memory__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, $xc-purple, $xc-pink);
  transition: width 0.6s $xc-ease;
}

/* --- Category Tabs --- */
.cats {
  margin-top: 22rpx;
}

.cats__list {
  display: flex;
  gap: 10rpx;
}

.cats__item {
  flex-shrink: 0;
  padding: 14rpx 22rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.9);
  color: $xc-muted;
  font-size: 22rpx;
  font-weight: 600;
  border: 1.5px solid rgba(155, 126, 216, 0.08);
  transition: all 0.3s;
}

.cats__item--active {
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  color: $xc-white;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(155, 126, 216, 0.25);
}

/* --- Hot Cards --- */
.hot {
  margin-top: 12rpx;
}

.hot__list {
  display: flex;
  gap: 14rpx;
}

.hot-card {
  flex-shrink: 0;
  width: 320rpx;
  border-radius: 22rpx;
  overflow: hidden;
  transition: transform 0.2s $xc-ease;

  &:active {
    transform: scale(0.97);
  }
}

.hot-card__img {
  height: 200rpx;
  position: relative;
  overflow: hidden;
}

.hot-card__tag {
  position: absolute;
  right: 14rpx;
  top: 14rpx;
  font-size: 18rpx;
  padding: 5rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(232, 114, 154, 0.85);
  color: $xc-white;
  font-weight: 700;
  // #ifdef H5
  backdrop-filter: blur(4px);
  // #endif
}

.hot-card__emoji {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 72rpx;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
}

.hot-card__body {
  padding: 16rpx 18rpx;
  background: $xc-card-solid;
  border: 1px solid rgba(155, 126, 216, 0.06);
  border-top: none;
  border-radius: 0 0 22rpx 22rpx;
}

.hot-card__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
}

.hot-card__desc {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: $xc-muted;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-card__meta {
  display: flex;
  gap: 10rpx;
  margin-top: 10rpx;
  font-size: 20rpx;
  color: $xc-hint;
}

/* --- Limited Banner --- */
.limited {
  margin-top: 26rpx;
  border-radius: 22rpx;
  padding: 20rpx 22rpx;
  background: linear-gradient(135deg, #FFF0E8, #FDE6EF);
  border: 1.5px solid rgba(232, 114, 154, 0.15);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  gap: 16rpx;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

.limited__glint {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  background-size: 200% 100%;
  animation: shimmer 3s infinite;
}

.limited__icon {
  font-size: 48rpx;
  position: relative;
  z-index: 1;
}

.limited__body {
  flex: 1;
  position: relative;
  z-index: 1;
}

.limited__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-pink;
}

.limited__meta {
  display: block;
  margin-top: 4rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

.limited__timer {
  position: relative;
  z-index: 1;
  text-align: center;
}

.limited__timer-val {
  display: block;
  font-size: 28rpx;
  font-weight: 900;
  color: $xc-pink;
  font-variant-numeric: tabular-nums;
}

.limited__timer-label {
  display: block;
  font-size: 18rpx;
  color: $xc-hint;
}

/* --- Status panels --- */
.panel {
  padding: 28rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.88);
  text-align: center;
}

.panel__text {
  color: $xc-muted;
  font-size: 24rpx;
}

.panel--error {
  background: rgba(255, 240, 245, 0.88);

  .panel__text {
    color: $xc-pink;
  }
}

/* --- All Tests List --- */
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
  gap: 16rpx;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s $xc-ease, box-shadow 0.2s;

  &:active {
    transform: scale(0.98);
    box-shadow: $xc-sh-md;
  }

  &::after {
    content: "";
    position: absolute;
    inset: -2rpx;
    border-radius: inherit;
    border: 2px solid transparent;
    animation: rainbow 5s linear infinite;
    pointer-events: none;
    opacity: 0.5;
  }
}

.all-item__icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  position: relative;
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
  color: $xc-hint;
  font-size: 30rpx;
}

/* --- Friend Tests --- */
.friend {
  border-radius: 24rpx;
  border: 2rpx solid rgba(232, 114, 154, 0.32);
  background: rgba(255, 255, 255, 0.86);
  padding: 24rpx;
  position: relative;
  overflow: hidden;
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
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.friend__item {
  border-radius: 16rpx;
  padding: 16rpx 18rpx;
  background: linear-gradient(135deg, rgba(253, 230, 239, 0.6), rgba(255, 240, 232, 0.6));
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 24rpx;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.98);
  }
}

/* --- Cascading animations --- */
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
