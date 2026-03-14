<script setup lang="ts">
import type { AppProfileOverview } from "@/shared/models/profile";

defineProps<{
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
</script>

<template>
  <view>
    <view class="hero">
      <view class="hero__top">
        <view class="hero__avatar-wrap">
          <text class="hero__avatar">{{ overview.avatar_value }}</text>
        </view>
        <view class="hero__info">
          <text class="hero__title">{{ overview.nickname }}</text>
          <text class="hero__signature">{{ greetingText }}</text>
          <view class="hero__actions">
            <button class="hero__tag-btn" @tap="emit('go-persona-card')">人设名片</button>
            <button class="hero__icon-btn" @tap="emit('go-settings')">✎</button>
          </view>
        </view>
      </view>
    </view>

    <view class="stats">
      <view class="stat-card stat-card--highlight">
        <text class="stat-card__value">{{ statDisplay.testCount }}</text>
        <text class="stat-card__label">已完成测试</text>
      </view>
      <view class="stat-card stat-card--highlight">
        <text class="stat-card__value">{{ statDisplay.matchCount }}</text>
        <text class="stat-card__label">匹配报告</text>
      </view>
      <view class="stat-card stat-card--highlight">
        <text class="stat-card__value">{{ statDisplay.pendingCount }}</text>
        <text class="stat-card__label">待解锁</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.hero {
  border-radius: 28rpx;
  padding: 34rpx 28rpx;
  @include gradient-hero;
  box-shadow: $xc-sh-lg;
}

.hero__top {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20rpx;
  align-items: center;
}

.hero__avatar-wrap {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(255, 255, 255, 0.88);
  box-shadow: 0 0 0 8rpx rgba(155, 126, 216, 0.16);
  background: rgba(255, 255, 255, 0.26);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero__avatar {
  font-size: 56rpx;
}

.hero__info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.hero__title {
  font-size: 42rpx;
  color: #fff;
  font-family: $xc-font-serif;
  font-weight: 700;
}

.hero__signature {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.9);
}

.hero__actions {
  margin-top: 8rpx;
  display: flex;
  gap: 10rpx;
}

.hero__tag-btn,
.hero__icon-btn {
  border: none;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 22rpx;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.hero__tag-btn {
  padding: 12rpx 16rpx;
  border-radius: 999rpx;
}

.hero__icon-btn {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
}

.stats {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.stat-card {
  border-radius: 22rpx;
  padding: 22rpx 16rpx;
  @include glass;
  align-items: center;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.stat-card--highlight .stat-card__value {
  color: $xc-purple-d;
}

.stat-card__value {
  font-size: 34rpx;
  font-weight: 700;
}

.stat-card__label {
  font-size: 22rpx;
  color: $xc-muted;
}
</style>
