<template>
  <view class="page">
    <view class="panel panel--accent">
      <text class="panel__title">匹配页预留</text>
      <text class="panel__body">
        双人测试、邀请码和匹配报告会在 P1 阶段接进来。当前先保持页面路径和信息架构稳定。
      </text>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx;
}

.panel {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.85);
  border: 2rpx solid $xc-line;
}

.panel--accent {
  background: rgba(255, 242, 232, 0.92);
}

.panel__title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
}

.panel__body {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: $xc-muted;
}
</style>
