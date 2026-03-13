<template>
  <view class="page">
    <view class="panel">
      <text class="panel__title">发现页待接入</text>
      <text class="panel__body">
        这里会承接推荐测试、主题专题和成长内容。当前先把用户端主工程和测试链路打通。
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
