<script setup lang="ts">
const features = [
  { emoji: "🧪", title: "15 种趣味答题交互", description: "从滑动、气泡到塔罗翻牌，每次作答都像在玩一场轻盈实验。" },
  { emoji: "🔮", title: "AI 驱动的灵魂画像", description: "把答题轨迹整理成更立体的人格报告，帮你看见细微的自己。" },
  { emoji: "💕", title: "双人灵魂匹配", description: "和重要的人一起完成测试，看到彼此相似与互补的地方。" },
  { emoji: "🏆", title: "成长型徽章与碎片收集", description: "把一次次记录沉淀成长期旅程，而不是看完就忘的瞬间结果。" },
];

const milestones = [
  "用轻心理测试替代生硬问卷，让探索更像一场游戏。",
  "把报告、匹配、徽章、碎片和日历串成一条持续成长链路。",
  "让“小测”成为会记住你、陪你慢慢完成画像的长期角色。",
];

function openLegal(title: string) {
  uni.showToast({
    title: `${title}即将上线`,
    icon: "none",
  });
}
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--pink" />
    <view class="shell">
      <view class="hero-card">
        <view class="hero-card__brand">
          <view class="brand-mark">
            <text class="brand-mark__char">心</text>
          </view>
          <view class="hero-card__copy">
            <text class="hero-card__eyebrow">ABOUT XINCE</text>
            <text class="hero-card__title">心测</text>
            <text class="hero-card__subtitle">你的灵魂说明书</text>
          </view>
        </view>
        <text class="hero-card__body">
          心测不是一张做完就结束的报告，而是一条会随着测试、匹配和每日记录不断生长的长期旅程。
        </text>
        <view class="hero-card__meta">
          <text class="hero-card__meta-item">v1.0.0</text>
          <text class="hero-card__meta-item">H5 / 小程序双端体验</text>
        </view>
      </view>

      <view class="card">
        <text class="card__title">核心体验</text>
        <view class="feature-list">
          <view v-for="item in features" :key="item.title" class="feature-item">
            <view class="feature-item__icon">
              <text>{{ item.emoji }}</text>
            </view>
            <view class="feature-item__body">
              <text class="feature-item__title">{{ item.title }}</text>
              <text class="feature-item__desc">{{ item.description }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="card card--soft">
        <text class="card__title">我们想做的事</text>
        <view class="milestone-list">
          <view v-for="item in milestones" :key="item" class="milestone-item">
            <text class="milestone-item__dot" />
            <text class="milestone-item__body">{{ item }}</text>
          </view>
        </view>
      </view>

      <view class="card">
        <text class="card__title">法律与说明</text>
        <view class="link-list">
          <view class="link-item" @tap="openLegal('用户协议')">
            <view class="link-item__content">
              <text class="link-item__title">用户协议</text>
              <text class="link-item__desc">了解账号、测试和内容使用规则</text>
            </view>
            <text class="link-item__arrow">›</text>
          </view>
          <view class="link-item" @tap="openLegal('隐私政策')">
            <view class="link-item__content">
              <text class="link-item__title">隐私政策</text>
              <text class="link-item__desc">查看数据采集、保护和使用方式</text>
            </view>
            <text class="link-item__arrow">›</text>
          </view>
        </view>
      </view>

      <text class="copyright">© 2026 XinCe Team · 用心理学的温度照亮每个灵魂</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28rpx 24rpx 60rpx;
  background:
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.18), transparent 28%),
    radial-gradient(circle at bottom right, rgba(232, 114, 154, 0.14), transparent 24%),
    $xc-bg;
}

.page__glow {
  position: absolute;
  width: 420rpx;
  height: 420rpx;
  border-radius: 50%;
  filter: blur(30px);
  opacity: 0.42;
  pointer-events: none;
}

.page__glow--violet {
  top: -120rpx;
  right: -120rpx;
  background: rgba(155, 126, 216, 0.22);
}

.page__glow--pink {
  left: -120rpx;
  bottom: 180rpx;
  background: rgba(232, 114, 154, 0.14);
}

.shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.hero-card,
.card {
  @include card-base;
}

.hero-card {
  padding: 34rpx 30rpx;
  background:
    radial-gradient(circle at top, rgba(255, 245, 218, 0.92), rgba(248, 236, 255, 0.9)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(245, 238, 255, 0.88));
}

.hero-card__brand {
  display: flex;
  gap: 18rpx;
  align-items: center;
}

.brand-mark {
  width: 132rpx;
  height: 132rpx;
  border-radius: 36rpx;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 20rpx 40rpx rgba(155, 126, 216, 0.25);
}

.brand-mark__char {
  font-size: 60rpx;
  font-weight: 800;
  color: $xc-white;
}

.hero-card__copy {
  flex: 1;
}

.hero-card__eyebrow {
  display: block;
  font-size: 20rpx;
  letter-spacing: 2.8rpx;
  font-weight: 700;
  color: rgba(123, 110, 133, 0.76);
}

.hero-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 42rpx;
  font-weight: 800;
  color: $xc-ink;
}

.hero-card__subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 25rpx;
  color: $xc-accent;
}

.hero-card__body {
  display: block;
  margin-top: 22rpx;
  font-size: 24rpx;
  line-height: 1.8;
  color: $xc-muted;
}

.hero-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.hero-card__meta-item {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 242, 231, 0.96);
  font-size: 22rpx;
  color: $xc-ink;
}

.card {
  padding: 28rpx;
}

.card--soft {
  background:
    linear-gradient(145deg, rgba(255, 251, 244, 0.96), rgba(248, 241, 255, 0.9));
}

.card__title {
  display: block;
  font-size: 31rpx;
  font-weight: 800;
  color: $xc-ink;
}

.feature-list,
.milestone-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.feature-item {
  display: flex;
  gap: 18rpx;
  align-items: flex-start;
  padding: 18rpx;
  border-radius: 24rpx;
  background: rgba(248, 246, 255, 0.9);
}

.feature-item__icon {
  width: 74rpx;
  height: 74rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.88);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
}

.feature-item__body {
  flex: 1;
}

.feature-item__title {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.feature-item__desc {
  display: block;
  margin-top: 8rpx;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.milestone-item {
  display: flex;
  gap: 14rpx;
  align-items: flex-start;
  padding: 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 247, 238, 0.92);
}

.milestone-item__dot {
  width: 18rpx;
  height: 18rpx;
  margin-top: 10rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  box-shadow: 0 0 0 8rpx rgba(155, 126, 216, 0.1);
}

.milestone-item__body {
  flex: 1;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-ink;
}

.link-list {
  margin-top: 18rpx;
}

.link-item {
  display: grid;
  grid-template-columns: 1fr 24rpx;
  gap: 16rpx;
  align-items: center;
  padding: 22rpx 0;
  border-bottom: 1px solid rgba(155, 126, 216, 0.08);
}

.link-item:last-child {
  border-bottom: 0;
}

.link-item__content {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.link-item__title {
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.link-item__desc {
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.link-item__arrow {
  font-size: 30rpx;
  color: $xc-hint;
  text-align: right;
}

.copyright {
  margin-top: 4rpx;
  text-align: center;
  font-size: 22rpx;
  line-height: 1.7;
  color: rgba(123, 110, 133, 0.82);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
