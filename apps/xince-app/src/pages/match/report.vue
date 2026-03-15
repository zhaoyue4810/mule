<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import CelebrationOverlay from "@/components/feedback/CelebrationOverlay.vue";
import ConfettiCanvas from "@/components/feedback/ConfettiCanvas.vue";
import MatchRadarCanvas from "@/components/match/MatchRadarCanvas.vue";
import type { MatchResultPayload } from "@/shared/models/match";
import { ensureAppSession } from "@/shared/services/auth";
import { fetchMatchResult } from "@/shared/services/match";
import { SoundManager } from "@/shared/utils/sound-manager";

const sessionId = ref(0);
const loading = ref(false);
const error = ref("");
const report = ref<MatchResultPayload | null>(null);
const displayScore = ref(0);
const celebrationVisible = ref(false);
const confettiActive = ref(false);
const pageChimed = ref(false);
let scoreTimer: ReturnType<typeof setInterval> | null = null;
let confettiTimer: ReturnType<typeof setTimeout> | null = null;

const scoreTone = computed(() => {
  const score = report.value?.compatibility_score || 0;
  if (score >= 92) {
    return "score-ring--diamond";
  }
  if (score >= 80) {
    return "score-ring--glow";
  }
  return "score-ring--warm";
});

const scoreSweep = computed(() => Math.max(0, Math.min(100, displayScore.value)));

const analysisCards = computed(() => {
  const similar = report.value?.similar_dimensions?.map((item) => item.toUpperCase()).join("、") || "节奏接近";
  const complementary =
    report.value?.complementary_dimensions?.map((item) => item.toUpperCase()).join("、") || "互补自然";
  const firstDiff = report.value?.dimension_comparison
    ?.slice()
    .sort((a, b) => b.difference - a.difference)?.[0];
  const conflict = firstDiff?.dim_code ? `${firstDiff.dim_code.toUpperCase()} 维度` : "表达节奏";
  return [
    { icon: "🧲", title: "相似之处", body: `你们在 ${similar} 上天然同频。` },
    { icon: "🧩", title: "互补特质", body: `在 ${complementary} 上形成稳定互补。` },
    { icon: "⚡", title: "摩擦点", body: `注意 ${conflict} 的分歧，先描述感受再给建议。` },
    { icon: "💡", title: "关系建议", body: "固定一次高质量对话，把误解转成共同目标。" },
  ];
});

function stopScoreTimer() {
  if (scoreTimer) {
    clearInterval(scoreTimer);
    scoreTimer = null;
  }
}

function stopConfettiTimer() {
  if (confettiTimer) {
    clearTimeout(confettiTimer);
    confettiTimer = null;
  }
}

function animateScore(target: number) {
  stopScoreTimer();
  displayScore.value = 0;
  const safeTarget = Math.max(0, Math.min(100, Math.round(target)));
  scoreTimer = setInterval(() => {
    displayScore.value = Math.min(safeTarget, displayScore.value + Math.max(1, Math.ceil((safeTarget - displayScore.value) / 8)));
    if (displayScore.value >= safeTarget) {
      stopScoreTimer();
    }
  }, 28);
}

async function load() {
  if (!sessionId.value) {
    return;
  }
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    report.value = await fetchMatchResult(sessionId.value);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "匹配报告加载失败";
  } finally {
    loading.value = false;
  }
}

function formatDimensionLabel(item: string) {
  return item.toUpperCase();
}

onLoad((query) => {
  sessionId.value = Number(query?.sessionId || 0);
});

onMounted(load);

watch(
  () => report.value,
  (value) => {
    stopConfettiTimer();
    confettiActive.value = false;
    if (!value) {
      return;
    }
    if (!pageChimed.value && !value.unlocked_badges?.length && SoundManager.isSoundEnabled()) {
      SoundManager.play("chime");
      pageChimed.value = true;
    }
    animateScore(value.compatibility_score || 0);
    if ((value.compatibility_score || 0) >= 85) {
      confettiTimer = setTimeout(() => {
        confettiActive.value = true;
      }, 1000);
    }
    if (value.unlocked_badges?.length) {
      celebrationVisible.value = true;
    }
  },
  { immediate: false },
);

onBeforeUnmount(() => {
  stopScoreTimer();
  stopConfettiTimer();
});
</script>

<template>
  <view class="page">
    <ConfettiCanvas :active="confettiActive" @done="confettiActive = false" />
    <view v-if="loading" class="panel">
      <text class="panel__text">正在展开你们的双人匹配报告...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__title">加载失败</text>
      <text class="panel__text">{{ error }}</text>
      <button class="panel__button" @tap="load">重新加载</button>
    </view>

    <view v-else-if="report" class="stack">
      <view class="hero">
        <view class="hero__pair">
          <view class="hero__avatar">{{ report.initiator.avatar_value }}</view>
          <text class="hero__vs">VS</text>
          <view class="hero__avatar hero__avatar--alt">{{ report.partner.avatar_value }}</view>
        </view>
        <view class="score-ring" :class="scoreTone">
          <view class="score-ring__outer" :style="{ background: `conic-gradient(#9B7ED8 ${scoreSweep * 3.6}deg, rgba(255,255,255,0.2) 0)` }">
            <view class="score-ring__inner">
              <text class="score-ring__value">{{ displayScore }}</text>
              <text class="score-ring__unit">%</text>
            </view>
          </view>
        </view>
        <text class="hero__tier">{{ report.tier }}</text>
        <text class="hero__body">{{ report.analysis }}</text>
      </view>

      <MatchRadarCanvas :dimensions="report.dimension_comparison" />

      <view class="panel">
        <text class="panel__title">维度对比</text>
        <view
          v-for="(item, index) in report.dimension_comparison"
          :key="item.dim_code"
          class="compare-card"
        >
          <view class="compare-card__top">
            <text class="compare-card__name">{{ formatDimensionLabel(item.dim_code) }}</text>
            <text class="compare-card__tag">{{ item.relation }}</text>
          </view>
          <view class="compare-dual">
            <view class="compare-dual__bar">
              <view class="compare-dual__fill compare-dual__fill--a" :style="{ width: `${item.initiator_score}%`, transitionDelay: `${index * 60}ms` }" />
            </view>
            <text class="compare-dual__value">{{ Math.round(item.initiator_score) }}</text>
            <view class="compare-dual__bar">
              <view class="compare-dual__fill compare-dual__fill--b" :style="{ width: `${item.partner_score}%`, transitionDelay: `${index * 60}ms` }" />
            </view>
            <text class="compare-dual__value">{{ Math.round(item.partner_score) }}</text>
          </view>
        </view>
      </view>

      <view class="analysis-grid">
        <view v-for="item in analysisCards" :key="item.title" class="analysis-card">
          <text class="analysis-card__icon">{{ item.icon }}</text>
          <text class="analysis-card__title">{{ item.title }}</text>
          <text class="analysis-card__body">{{ item.body }}</text>
        </view>
      </view>

      <view class="panel" v-if="report.unlocked_badges.length">
        <text class="panel__title">双人徽章解锁</text>
        <view class="badge-grid">
          <view
            v-for="badge in report.unlocked_badges"
            :key="badge.badge_key"
            class="badge-card"
          >
            <text class="badge-card__emoji">{{ badge.emoji }}</text>
            <text class="badge-card__name">{{ badge.name }}</text>
          </view>
        </view>
      </view>
    </view>

    <CelebrationOverlay
      :visible="celebrationVisible"
      title="双人徽章已解锁"
      message="你们的这次共振，点亮了新的关系印记。"
      :badges="report?.unlocked_badges || []"
      @close="celebrationVisible = false"
    />
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

.hero,
.panel,
.analysis-card {
  @include card-base;
}

.hero,
.panel {
  padding: 24rpx;
}

.hero {
  background:
    linear-gradient(145deg, rgba(155, 126, 216, 0.24), rgba(232, 114, 154, 0.18)),
    rgba(255, 255, 255, 0.9);
}

.hero__pair {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
}

.hero__avatar {
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.86);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}

.hero__avatar--alt {
  background: rgba(253, 230, 239, 0.86);
}

.hero__vs {
  font-size: 24rpx;
  font-weight: 700;
  color: $xc-purple;
}

.score-ring {
  margin-top: 16rpx;
  display: flex;
  justify-content: center;
}

.score-ring__outer {
  width: 210rpx;
  height: 210rpx;
  border-radius: 50%;
  padding: 10rpx;
}

.score-ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: row;
  background: rgba(255, 255, 255, 0.92);
}

.score-ring__value {
  font-size: 62rpx;
  font-weight: 700;
}

.score-ring__unit {
  margin-left: 4rpx;
  font-size: 26rpx;
  color: $xc-muted;
}

.score-ring--diamond .score-ring__outer {
  box-shadow: 0 0 22rpx rgba(212, 168, 83, 0.46);
}

.score-ring--glow .score-ring__outer {
  box-shadow: 0 0 20rpx rgba(155, 126, 216, 0.46);
}

.hero__tier {
  display: block;
  margin-top: 12rpx;
  text-align: center;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-purple;
}

.hero__body,
.panel__text {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
}

.compare-card {
  margin-top: 12rpx;
  padding: 14rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.86);
}

.compare-card__top {
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
}

.compare-card__name {
  font-size: 24rpx;
  font-weight: 600;
}

.compare-card__tag {
  font-size: 21rpx;
  color: $xc-muted;
}

.compare-dual {
  margin-top: 10rpx;
  display: grid;
  grid-template-columns: 1fr auto 1fr auto;
  gap: 8rpx;
  align-items: center;
}

.compare-dual__bar {
  height: 14rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  overflow: hidden;
}

.compare-dual__fill {
  height: 100%;
  transition: width 0.55s $xc-ease;
}

.compare-dual__fill--a {
  background: linear-gradient(90deg, #9b7ed8, #c9b5f0);
}

.compare-dual__fill--b {
  background: linear-gradient(90deg, #e8729a, #f4a5bf);
}

.compare-dual__value {
  font-size: 20rpx;
  color: $xc-muted;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10rpx;
}

.analysis-card {
  padding: 16rpx;
}

.analysis-card__icon {
  display: block;
  font-size: 28rpx;
}

.analysis-card__title {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  font-weight: 700;
}

.analysis-card__body {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.badge-grid {
  margin-top: 12rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
}

.badge-card {
  border-radius: 16rpx;
  padding: 14rpx 10rpx;
  text-align: center;
  background: rgba(253, 230, 239, 0.62);
}

.badge-card__emoji {
  display: block;
  font-size: 34rpx;
}

.badge-card__name {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  font-weight: 600;
}
</style>
