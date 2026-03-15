<script setup lang="ts">
defineProps<{
  heroStyle: Record<string, string>;
  testName: string;
  titleText: string;
  personaEmoji: string;
  personaName: string;
  tierText: string;
  totalScore: number;
  scoreProgress: number;
  rarityText: string;
  topThreeDimensions: Array<{
    dim_code: string;
    label: string;
    score: number;
  }>;
  quoteText: string;
  keywords: string[];
  statChips: string[];
  highlightLines: string[];
  footerText: string;
}>();

const emit = defineEmits<{
  (event: "share"): void;
}>();
</script>

<template>
  <view class="hero-stack">
    <view class="hero d1" :style="heroStyle">
      <view class="hero__ambient hero__ambient--one" />
      <view class="hero__ambient hero__ambient--two" />
      <view class="hero__top">
        <text class="hero__eyebrow">{{ testName }} · 测试报告</text>
        <text class="hero__rarity">{{ rarityText }}</text>
      </view>

      <view class="hero__main">
        <view class="hero__persona-badge">
          <text class="hero__emoji">{{ personaEmoji }}</text>
        </view>

        <view class="hero__title-wrap">
          <text class="hero__hint">{{ titleText }}</text>
          <text class="hero__title">{{ personaName }}</text>
          <view class="hero__meta">
            <text class="hero__tier">{{ tierText }}</text>
            <text
              v-for="keyword in keywords.slice(0, 2)"
              :key="keyword"
              class="hero__keyword"
            >
              {{ keyword }}
            </text>
          </view>
        </view>

        <view class="score-ring">
          <view
            class="score-ring__circle"
            :style="{ background: `conic-gradient(#ffffff ${scoreProgress * 3.6}deg, rgba(255,255,255,0.18) 0)` }"
          >
            <view class="score-ring__inner">
              <text class="score-ring__value">{{ totalScore }}</text>
              <text class="score-ring__label">灵魂指数</text>
            </view>
          </view>
        </view>
      </view>

      <text class="hero__quote">{{ quoteText }}</text>

      <view class="hero-top-dims">
        <view
          v-for="item in topThreeDimensions"
          :key="item.dim_code"
          class="hero-dim-card"
        >
          <text class="hero-dim-card__eyebrow">Top 维度</text>
          <text class="hero-dim-card__name">{{ item.label }}</text>
          <text class="hero-dim-card__score">{{ item.score.toFixed(1) }}</text>
        </view>
      </view>
    </view>

    <view class="panel persona-card d2">
      <view class="panel-head">
        <view>
          <text class="panel-title">可分享人格卡片</text>
          <text class="panel-subtitle">像原型一样，把你的灵魂说明书保存下来。</text>
        </view>
        <button class="mini-button mini-button--light" @tap="emit('share')">分享</button>
      </view>

      <view class="persona-share">
        <view class="persona-share__shine" />
        <view class="persona-share__header">
          <view>
            <text class="persona-share__eyebrow">{{ testName }} · 灵魂说明书</text>
            <text class="persona-share__name">{{ personaName }}</text>
          </view>
          <text class="persona-share__emoji">{{ personaEmoji }}</text>
        </view>

        <view class="persona-share__chips">
          <text
            v-for="chip in statChips.slice(0, 3)"
            :key="chip"
            class="persona-share__chip"
          >
            {{ chip }}
          </text>
        </view>

        <view class="persona-share__highlights">
          <text
            v-for="line in highlightLines.slice(0, 2)"
            :key="line"
            class="persona-share__highlight"
          >
            {{ line }}
          </text>
        </view>

        <view class="persona-share__keywords">
          <text
            v-for="keyword in keywords.slice(0, 4)"
            :key="keyword"
            class="persona-share__keyword"
          >
            {{ keyword }}
          </text>
        </view>

        <view class="persona-share__stats">
          <view
            v-for="item in topThreeDimensions"
            :key="`${item.dim_code}-share`"
            class="persona-share__stat"
          >
            <text class="persona-share__stat-value">{{ item.score.toFixed(1) }}</text>
            <text class="persona-share__stat-label">{{ item.label }}</text>
          </view>
        </view>

        <text class="persona-share__footer">{{ footerText }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.hero-stack {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.d1 {
  animation: fadeInUp 0.55s $xc-ease both;
  animation-delay: 0.06s;
}

.d2 {
  animation: fadeInUp 0.55s $xc-ease both;
  animation-delay: 0.12s;
}

.hero {
  position: relative;
  overflow: hidden;
  border-radius: 36rpx;
  padding: 30rpx 28rpx 26rpx;
  color: #fff;
  box-shadow: 0 22rpx 60rpx rgba(79, 51, 112, 0.26);
}

.hero__ambient {
  position: absolute;
  border-radius: 999rpx;
  pointer-events: none;
  filter: blur(8rpx);
}

.hero__ambient--one {
  top: -30rpx;
  right: -10rpx;
  width: 200rpx;
  height: 200rpx;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.28), transparent 68%);
}

.hero__ambient--two {
  bottom: -60rpx;
  left: -24rpx;
  width: 260rpx;
  height: 180rpx;
  background: radial-gradient(circle, rgba(255, 244, 209, 0.18), transparent 72%);
}

.hero__top,
.hero__main,
.hero__quote,
.hero-top-dims {
  position: relative;
  z-index: 1;
}

.hero__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.hero__eyebrow {
  font-size: 22rpx;
  letter-spacing: 1rpx;
  opacity: 0.92;
}

.hero__rarity {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 20rpx;
  font-weight: 600;
  // #ifdef H5
  backdrop-filter: blur(14rpx);
  // #endif
}

.hero__main {
  margin-top: 24rpx;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 22rpx;
  align-items: center;
}

.hero__persona-badge {
  width: 108rpx;
  height: 108rpx;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.46), transparent 46%),
    rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.18);
}

.hero__emoji {
  font-size: 62rpx;
  line-height: 1;
}

.hero__title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.hero__hint {
  font-size: 22rpx;
  opacity: 0.86;
}

.hero__title {
  font-size: 52rpx;
  line-height: 1.08;
  font-family: $xc-font-serif;
  font-weight: 900;
  text-shadow: 0 8rpx 24rpx rgba(45, 25, 67, 0.15);
}

.hero__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.hero__tier,
.hero__keyword {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
}

.hero__tier {
  background: rgba(28, 17, 45, 0.24);
  font-weight: 700;
}

.hero__keyword {
  background: rgba(255, 255, 255, 0.16);
}

.score-ring__circle {
  width: 154rpx;
  height: 154rpx;
  padding: 10rpx;
  border-radius: 50%;
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.15);
}

.score-ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(33, 22, 46, 0.46);
  // #ifdef H5
  backdrop-filter: blur(12rpx);
  // #endif
}

.score-ring__value {
  font-size: 40rpx;
  font-weight: 800;
}

.score-ring__label {
  margin-top: 4rpx;
  font-size: 20rpx;
  opacity: 0.86;
}

.hero__quote {
  display: block;
  margin-top: 20rpx;
  font-size: 24rpx;
  line-height: 1.72;
  opacity: 0.92;
}

.hero-top-dims {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.hero-dim-card {
  border-radius: 22rpx;
  padding: 18rpx 16rpx;
  background: rgba(255, 255, 255, 0.14);
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.1);
  // #ifdef H5
  backdrop-filter: blur(12rpx);
  // #endif
}

.hero-dim-card__eyebrow {
  display: block;
  font-size: 18rpx;
  opacity: 0.72;
}

.hero-dim-card__name {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  font-weight: 700;
}

.hero-dim-card__score {
  display: block;
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 800;
}

.panel {
  border-radius: 30rpx;
  padding: 26rpx;
  @include card-base;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.panel-title {
  display: block;
  font-size: 30rpx;
  color: $xc-ink;
  font-weight: 800;
}

.panel-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.mini-button {
  border: none;
  border-radius: 999rpx;
  padding: 14rpx 22rpx;
  font-size: 22rpx;
  color: #fff;
  @include btn-primary;
}

.mini-button::after {
  border: none;
}

.mini-button--light {
  background: rgba(155, 126, 216, 0.12);
  color: $xc-purple-d;
  box-shadow: none;
}

.persona-share {
  position: relative;
  overflow: hidden;
  margin-top: 18rpx;
  border-radius: 28rpx;
  padding: 24rpx 24rpx 22rpx;
  background:
    linear-gradient(145deg, rgba(60, 39, 87, 0.94), rgba(124, 93, 191, 0.94), rgba(232, 114, 154, 0.86));
  color: #fff;
  box-shadow: 0 18rpx 50rpx rgba(116, 80, 165, 0.24);
}

.persona-share__shine {
  position: absolute;
  top: -40rpx;
  right: -10rpx;
  width: 180rpx;
  height: 180rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.26), transparent 68%);
}

.persona-share__header,
.persona-share__chips,
.persona-share__highlights,
.persona-share__keywords,
.persona-share__stats,
.persona-share__footer {
  position: relative;
  z-index: 1;
}

.persona-share__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.persona-share__eyebrow {
  display: block;
  font-size: 20rpx;
  opacity: 0.78;
}

.persona-share__name {
  display: block;
  margin-top: 10rpx;
  font-size: 42rpx;
  font-family: $xc-font-serif;
  font-weight: 800;
}

.persona-share__emoji {
  font-size: 64rpx;
  line-height: 1;
}

.persona-share__chips,
.persona-share__keywords {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.persona-share__chip,
.persona-share__keyword {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
}

.persona-share__chip {
  background: rgba(255, 255, 255, 0.18);
}

.persona-share__keyword {
  background: rgba(33, 22, 46, 0.24);
}

.persona-share__highlights {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.persona-share__highlight {
  display: block;
  padding: 16rpx 18rpx;
  border-radius: 18rpx;
  font-size: 23rpx;
  line-height: 1.68;
  background: rgba(255, 255, 255, 0.12);
}

.persona-share__stats {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.persona-share__stat {
  border-radius: 20rpx;
  padding: 16rpx 14rpx;
  background: rgba(255, 255, 255, 0.12);
  text-align: center;
}

.persona-share__stat-value {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
}

.persona-share__stat-label {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  opacity: 0.84;
}

.persona-share__footer {
  display: block;
  margin-top: 18rpx;
  font-size: 20rpx;
  opacity: 0.78;
  text-align: center;
  letter-spacing: 1rpx;
}

@media (max-width: 420px) {
  .hero__main {
    grid-template-columns: 1fr;
  }

  .score-ring {
    justify-self: start;
  }

  .hero-top-dims,
  .persona-share__stats {
    grid-template-columns: 1fr;
  }
}
</style>
