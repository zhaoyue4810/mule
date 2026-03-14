<script setup lang="ts">
type DeepPanelKey = "strength" | "growth" | "advice" | "social";

defineProps<{
  pending: boolean;
  aiRefreshing: boolean;
  aiStatus: string;
  sections: Array<{
    key: DeepPanelKey;
    title: string;
    text: string;
  }>;
  activeKey: DeepPanelKey | null;
}>();

const emit = defineEmits<{
  (event: "toggle", key: DeepPanelKey): void;
  (event: "retry"): void;
}>();
</script>

<template>
  <view class="panel">
    <text class="panel-title">深度分析</text>
    <view v-if="pending" class="ai-skeleton">
      <view class="ai-skeleton__line" />
      <view class="ai-skeleton__line ai-skeleton__line--short" />
      <view class="ai-skeleton__line" />
      <text class="ai-skeleton__hint">小测正在撰写深度分析...</text>
    </view>
    <view v-else class="deep-list">
      <view
        v-for="item in sections"
        :key="item.key"
        class="deep-card"
        :class="{ 'deep-card--open': activeKey === item.key }"
      >
        <view class="deep-card__head" @tap="emit('toggle', item.key)">
          <text class="deep-card__title">{{ item.title }}</text>
          <text class="deep-card__icon">{{ activeKey === item.key ? "−" : "+" }}</text>
        </view>
        <view class="deep-card__body">
          <text>{{ item.text }}</text>
        </view>
      </view>
    </view>
    <button
      v-if="aiStatus !== 'COMPLETED'"
      class="mini-button"
      :disabled="aiRefreshing"
      @tap="emit('retry')"
    >
      {{ aiRefreshing ? "处理中..." : "重新生成 AI 解读" }}
    </button>
  </view>
</template>

<style scoped lang="scss">
.panel {
  border-radius: $xc-r-card;
  padding: 24rpx;
  @include card-base;
}

.panel-title {
  display: block;
  font-size: 30rpx;
  color: $xc-ink;
  font-weight: 600;
}

.ai-skeleton {
  margin-top: 18rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.86);
  padding: 20rpx;
}

.ai-skeleton__line {
  height: 16rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, rgba(155, 126, 216, 0.08), rgba(155, 126, 216, 0.28), rgba(155, 126, 216, 0.08));
  background-size: 220% 100%;
  animation: shimmer 1.5s linear infinite;
  margin-top: 10rpx;
}

.ai-skeleton__line--short {
  width: 74%;
}

.ai-skeleton__hint {
  margin-top: 16rpx;
  display: block;
  font-size: 22rpx;
  color: $xc-muted;
}

.deep-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.deep-card {
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.84);
  border: 2rpx solid rgba(155, 126, 216, 0.1);
  overflow: hidden;
}

.deep-card__head {
  padding: 18rpx 20rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.deep-card__title {
  font-size: 26rpx;
  color: $xc-ink;
}

.deep-card__icon {
  font-size: 30rpx;
  color: $xc-purple;
}

.deep-card__body {
  max-height: 0;
  transition: max-height 0.28s $xc-ease, padding 0.28s $xc-ease;
  padding: 0 20rpx;
  overflow: hidden;
  color: $xc-muted;
  font-size: 24rpx;
  line-height: 1.7;
}

.deep-card--open .deep-card__body {
  max-height: 240rpx;
  padding: 0 20rpx 18rpx;
}

.mini-button {
  margin-top: 14rpx;
  border: none;
  border-radius: 999rpx;
  padding: 14rpx 22rpx;
  font-size: 22rpx;
  color: #fff;
  @include btn-primary;
}
</style>
