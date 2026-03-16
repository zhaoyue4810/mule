<script setup lang="ts">
import { computed } from "vue";

import type { AppProfileOverview } from "@/shared/models/profile";

const props = defineProps<{
  overview: AppProfileOverview;
  greetingText: string;
  statDisplay: {
    testCount: number;
    matchCount: number;
    pendingCount: number;
  };
}>();

const emit = defineEmits<{
  (event: "go-persona-card"): void;
  (event: "go-settings"): void;
}>();

const explorerTitle = computed(
  () => props.overview.persona_distribution[0]?.persona_name || "灵魂探索者",
);

const explorerStage = computed(() => {
  const count = props.overview.test_count;
  if (count >= 12) {
    return "高阶观察者";
  }
  if (count >= 7) {
    return "持续深入中";
  }
  if (count >= 3) {
    return "画像逐渐成形";
  }
  return "旅程刚刚开始";
});

const dominantTags = computed(() =>
  props.overview.dominant_dimensions
    .slice(0, 3)
    .map((item) => item.dim_code.toUpperCase()),
);

const completionPercent = computed(() =>
  Math.max(
    18,
    Math.min(
      96,
      props.overview.test_count * 8 + props.overview.distinct_test_count * 7 + 12,
    ),
  ),
);

const headerPanels = computed(() => [
  {
    label: "最近活跃",
    value: props.overview.last_test_at ? formatTime(props.overview.last_test_at) : "刚刚启程",
  },
  {
    label: "探索广度",
    value: `${props.overview.distinct_test_count} 类测试`,
  },
  {
    label: "平均时长",
    value: formatDuration(props.overview.avg_duration_seconds),
  },
]);

function formatTime(value?: string | null) {
  if (!value) {
    return "暂未记录";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getMonth() + 1}/${date.getDate()} ${`${date.getHours()}`.padStart(2, "0")}:${`${date.getMinutes()}`.padStart(2, "0")}`;
}

function formatDuration(value: number) {
  if (!value) {
    return "待累计";
  }
  const minutes = Math.max(1, Math.round(value / 60));
  return `${minutes} 分钟`;
}
</script>

<template>
  <view>
    <view class="hero">
      <view class="hero__orb hero__orb--violet" />
      <view class="hero__orb hero__orb--pink" />

      <view class="hero__topline">
        <text class="hero__eyebrow">SOUL DOSSIER</text>
        <button class="hero__settings" @tap="emit('go-settings')">⚙</button>
      </view>

      <view class="hero__main">
        <view class="hero__avatar-panel">
          <view class="hero__avatar-ring">
            <view class="hero__avatar-wrap">
              <text class="hero__avatar">{{ overview.avatar_value }}</text>
            </view>
          </view>
          <text class="hero__stage">{{ explorerStage }}</text>
        </view>

        <view class="hero__copy">
          <text class="hero__title">{{ overview.nickname }}</text>
          <text class="hero__persona">{{ explorerTitle }}</text>
          <text class="hero__signature">{{ greetingText }}</text>

          <view class="hero__tags">
            <text v-for="item in dominantTags" :key="item" class="hero__tag">{{ item }}</text>
            <text v-if="!dominantTags.length" class="hero__tag">NEW SOUL</text>
          </view>

          <view class="hero__actions">
            <button class="hero__action hero__action--primary" @tap="emit('go-persona-card')">
              人设名片
            </button>
            <button class="hero__action hero__action--ghost" @tap="emit('go-settings')">
              资料设置
            </button>
          </view>
        </view>
      </view>

      <view class="hero__progress-card">
        <view class="hero__progress-top">
          <text class="hero__progress-label">灵魂完整度</text>
          <text class="hero__progress-value">{{ completionPercent }}%</text>
        </view>
        <view class="hero__progress-track">
          <view class="hero__progress-fill" :style="{ width: `${completionPercent}%` }" />
        </view>
        <view class="hero__mini-grid">
          <view v-for="item in headerPanels" :key="item.label" class="hero__mini-card">
            <text class="hero__mini-label">{{ item.label }}</text>
            <text class="hero__mini-value">{{ item.value }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="stats">
      <view class="stat-card stat-card--violet">
        <text class="stat-card__value">{{ statDisplay.testCount }}</text>
        <text class="stat-card__label">已完成测试</text>
        <text class="stat-card__hint">沉淀出的正式报告</text>
      </view>
      <view class="stat-card stat-card--pink">
        <text class="stat-card__value">{{ statDisplay.matchCount }}</text>
        <text class="stat-card__label">匹配报告</text>
        <text class="stat-card__hint">双人关系档案</text>
      </view>
      <view class="stat-card stat-card--gold">
        <text class="stat-card__value">{{ statDisplay.pendingCount }}</text>
        <text class="stat-card__label">待解锁碎片</text>
        <text class="stat-card__hint">下一层自我画像</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.hero {
  position: relative;
  overflow: hidden;
  padding: 30rpx 28rpx 28rpx;
  border-radius: 40rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.28), transparent 38%),
    linear-gradient(145deg, #7357be 0%, #9b7ed8 34%, #f093b7 100%);
  box-shadow: 0 28rpx 72rpx rgba(124, 93, 191, 0.24);
  color: #fff;
}

.hero__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(14px);
  opacity: 0.28;
}

.hero__orb--violet {
  top: -32rpx;
  left: -24rpx;
  width: 180rpx;
  height: 180rpx;
  background: rgba(255, 255, 255, 0.4);
}

.hero__orb--pink {
  right: -38rpx;
  bottom: 36rpx;
  width: 200rpx;
  height: 200rpx;
  background: rgba(255, 220, 230, 0.34);
}

.hero__topline {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hero__eyebrow {
  font-size: 20rpx;
  letter-spacing: 4rpx;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.78);
}

.hero__settings {
  width: 64rpx;
  height: 64rpx;
  padding: 0;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 26rpx;
  line-height: 64rpx;
}

.hero__main {
  position: relative;
  z-index: 1;
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20rpx;
  align-items: center;
}

.hero__avatar-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.hero__avatar-ring {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 148rpx;
  height: 148rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  border: 2rpx solid rgba(255, 255, 255, 0.24);
  box-shadow: 0 0 0 10rpx rgba(255, 255, 255, 0.08);
}

.hero__avatar-wrap {
  width: 122rpx;
  height: 122rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.86);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid rgba(255, 255, 255, 0.72);
}

.hero__avatar {
  font-size: 58rpx;
}

.hero__stage {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.88);
}

.hero__copy {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.hero__title {
  font-size: 44rpx;
  line-height: 1.1;
  font-family: $xc-font-serif;
  font-weight: 700;
}

.hero__persona {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.88);
}

.hero__signature {
  font-size: 23rpx;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.92);
}

.hero__tags {
  margin-top: 4rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.hero__tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 19rpx;
  color: rgba(255, 255, 255, 0.88);
}

.hero__actions {
  margin-top: 10rpx;
  display: flex;
  gap: 12rpx;
}

.hero__action {
  height: 68rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  border: none;
}

.hero__action--primary {
  background: rgba(255, 255, 255, 0.92);
  color: $xc-purple-d;
  font-weight: 700;
}

.hero__action--ghost {
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
}

.hero__progress-card {
  position: relative;
  z-index: 1;
  margin-top: 22rpx;
  padding: 20rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.14);
}

.hero__progress-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.hero__progress-label,
.hero__progress-value {
  font-size: 23rpx;
}

.hero__progress-value {
  font-weight: 700;
}

.hero__progress-track {
  margin-top: 12rpx;
  height: 12rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.16);
}

.hero__progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.96), rgba(255, 230, 238, 0.96));
  box-shadow: 0 0 20rpx rgba(255, 255, 255, 0.2);
}

.hero__mini-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.hero__mini-card {
  min-height: 96rpx;
  padding: 14rpx 12rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.1);
}

.hero__mini-label {
  display: block;
  font-size: 18rpx;
  color: rgba(255, 255, 255, 0.68);
}

.hero__mini-value {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  line-height: 1.5;
  color: #fff;
  font-weight: 600;
}

.stats {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.stat-card {
  position: relative;
  overflow: hidden;
  border-radius: 24rpx;
  padding: 22rpx 16rpx 18rpx;
  border: 1px solid rgba(155, 126, 216, 0.12);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 18rpx 40rpx rgba(155, 126, 216, 0.1);

  // #ifdef H5
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  // #endif
}

.stat-card::before {
  content: "";
  position: absolute;
  top: -36rpx;
  right: -24rpx;
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  opacity: 0.14;
}

.stat-card--violet::before {
  background: rgba(124, 93, 191, 0.9);
}

.stat-card--pink::before {
  background: rgba(232, 114, 154, 0.94);
}

.stat-card--gold::before {
  background: rgba(234, 185, 90, 0.92);
}

.stat-card__value {
  position: relative;
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  color: $xc-ink;
}

.stat-card__label {
  position: relative;
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  color: $xc-ink;
  font-weight: 600;
}

.stat-card__hint {
  position: relative;
  display: block;
  margin-top: 8rpx;
  font-size: 19rpx;
  line-height: 1.5;
  color: $xc-muted;
}
</style>
