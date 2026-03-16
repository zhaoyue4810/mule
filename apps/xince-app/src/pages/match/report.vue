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

const syncIndex = computed(() => {
  const source = report.value?.dimension_comparison || [];
  if (!source.length) {
    return 0;
  }
  return Math.round(
    source.reduce((total, item) => total + item.similarity, 0) / source.length,
  );
});

const strongestGap = computed(() =>
  (report.value?.dimension_comparison || [])
    .slice()
    .sort((a, b) => b.difference - a.difference)[0] || null,
);

const topCards = computed(() => [
  {
    label: "同步维度",
    value: `${report.value?.similar_dimensions?.length || 0}`,
    hint: report.value?.similar_dimensions?.length ? "天然共振" : "继续探索",
  },
  {
    label: "互补维度",
    value: `${report.value?.complementary_dimensions?.length || 0}`,
    hint: report.value?.complementary_dimensions?.length ? "差异能量" : "趋于一致",
  },
  {
    label: "双人徽章",
    value: `${report.value?.unlocked_badges?.length || 0}`,
    hint: report.value?.unlocked_badges?.length ? "这次已点亮" : "继续匹配解锁",
  },
]);

const analysisCards = computed(() => {
  const similar =
    report.value?.similar_dimensions?.map((item) => item.toUpperCase()).join("、") || "节奏接近";
  const complementary =
    report.value?.complementary_dimensions?.map((item) => item.toUpperCase()).join("、") ||
    "互补自然";
  const conflict = strongestGap.value?.dim_code
    ? `${strongestGap.value.dim_code.toUpperCase()} 维度`
    : "表达节奏";
  return [
    {
      icon: "🧲",
      title: "天然同频点",
      body: `你们在 ${similar} 上最容易不费力地站到同一边，这会成为关系里的稳定基底。`,
    },
    {
      icon: "🧩",
      title: "互补能量",
      body: `在 ${complementary} 这些维度上，你们更像两种不同但能拼起来的力量。`,
    },
    {
      icon: "⚡",
      title: "潜在摩擦",
      body: `当话题落到 ${conflict} 时，最好先确认彼此感受，再给判断和建议。`,
    },
    {
      icon: "💡",
      title: "关系建议",
      body: "把最有共识的部分当成日常沟通入口，把差异大的维度留给更慢一点的深聊。 ",
    },
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
    displayScore.value = Math.min(
      safeTarget,
      displayScore.value + Math.max(1, Math.ceil((safeTarget - displayScore.value) / 8)),
    );
    if (displayScore.value >= safeTarget) {
      stopScoreTimer();
    }
  }, 28);
}

async function load() {
  if (!sessionId.value) {
    error.value = "缺少 sessionId 参数";
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

function shareReport() {
  const currentUrl =
    typeof window !== "undefined" && window.location ? window.location.href : "";
  const shareText = currentUrl || `/pages/match/report?sessionId=${sessionId.value}`;
  uni.setClipboardData({
    data: shareText,
  });
}

function goHome() {
  uni.switchTab({
    url: "/pages/home/index",
  });
}

function goMatchHub() {
  uni.switchTab({
    url: "/pages/match/index",
  });
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
      }, 900);
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
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--pink" />
    <view class="page__mesh" />

    <ConfettiCanvas :active="confettiActive" @done="confettiActive = false" />

    <view class="page__content">
      <view v-if="loading" class="surface-card panel">
        <text class="panel__eyebrow">MATCH REPORT</text>
        <text class="panel__title">正在展开你们的双人匹配报告</text>
        <text class="panel__text">维度对比、关系分析和双人徽章都会一起显影出来。</text>
      </view>

      <view v-else-if="error" class="surface-card panel panel--error">
        <text class="panel__eyebrow">UNAVAILABLE</text>
        <text class="panel__title">加载失败</text>
        <text class="panel__text">{{ error }}</text>
        <button class="panel__button" @tap="load">重新加载</button>
      </view>

      <view v-else-if="report" class="stack">
        <view class="hero">
          <view class="hero__orb hero__orb--violet" />
          <view class="hero__orb hero__orb--pink" />
          <view class="hero__topline">
            <text class="hero__eyebrow">SOUL PAIR REPORT</text>
            <text class="hero__badge">{{ report.tier }}</text>
          </view>

          <view class="hero__pair">
            <view class="hero__person">
              <view class="hero__avatar">{{ report.initiator.avatar_value }}</view>
              <text class="hero__name">{{ report.initiator.nickname }}</text>
            </view>
            <view class="hero__vs">❤</view>
            <view class="hero__person">
              <view class="hero__avatar hero__avatar--alt">{{ report.partner.avatar_value }}</view>
              <text class="hero__name">{{ report.partner.nickname }}</text>
            </view>
          </view>

          <view class="score-ring" :class="scoreTone">
            <view
              class="score-ring__outer"
              :style="{ background: `conic-gradient(#ffffff ${scoreSweep * 3.6}deg, rgba(255,255,255,0.16) 0)` }"
            >
              <view class="score-ring__inner">
                <text class="score-ring__value">{{ displayScore }}</text>
                <text class="score-ring__unit">%</text>
              </view>
            </view>
          </view>

          <text class="hero__title">{{ report.test_name }}</text>
          <text class="hero__body">{{ report.analysis }}</text>

          <view class="hero__stats">
            <view v-for="item in topCards" :key="item.label" class="hero-stat">
              <text class="hero-stat__value">{{ item.value }}</text>
              <text class="hero-stat__label">{{ item.label }}</text>
              <text class="hero-stat__hint">{{ item.hint }}</text>
            </view>
          </view>
        </view>

        <view class="surface-card radar-panel">
          <view class="section-head">
            <view>
              <text class="section-head__title">维度共振图</text>
              <text class="section-head__desc">同步指数 {{ syncIndex }}，越接近 100 越说明你们在更多维度上步调一致。</text>
            </view>
          </view>

          <MatchRadarCanvas :dimensions="report.dimension_comparison" />

          <view class="tag-row">
            <text
              v-for="item in report.similar_dimensions"
              :key="`similar-${item}`"
              class="tag-pill tag-pill--violet"
            >
              同频 {{ formatDimensionLabel(item) }}
            </text>
            <text
              v-for="item in report.complementary_dimensions"
              :key="`complementary-${item}`"
              class="tag-pill tag-pill--pink"
            >
              互补 {{ formatDimensionLabel(item) }}
            </text>
          </view>
        </view>

        <view class="surface-card compare-panel">
          <view class="section-head">
            <view>
              <text class="section-head__title">逐项维度对比</text>
              <text class="section-head__desc">
                {{ strongestGap ? `当前差异最大的是 ${formatDimensionLabel(strongestGap.dim_code)}，分差 ${Math.round(strongestGap.difference)}` : "所有维度都已纳入对比。" }}
              </text>
            </view>
          </view>

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
              <view class="compare-dual__person">
                <text class="compare-dual__person-name">{{ report.initiator.nickname }}</text>
                <view class="compare-dual__bar">
                  <view
                    class="compare-dual__fill compare-dual__fill--a"
                    :style="{ width: `${item.initiator_score}%`, transitionDelay: `${index * 60}ms` }"
                  />
                </view>
                <text class="compare-dual__value">{{ Math.round(item.initiator_score) }}</text>
              </view>
              <view class="compare-dual__person">
                <text class="compare-dual__person-name">{{ report.partner.nickname }}</text>
                <view class="compare-dual__bar">
                  <view
                    class="compare-dual__fill compare-dual__fill--b"
                    :style="{ width: `${item.partner_score}%`, transitionDelay: `${index * 60}ms` }"
                  />
                </view>
                <text class="compare-dual__value">{{ Math.round(item.partner_score) }}</text>
              </view>
            </view>
          </view>
        </view>

        <view class="analysis-grid">
          <view v-for="item in analysisCards" :key="item.title" class="surface-card analysis-card">
            <text class="analysis-card__icon">{{ item.icon }}</text>
            <text class="analysis-card__title">{{ item.title }}</text>
            <text class="analysis-card__body">{{ item.body }}</text>
          </view>
        </view>

        <view class="surface-card badge-panel" v-if="report.unlocked_badges.length">
          <view class="section-head">
            <view>
              <text class="section-head__title">这次点亮的双人徽章</text>
              <text class="section-head__desc">你们刚刚把一次关系共振，沉淀成了可收藏的双人成就。</text>
            </view>
          </view>
          <view class="badge-grid">
            <view
              v-for="badge in report.unlocked_badges"
              :key="badge.badge_key"
              class="badge-card"
            >
              <view class="badge-card__halo" />
              <text class="badge-card__emoji">{{ badge.emoji }}</text>
              <text class="badge-card__name">{{ badge.name }}</text>
            </view>
          </view>
        </view>

        <view class="action-row">
          <button class="panel__button panel__button--ghost" @tap="shareReport">复制报告链接</button>
          <button class="panel__button panel__button--ghost" @tap="goMatchHub">返回匹配站</button>
          <button class="panel__button" @tap="goHome">回到首页</button>
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
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28rpx 24rpx calc(46rpx + env(safe-area-inset-bottom, 0rpx));
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.94), rgba(248, 241, 255, 0.8) 48%, #fffaf7 100%);
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
  width: 440rpx;
  height: 440rpx;
  border-radius: 50%;
  filter: blur(34px);
  opacity: 0.42;
}

.page__glow--violet {
  top: -120rpx;
  right: -120rpx;
  background: rgba(155, 126, 216, 0.24);
}

.page__glow--pink {
  bottom: 160rpx;
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
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.28), transparent 36%),
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
  top: -26rpx;
  left: -18rpx;
  width: 170rpx;
  height: 170rpx;
  background: rgba(255, 255, 255, 0.42);
}

.hero__orb--pink {
  right: -34rpx;
  bottom: 72rpx;
  width: 180rpx;
  height: 180rpx;
  background: rgba(255, 220, 232, 0.4);
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

.hero__pair {
  position: relative;
  z-index: 1;
  margin-top: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
}

.hero__person {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.hero__avatar {
  width: 110rpx;
  height: 110rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 50rpx;
  color: #47335f;
  background: rgba(255, 255, 255, 0.9);
  border: 4rpx solid rgba(255, 255, 255, 0.72);
}

.hero__avatar--alt {
  background: rgba(255, 243, 247, 0.86);
}

.hero__name {
  font-size: 21rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero__vs {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
}

.score-ring {
  position: relative;
  z-index: 1;
  margin-top: 24rpx;
  display: flex;
  justify-content: center;
}

.score-ring__outer {
  width: 220rpx;
  height: 220rpx;
  border-radius: 50%;
  padding: 10rpx;
}

.score-ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  color: $xc-purple-d;
}

.score-ring__value {
  font-size: 68rpx;
  font-weight: 800;
}

.score-ring__unit {
  margin-left: 6rpx;
  font-size: 28rpx;
  color: $xc-muted;
}

.score-ring--diamond .score-ring__outer {
  box-shadow: 0 0 24rpx rgba(247, 219, 121, 0.42);
}

.score-ring--glow .score-ring__outer {
  box-shadow: 0 0 24rpx rgba(255, 255, 255, 0.24);
}

.score-ring--warm .score-ring__outer {
  box-shadow: 0 0 20rpx rgba(255, 213, 189, 0.36);
}

.hero__title {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 20rpx;
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

.hero__stats {
  position: relative;
  z-index: 1;
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.hero-stat {
  padding: 18rpx 12rpx 16rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.14);
  text-align: center;
}

.hero-stat__value {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.hero-stat__label {
  display: block;
  margin-top: 4rpx;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.8);
}

.hero-stat__hint {
  display: block;
  margin-top: 6rpx;
  font-size: 18rpx;
  color: rgba(255, 255, 255, 0.66);
}

.radar-panel,
.compare-panel,
.badge-panel {
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

.tag-row {
  margin-top: 12rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.tag-pill {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
}

.tag-pill--violet {
  background: rgba(124, 93, 191, 0.08);
  color: $xc-purple-d;
}

.tag-pill--pink {
  background: rgba(232, 114, 154, 0.1);
  color: #b24b70;
}

.compare-card {
  margin-top: 14rpx;
  padding: 18rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.84);
}

.compare-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.compare-card__name {
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.compare-card__tag {
  font-size: 20rpx;
  color: $xc-purple-d;
}

.compare-dual {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.compare-dual__person {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.compare-dual__person-name {
  font-size: 20rpx;
  color: $xc-muted;
}

.compare-dual__bar {
  height: 14rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(155, 126, 216, 0.1);
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
  color: $xc-hint;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.analysis-card {
  padding: 20rpx;
}

.analysis-card__icon {
  display: block;
  font-size: 30rpx;
}

.analysis-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 25rpx;
  font-weight: 700;
  color: $xc-ink;
}

.analysis-card__body {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.badge-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.badge-card {
  position: relative;
  overflow: hidden;
  min-height: 160rpx;
  padding: 20rpx 12rpx 16rpx;
  border-radius: 24rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.62), transparent 34%),
    linear-gradient(145deg, rgba(124, 93, 191, 0.12), rgba(232, 114, 154, 0.1)),
    rgba(255, 255, 255, 0.84);
  text-align: center;
}

.badge-card__halo {
  position: absolute;
  top: -30rpx;
  left: 50%;
  width: 120rpx;
  height: 120rpx;
  margin-left: -60rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(232, 114, 154, 0.22), transparent 72%);
}

.badge-card__emoji {
  position: relative;
  display: block;
  font-size: 38rpx;
}

.badge-card__name {
  position: relative;
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.5;
  color: $xc-ink;
  font-weight: 600;
}

.action-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
}
</style>
