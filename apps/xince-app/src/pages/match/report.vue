<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import MatchRadarCanvas from "@/components/match/MatchRadarCanvas.vue";
import type { MatchResultPayload } from "@/shared/models/match";
import { ensureAppSession } from "@/shared/services/auth";
import { fetchMatchResult } from "@/shared/services/match";

const sessionId = ref(0);
const loading = ref(false);
const error = ref("");
const report = ref<MatchResultPayload | null>(null);

const scoreTone = computed(() => {
  const score = report.value?.compatibility_score || 0;
  if (score >= 95) {
    return "score--diamond";
  }
  if (score >= 85) {
    return "score--glow";
  }
  return "score--warm";
});

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
</script>

<template>
  <view class="page">
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
        <text class="hero__eyebrow">Match Report</text>
        <text class="hero__pair">{{ report.initiator.nickname }} × {{ report.partner.nickname }}</text>
        <view class="score" :class="scoreTone">
          <text class="score__value">{{ report.compatibility_score }}</text>
          <text class="score__unit">/100</text>
        </view>
        <text class="hero__tier">{{ report.tier }}</text>
        <text class="hero__body">{{ report.analysis }}</text>
      </view>

      <MatchRadarCanvas :dimensions="report.dimension_comparison" />

      <view class="panel">
        <text class="panel__title">相似共振</text>
        <view class="chip-row">
          <text
            v-for="item in report.similar_dimensions"
            :key="item"
            class="chip chip--warm"
          >
            {{ formatDimensionLabel(item) }}
          </text>
        </view>
        <text class="panel__title panel__title--next">互补拉力</text>
        <view class="chip-row">
          <text
            v-for="item in report.complementary_dimensions"
            :key="item"
            class="chip chip--cool"
          >
            {{ formatDimensionLabel(item) }}
          </text>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">维度对比</text>
        <view
          v-for="item in report.dimension_comparison"
          :key="item.dim_code"
          class="compare-card"
        >
          <view class="compare-card__top">
            <text class="compare-card__name">{{ formatDimensionLabel(item.dim_code) }}</text>
            <text class="compare-card__tag">{{ item.relation }}</text>
          </view>
          <view class="compare-bar">
            <view class="compare-bar__track">
              <view class="compare-bar__fill compare-bar__fill--warm" :style="{ width: `${item.initiator_score}%` }" />
            </view>
            <text class="compare-bar__value">{{ Math.round(item.initiator_score) }}</text>
          </view>
          <view class="compare-bar">
            <view class="compare-bar__track">
              <view class="compare-bar__fill compare-bar__fill--cool" :style="{ width: `${item.partner_score}%` }" />
            </view>
            <text class="compare-bar__value">{{ Math.round(item.partner_score) }}</text>
          </view>
        </view>
      </view>

      <view class="panel" v-if="report.unlocked_badges.length">
        <text class="panel__title">双人勋章</text>
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
  border-radius: 28rpx;
  background: rgba(255, 252, 247, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
  box-shadow: $xc-shadow;
}

.panel--error {
  background: rgba(255, 240, 235, 0.96);
}

.hero__eyebrow,
.hero__body,
.panel__text {
  color: $xc-muted;
}

.hero__eyebrow {
  display: block;
  font-size: 22rpx;
  letter-spacing: 3rpx;
  text-transform: uppercase;
}

.hero__pair,
.panel__title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
}

.hero__pair {
  margin-top: 14rpx;
}

.score {
  margin-top: 18rpx;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 10rpx;
}

.score__value {
  font-size: 112rpx;
  line-height: 1;
  font-weight: 700;
}

.score__unit {
  font-size: 28rpx;
  margin-bottom: 14rpx;
}

.score--diamond {
  color: #bf7a1b;
}

.score--glow {
  color: #d96f3d;
}

.score--warm {
  color: #b8664e;
}

.hero__tier {
  display: block;
  margin-top: 10rpx;
  text-align: center;
  font-size: 28rpx;
  color: #d96f3d;
  font-weight: 700;
}

.hero__body,
.panel__text {
  display: block;
  margin-top: 14rpx;
  font-size: 25rpx;
  line-height: 1.7;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 14rpx;
}

.chip {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
}

.chip--warm {
  background: rgba(217, 111, 61, 0.12);
  color: #d96f3d;
}

.chip--cool {
  background: rgba(107, 145, 217, 0.12);
  color: #6b91d9;
}

.panel__title--next {
  margin-top: 20rpx;
}

.compare-card {
  margin-top: 18rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.66);
}

.compare-card__top {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

.compare-card__name {
  font-size: 24rpx;
  font-weight: 700;
}

.compare-card__tag {
  font-size: 22rpx;
  color: $xc-muted;
}

.compare-bar {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 10rpx;
}

.compare-bar__track {
  flex: 1;
  height: 16rpx;
  border-radius: 999rpx;
  background: rgba(60, 40, 24, 0.08);
  overflow: hidden;
}

.compare-bar__fill {
  height: 100%;
  border-radius: 999rpx;
}

.compare-bar__fill--warm {
  background: linear-gradient(135deg, #e38b59, #d96f3d);
}

.compare-bar__fill--cool {
  background: linear-gradient(135deg, #7ba2e9, #6b91d9);
}

.compare-bar__value {
  width: 50rpx;
  text-align: right;
  font-size: 22rpx;
  color: $xc-muted;
}

.badge-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 18rpx;
}

.badge-card {
  padding: 22rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.72);
  text-align: center;
}

.badge-card__emoji {
  display: block;
  font-size: 42rpx;
}

.badge-card__name {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  font-weight: 600;
}
</style>
