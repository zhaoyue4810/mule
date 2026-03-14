<script setup lang="ts">
defineProps<{
  heroStyle: Record<string, string>;
  testName: string;
  personaEmoji: string;
  personaName: string;
  tierText: string;
  totalScore: number;
  scoreProgress: number;
  topThreeDimensions: Array<{
    dim_code: string;
    label: string;
    score: number;
  }>;
  quoteText: string;
}>();

const emit = defineEmits<{
  (event: "share"): void;
}>();
</script>

<template>
  <view class="hero d1" :style="heroStyle">
    <text class="hero__eyebrow">{{ testName }} · 测试报告</text>
    <view class="hero__main">
      <text class="hero__emoji">{{ personaEmoji }}</text>
      <view class="hero__title-wrap">
        <text class="hero__title">{{ personaName }}</text>
        <text class="hero__tier">{{ tierText }}</text>
      </view>
      <view class="score-ring">
        <view
          class="score-ring__circle"
          :style="{ background: `conic-gradient(#9B7ED8 ${scoreProgress * 3.6}deg, rgba(255,255,255,0.22) 0)` }"
        >
          <view class="score-ring__inner">
            <text class="score-ring__value">{{ totalScore }}</text>
            <text class="score-ring__label">总分</text>
          </view>
        </view>
      </view>
    </view>
    <view class="hero-top-dims">
      <view v-for="item in topThreeDimensions" :key="item.dim_code" class="hero-dim-card">
        <text class="hero-dim-card__name">{{ item.label }}</text>
        <text class="hero-dim-card__score">{{ item.score.toFixed(1) }}</text>
      </view>
    </view>
  </view>

  <view class="panel persona-card d2">
    <view class="panel-head">
      <text class="panel-title">可分享人格卡片</text>
      <button class="mini-button mini-button--light" @tap="emit('share')">分享</button>
    </view>
    <view class="persona-share">
      <text class="persona-share__name">{{ personaName }}</text>
      <text class="persona-share__emoji">{{ personaEmoji }}</text>
      <text class="persona-share__signature">{{ quoteText }}</text>
      <text class="persona-share__top">
        Top 维度：{{ topThreeDimensions.map((item) => item.label).join(" / ") || "平衡成长" }}
      </text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.d1 {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.06s;
}

.d2 {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.12s;
}

.hero {
  border-radius: $xc-r-xl;
  padding: 34rpx 28rpx;
  color: #fff;
  box-shadow: $xc-sh-lg;
}

.hero__eyebrow {
  display: block;
  font-size: 22rpx;
  opacity: 0.88;
}

.hero__main {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 20rpx;
  align-items: center;
}

.hero__emoji {
  font-size: 74rpx;
  line-height: 1;
}

.hero__title-wrap {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.hero__title {
  font-size: 50rpx;
  font-family: $xc-font-serif;
  font-weight: 700;
}

.hero__tier {
  align-self: flex-start;
  padding: 8rpx 16rpx;
  border-radius: $xc-r-pill;
  background: rgba(255, 255, 255, 0.2);
  font-size: 22rpx;
}

.score-ring__circle {
  width: 148rpx;
  height: 148rpx;
  border-radius: 50%;
  padding: 8rpx;
}

.score-ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(31, 22, 41, 0.42);
}

.score-ring__value {
  font-size: 34rpx;
  font-weight: 700;
}

.score-ring__label {
  margin-top: 2rpx;
  font-size: 20rpx;
  opacity: 0.86;
}

.hero-top-dims {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.hero-dim-card {
  padding: 16rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.18);
}

.hero-dim-card__name {
  display: block;
  font-size: 22rpx;
}

.hero-dim-card__score {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.panel {
  border-radius: $xc-r-card;
  padding: 24rpx;
  @include card-base;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  display: block;
  font-size: 30rpx;
  color: $xc-ink;
  font-weight: 600;
}

.mini-button {
  border: none;
  border-radius: 999rpx;
  padding: 12rpx 20rpx;
  font-size: 22rpx;
  color: #fff;
  @include btn-primary;
}

.mini-button--light {
  background: rgba(155, 126, 216, 0.16);
  box-shadow: none;
  color: $xc-purple-d;
}

.persona-share {
  margin-top: 16rpx;
  border-radius: 20rpx;
  padding: 24rpx;
  background: linear-gradient(140deg, rgba(155, 126, 216, 0.9), rgba(232, 114, 154, 0.78));
  color: #fff;
}

.persona-share__name {
  display: block;
  font-size: 38rpx;
  font-family: $xc-font-serif;
  font-weight: 700;
}

.persona-share__emoji {
  display: block;
  margin-top: 8rpx;
  font-size: 56rpx;
}

.persona-share__signature {
  margin-top: 12rpx;
  display: block;
  font-size: 24rpx;
  line-height: 1.6;
}

.persona-share__top {
  margin-top: 10rpx;
  display: block;
  font-size: 22rpx;
  opacity: 0.9;
}
</style>
