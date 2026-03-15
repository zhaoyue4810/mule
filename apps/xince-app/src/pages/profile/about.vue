<script setup lang="ts">
const features = [
  { emoji: "🧪", title: "15 种趣味答题交互", description: "从滑动、气泡到塔罗翻牌，每次作答都像在玩一场轻盈实验。" },
  { emoji: "🔮", title: "AI 驱动的灵魂画像", description: "把答题轨迹整理成更立体的人格报告，帮你看见细微的自己。" },
  { emoji: "💕", title: "双人灵魂匹配", description: "和重要的人一起完成测试，看到彼此相似与互补的地方。" },
  { emoji: "🏆", title: "成长型徽章与碎片收集", description: "把一次次记录沉淀成长期旅程，而不是看完就忘的瞬间结果。" },
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
    <view class="shell">
      <view class="hero-card">
        <view class="brand-mark">
          <text class="brand-mark__char">心</text>
        </view>
        <text class="hero-card__title">心测</text>
        <text class="hero-card__subtitle">你的灵魂说明书</text>
        <text class="hero-card__version">v1.0.0</text>
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

      <view class="card">
        <text class="card__title">法律与说明</text>
        <view class="link-list">
          <view class="link-item" @tap="openLegal('用户协议')">
            <text>用户协议</text>
            <text class="link-item__arrow">›</text>
          </view>
          <view class="link-item" @tap="openLegal('隐私政策')">
            <text>隐私政策</text>
            <text class="link-item__arrow">›</text>
          </view>
        </view>
      </view>

      <text class="copyright">© 2026 XinCe Team</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 28rpx 24rpx 60rpx;
  animation: fadeInUp 0.45s $xc-ease both;
  background:
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.18), transparent 28%),
    radial-gradient(circle at bottom right, rgba(232, 114, 154, 0.14), transparent 24%),
    $xc-bg;
}

.shell {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.hero-card,
.card {
  @include card-base;
}

.hero-card {
  padding: 42rpx 30rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background:
    radial-gradient(circle at top, rgba(255, 245, 218, 0.92), rgba(248, 236, 255, 0.9)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(245, 238, 255, 0.88));
}

.brand-mark {
  width: 140rpx;
  height: 140rpx;
  border-radius: 36rpx;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 20rpx 40rpx rgba(155, 126, 216, 0.25);
}

.brand-mark__char {
  font-size: 64rpx;
  font-weight: 800;
  color: $xc-white;
}

.hero-card__title {
  margin-top: 20rpx;
  font-size: 40rpx;
  font-weight: 800;
  color: $xc-ink;
}

.hero-card__subtitle,
.hero-card__version {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.card {
  padding: 28rpx;
}

.card__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.feature-list {
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

.link-list {
  margin-top: 16rpx;
}

.link-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 0;
  font-size: 26rpx;
  color: $xc-ink;
  border-bottom: 2rpx solid rgba(155, 126, 216, 0.08);
}

.link-item:last-child {
  border-bottom: 0;
}

.link-item__arrow {
  font-size: 34rpx;
  color: $xc-muted;
}

.copyright {
  margin-top: 6rpx;
  text-align: center;
  font-size: 22rpx;
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
