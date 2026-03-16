<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import XcBubble from "@/components/mascot/XcBubble.vue";
import type { PublishedTestDetail } from "@/shared/models/tests";
import { resolveTestTheme } from "@/shared/utils/test-ui";
import { SoundManager } from "@/shared/utils/sound-manager";
import { useTestCatalogStore } from "@/stores/test-catalog";

const store = useTestCatalogStore();

const detail = ref<PublishedTestDetail | null>(null);
const loading = ref(true);
const error = ref("");

const theme = computed(() => resolveTestTheme(detail.value?.category));
const liveTickerItems = computed(() => {
  if (!detail.value) {
    return [
      "刚刚又有 3 个人开始探索这套测试",
      "完成后会解锁专属人格画像",
      "报告会展示维度、画像和建议",
    ];
  }
  return [
    `${detail.value.participant_count || 0} 人正在查看这套测试`,
    `共 ${detail.value.question_count} 题，建议凭第一直觉作答`,
    detail.value.is_match_enabled ? "做完后还能发起好友匹配挑战" : "完成后会直接生成完整个人报告",
  ];
});
const previewItems = computed(() => {
  if (!detail.value) {
    return [
      { emoji: "🔮", label: "人格画像" },
      { emoji: "☁️", label: "灵魂天气" },
      { emoji: "🧭", label: "维度雷达" },
    ];
  }
  const personaNames = detail.value.personas.slice(0, 3).map((item) => item.persona_name);
  if (personaNames.length) {
    return personaNames.map((item, index) => ({
      emoji: ["🔮", "✨", "🪞"][index] || "🔮",
      label: item,
    }));
  }
  return [
    { emoji: "🔮", label: "人格画像" },
    { emoji: "☁️", label: "灵魂天气" },
    { emoji: "🧭", label: "维度雷达" },
  ];
});
const reviewItems = computed(() => {
  const category = detail.value?.category || "";
  if (category.includes("关系")) {
    return [
      { avatar: "🐱", bg: "var(--xc-pink-soft)", text: "做完之后突然更懂我和朋友为什么会一秒合拍。" },
      { avatar: "🦊", bg: "var(--xc-purple-soft)", text: "不是空泛鸡汤，报告里的关系节奏感挺准。" },
      { avatar: "🐰", bg: "var(--xc-peach-soft)", text: "适合和朋友一起测，结果很有讨论欲。" },
    ];
  }
  if (category.includes("职业")) {
    return [
      { avatar: "🦉", bg: "var(--xc-gold-soft)", text: "职业建议比我想象中更具体，不像泛泛而谈。" },
      { avatar: "🐼", bg: "var(--xc-purple-soft)", text: "对我在团队里的角色抓得挺准。" },
      { avatar: "🦊", bg: "var(--xc-peach-soft)", text: "做完后更知道自己适合什么工作状态。" },
    ];
  }
  return [
    { avatar: "🐱", bg: "var(--xc-pink-soft)", text: "题目很顺滑，像在被慢慢拆开看见自己。" },
    { avatar: "🦊", bg: "var(--xc-purple-soft)", text: "报告里的描述很细，我朋友说像把我看穿了。" },
    { avatar: "🐰", bg: "var(--xc-mint-soft)", text: "不是冷冰冰测试，更像一场有仪式感的探索。" },
  ];
});
const detailHook = computed(() => {
  const category = detail.value?.category || "";
  if (category.includes("关系")) {
    return "小测悄悄说：关系里的答案，往往藏在你最自然的反应里。";
  }
  if (category.includes("职业")) {
    return "小测悄悄说：工作状态没有标准答案，顺手和舒展最重要。";
  }
  if (category.includes("情感")) {
    return "小测悄悄说：别急着给自己下定义，先听听内心怎么回答。";
  }
  return "小测悄悄说：你越诚实地作答，后面的画像就越像真正的你。";
});
const startButtonText = computed(() =>
  detail.value?.is_match_enabled ? "开始挑战，看看你们有多配" : "揭开你的隐藏人格",
);

async function loadDetail(testCode: string) {
  loading.value = true;
  error.value = "";
  try {
    detail.value = await store.loadDetail(testCode, true);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "测试详情加载失败";
  } finally {
    loading.value = false;
  }
}

function startTest() {
  if (!detail.value) {
    return;
  }
  if (SoundManager.isSoundEnabled()) {
    SoundManager.play("whoosh");
  }
  uni.navigateTo({
    url: `/pages/test/answer?testCode=${detail.value.test_code}`,
  });
}

function goBack() {
  uni.navigateBack();
}

onLoad((query) => {
  const testCode = query && typeof query.testCode === "string" ? query.testCode : "";
  if (!testCode) {
    error.value = "缺少 testCode 参数";
    loading.value = false;
    return;
  }
  void loadDetail(testCode);
});
</script>

<template>
  <view class="page">
    <view class="page__ambient page__ambient--one" />
    <view class="page__ambient page__ambient--two" />

    <view v-if="loading" class="state-card">
      <text class="state-card__text">正在加载测试详情...</text>
    </view>

    <view v-else-if="error" class="state-card state-card--error">
      <text class="state-card__text">{{ error }}</text>
    </view>

    <view v-else-if="detail" class="detail xc-enter">
      <view class="detail__ticker anim-fu xc-enter xc-enter--1">
        <text class="detail__ticker-dot" />
        <swiper
          class="detail__ticker-swiper"
          autoplay
          circular
          interval="2800"
          duration="500"
          vertical
        >
          <swiper-item v-for="item in liveTickerItems" :key="item" class="detail__ticker-item">
            <text>{{ item }}</text>
          </swiper-item>
        </swiper>
      </view>

      <view class="detail__hero xc-card-lift xc-enter xc-enter--1" :class="theme.heroClass" :style="{ background: theme.gradient }">
        <view class="detail__back" @tap="goBack">
          <text>‹</text>
        </view>
        <text class="detail__emoji">{{ theme.emoji }}</text>
        <text class="detail__title">{{ detail.name }}</text>
        <text class="detail__sub">{{ detail.category }}</text>
      </view>

      <view class="detail__stats anim-si xc-enter xc-enter--2">
        <view class="detail__stat">
          <text class="detail__stat-value">{{ detail.question_count }}</text>
          <text class="detail__stat-label">题目数</text>
        </view>
        <view class="detail__stat">
          <text class="detail__stat-value">{{ detail.duration_hint || "约5分钟" }}</text>
          <text class="detail__stat-label">预计用时</text>
        </view>
        <view class="detail__stat">
          <text class="detail__stat-value">{{ detail.participant_count }}</text>
          <text class="detail__stat-label">参与人数</text>
        </view>
      </view>

      <view class="detail__preview anim-fu d1 xc-card-lift xc-enter xc-enter--2">
        <view class="detail__preview-items">
          <view v-for="item in previewItems" :key="item.label">
            <text class="detail__preview-emoji">{{ item.emoji }}</text>
            <text>{{ item.label }}</text>
          </view>
        </view>
        <view class="detail__preview-mask">
          <text>🔒</text>
          <text>完成测试后揭晓你的专属报告</text>
        </view>
      </view>

      <view class="detail__reviews anim-fu d2 xc-card-lift xc-enter xc-enter--3">
        <text class="detail__section-kicker">大家都说</text>
        <view v-for="item in reviewItems" :key="item.text" class="detail__review">
          <view class="detail__review-avatar" :style="{ background: item.bg }">
            <text>{{ item.avatar }}</text>
          </view>
          <text class="detail__review-text">{{ item.text }}</text>
        </view>
      </view>

      <view class="detail__friends anim-fu d3 xc-enter xc-enter--3">
        <view class="detail__friends-avatars">
          <text>🐱</text>
          <text>🦊</text>
          <text>🐰</text>
        </view>
        <text class="detail__friends-text">已有好友参与过这套测试，做完后还能一起聊结果。</text>
      </view>

      <view class="detail__section anim-fu d3 xc-card-lift xc-enter xc-enter--4">
        <text class="detail__section-title">📋 关于测试</text>
        <text class="detail__section-body">
          {{ detail.description || "这是一套兼顾趣味感和洞察力的测试，适合用几分钟看见自己更细微的一面。" }}
        </text>
      </view>

      <view class="detail__section anim-fu d4 xc-card-lift xc-enter xc-enter--4">
        <text class="detail__section-title">🎯 评估维度</text>
        <view class="detail__chips">
          <text
            v-for="item in detail.dimensions"
            :key="item.dim_code"
            class="detail__chip"
            :style="{ background: theme.chipGradient }"
          >
            {{ item.dim_name }}
          </text>
        </view>
      </view>

      <view v-if="detail.personas.length" class="detail__section anim-fu d4 xc-card-lift xc-enter xc-enter--5">
        <text class="detail__section-title">✨ 人格预览</text>
        <view class="detail__persona-list">
          <view v-for="persona in detail.personas.slice(0, 3)" :key="persona.persona_key" class="detail__persona">
            <text class="detail__persona-name">{{ persona.persona_name }}</text>
            <text class="detail__persona-keywords">
              {{ persona.keywords.join(" / ") || "待补充关键词" }}
            </text>
          </view>
        </view>
      </view>

      <view v-if="detail.is_match_enabled" class="detail__section anim-fu d5 xc-card-lift xc-enter xc-enter--5">
        <text class="detail__section-title">💕 匹配玩法</text>
        <text class="detail__section-body">
          完成答题后可以邀请另一位用户参与同一测试，系统会生成你们的专属匹配报告，看见彼此的契合与差异。
        </text>
      </view>

      <view class="detail__bubble-wrap anim-fu d5 xc-enter xc-enter--5">
        <XcBubble :text="detailHook" :persistent="true" />
      </view>

      <button class="detail__button anim-fu d5 xc-card-lift xc-enter xc-enter--5" :class="`detail__button--${theme.buttonClass}`" @tap="startTest">
        <text>{{ startButtonText }}</text>
        <text class="detail__button-arrow">→</text>
      </button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
:global(page) {
  --xc-purple-soft: #ede5f9;
  --xc-pink-soft: #fde6ef;
  --xc-peach-soft: #fff0e8;
  --xc-mint-soft: #e2f5ef;
  --xc-gold-soft: #fdf4de;
}

.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding-bottom: 40rpx;
}

.page__ambient {
  position: fixed;
  inset: auto auto auto 0;
  border-radius: 50%;
  filter: blur(36px);
  opacity: 0.4;
  pointer-events: none;
}

.page__ambient--one {
  top: 120rpx;
  left: -80rpx;
  width: 240rpx;
  height: 240rpx;
  background: rgba(155, 126, 216, 0.22);
}

.page__ambient--two {
  top: 420rpx;
  right: -90rpx;
  width: 280rpx;
  height: 280rpx;
  background: rgba(232, 114, 154, 0.14);
}

.state-card {
  position: relative;
  margin: 28rpx;
  padding: 32rpx;
  border-radius: $xc-r-lg;
  @include glass;
  text-align: center;
}

.state-card--error {
  background: rgba(255, 240, 235, 0.92);
}

.state-card__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.detail {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.detail__ticker {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin: 18rpx 24rpx -4rpx;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, rgba(237, 229, 249, 0.96), rgba(253, 230, 239, 0.92));
  color: $xc-purple-d;
}

.detail__ticker-dot {
  width: 12rpx;
  height: 12rpx;
  flex-shrink: 0;
  border-radius: 50%;
  background: $xc-pink;
  box-shadow: 0 0 16rpx rgba(232, 114, 154, 0.5);
  animation: pulse 1.6s ease-in-out infinite;
}

.detail__ticker-swiper {
  flex: 1;
  height: 36rpx;
}

.detail__ticker-item {
  display: flex;
  align-items: center;
  height: 36rpx;
}

.detail__ticker-item text {
  font-size: 21rpx;
  white-space: nowrap;
}

.detail__hero {
  position: relative;
  overflow: hidden;
  padding: 88rpx 30rpx 46rpx;
  border-radius: 0 0 $xc-r-xl $xc-r-xl;
  text-align: center;
  color: $xc-white;
  box-shadow: $xc-sh-lg;
}

.detail__hero::before,
.detail__hero::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.detail__hero::before {
  inset: auto -70rpx -120rpx auto;
  width: 220rpx;
  height: 220rpx;
  background: rgba(255, 255, 255, 0.12);
}

.detail__hero::after {
  top: 10rpx;
  left: -50rpx;
  width: 180rpx;
  height: 180rpx;
  background: rgba(255, 255, 255, 0.08);
}

.detail__back {
  position: absolute;
  top: 24rpx;
  left: 18rpx;
  z-index: 2;
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: $xc-white;
  font-size: 38rpx;
  // #ifdef H5
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  // #endif
}

.detail__emoji,
.detail__title,
.detail__sub {
  position: relative;
  z-index: 1;
}

.detail__emoji {
  font-size: 88rpx;
  animation: heartbeat 2s ease-in-out infinite;
}

.detail__title {
  display: block;
  margin-top: 8rpx;
  font-family: $xc-font-serif;
  font-size: 42rpx;
  font-weight: 900;
  line-height: 1.35;
}

.detail__sub {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  opacity: 0.8;
}

.detail__stats {
  display: flex;
  justify-content: space-around;
  gap: 12rpx;
  margin: -18rpx 24rpx 0;
  padding: 24rpx 18rpx;
  border-radius: $xc-r;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: $xc-sh-md;
  position: relative;
  z-index: 2;
}

.detail__stat {
  flex: 1;
  min-width: 0;
  text-align: center;
}

.detail__stat-value {
  display: block;
  font-size: 30rpx;
  font-weight: 800;
  @include text-gradient;
}

.detail__stat-label {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-hint;
}

.detail__preview {
  position: relative;
  overflow: hidden;
  height: 196rpx;
  margin: 0 24rpx;
  border-radius: $xc-r;
  background: linear-gradient(135deg, $xc-purple-p, $xc-pink-p, $xc-peach-p);
}

.detail__preview-items {
  display: flex;
  gap: 16rpx;
  height: 100%;
  padding: 24rpx;
  align-items: center;
  filter: blur(5px);
  opacity: 0.7;
}

.detail__preview-items view {
  flex: 1;
  min-width: 0;
  height: 116rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16rpx;
  text-align: center;
  flex-direction: column;
  gap: 8rpx;
}

.detail__preview-items text {
  font-size: 24rpx;
  color: $xc-purple-d;
  font-weight: 700;
}

.detail__preview-emoji {
  font-size: 34rpx;
}

.detail__preview-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  background: rgba(255, 255, 255, 0.08);
  font-size: 24rpx;
  color: $xc-purple-d;
  font-weight: 700;
  // #ifdef H5
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  // #endif
}

.detail__reviews,
.detail__section {
  margin: 0 24rpx;
  padding: 24rpx;
  border-radius: $xc-r;
  @include glass;
  box-shadow: $xc-sh-md;
}

.detail__section-kicker,
.detail__section-title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  color: $xc-ink;
}

.detail__review {
  display: flex;
  gap: 10rpx;
  align-items: flex-start;
  margin-top: 14rpx;
}

.detail__review-avatar {
  width: 42rpx;
  height: 42rpx;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
}

.detail__review-text {
  flex: 1;
  min-width: 0;
  padding: 10rpx 14rpx;
  border-radius: 0 18rpx 18rpx 18rpx;
  background: rgba(245, 237, 230, 0.86);
  font-size: 24rpx;
  color: $xc-muted;
  line-height: 1.6;
}

.detail__friends {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin: 0 24rpx;
}

.detail__friends-avatars {
  display: flex;
}

.detail__friends-avatars text {
  width: 44rpx;
  height: 44rpx;
  margin-left: -10rpx;
  border-radius: 50%;
  border: 3rpx solid $xc-white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  background: rgba(255, 255, 255, 0.92);
}

.detail__friends-avatars text:first-child {
  margin-left: 0;
}

.detail__friends-text {
  font-size: 22rpx;
  color: $xc-hint;
  line-height: 1.5;
}

.detail__section-body {
  display: block;
  margin-top: 14rpx;
  font-size: 25rpx;
  color: $xc-muted;
  line-height: 1.78;
}

.detail__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 16rpx;
}

.detail__chip {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
  color: $xc-purple-d;
  border: 1px solid rgba(155, 126, 216, 0.08);
}

.detail__persona-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 16rpx;
}

.detail__persona {
  padding: 22rpx 20rpx;
  border-radius: 22rpx;
  background: linear-gradient(135deg, rgba(237, 229, 249, 0.48), rgba(253, 230, 239, 0.34));
  border: 1px solid rgba(155, 126, 216, 0.08);
}

.detail__persona-name {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.detail__persona-keywords {
  display: block;
  margin-top: 8rpx;
  font-size: 23rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.detail__bubble-wrap {
  margin: 0 24rpx;
}

.detail__button {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  margin: 4rpx 24rpx 0;
  height: 92rpx;
  border-radius: $xc-r;
  color: $xc-white;
  font-size: 30rpx;
  font-weight: 800;
  box-shadow: 0 10px 28px rgba(155, 126, 216, 0.26);
}

.detail__button::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.18), transparent);
  background-size: 200% 100%;
  animation: shimmer 2.6s infinite;
}

.detail__button--purple {
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
}

.detail__button--pink {
  background: linear-gradient(135deg, $xc-pink, $xc-peach);
}

.detail__button--mint {
  background: linear-gradient(135deg, $xc-mint, #5dafbf);
}

.detail__button--gold {
  background: linear-gradient(135deg, $xc-gold, $xc-peach);
}

.detail__button-arrow {
  position: relative;
  z-index: 1;
}

.anim-fu {
  animation: fadeInUp 0.48s $xc-ease both;
}

.anim-si {
  animation: scaleIn 0.44s $xc-ease both;
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

@keyframes heartbeat {
  0%,
  100% {
    transform: scale(1);
  }
  15% {
    transform: scale(1.13);
  }
  30% {
    transform: scale(1);
  }
  45% {
    transform: scale(1.07);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(18rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.94);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
