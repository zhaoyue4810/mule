<script setup lang="ts">
import { computed } from "vue";

type DeepPanelKey = "strength" | "growth" | "advice" | "social";

const props = defineProps<{
  pending: boolean;
  aiRefreshing: boolean;
  aiStatus: string;
  summary: string;
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

const cardMeta: Record<
  DeepPanelKey,
  { icon: string; eyebrow: string; tone: "purple" | "pink" | "gold" | "mint" }
> = {
  strength: { icon: "🌟", eyebrow: "最闪亮的部分", tone: "purple" },
  growth: { icon: "🔧", eyebrow: "还能更进一步", tone: "pink" },
  advice: { icon: "💡", eyebrow: "今天就能用上", tone: "gold" },
  social: { icon: "🤝", eyebrow: "你与世界相处的方式", tone: "mint" },
};

const statusText = computed(() => {
  if (props.pending) {
    return "AI 撰写中";
  }
  if (props.aiStatus === "COMPLETED") {
    return "深度解读已生成";
  }
  return "可继续润色";
});

const statusClass = computed(() => {
  if (props.pending) {
    return "status--pending";
  }
  if (props.aiStatus === "COMPLETED") {
    return "status--done";
  }
  return "status--idle";
});
</script>

<template>
  <view class="panel">
    <view class="panel-head">
      <view>
        <text class="panel-title">深度解读</text>
        <text class="panel-subtitle">{{ summary }}</text>
      </view>
      <text class="status-chip" :class="statusClass">{{ statusText }}</text>
    </view>

    <view v-if="pending" class="ai-skeleton">
      <view class="ai-skeleton__orb">
        <text class="ai-skeleton__orb-icon">✨</text>
      </view>
      <view class="ai-skeleton__content">
        <view class="ai-skeleton__line" />
        <view class="ai-skeleton__line ai-skeleton__line--short" />
        <view class="ai-skeleton__line" />
        <text class="ai-skeleton__hint">小测正在把你的结果整理成更像“灵魂说明书”的语言。</text>
      </view>
    </view>

    <view v-else class="deep-list">
      <view
        v-for="item in sections"
        :key="item.key"
        class="deep-card"
        :class="[`deep-card--${cardMeta[item.key].tone}`, { 'deep-card--open': activeKey === item.key }]"
      >
        <view class="deep-card__head" @tap="emit('toggle', item.key)">
          <view class="deep-card__lead">
            <view class="deep-card__icon-wrap">
              <text class="deep-card__icon">{{ cardMeta[item.key].icon }}</text>
            </view>
            <view class="deep-card__title-wrap">
              <text class="deep-card__eyebrow">{{ cardMeta[item.key].eyebrow }}</text>
              <text class="deep-card__title">{{ item.title }}</text>
            </view>
          </view>
          <text class="deep-card__toggle">{{ activeKey === item.key ? "收起" : "展开" }}</text>
        </view>

        <view class="deep-card__body">
          <text class="deep-card__body-text">{{ item.text }}</text>
        </view>
      </view>
    </view>

    <view class="panel-foot">
      <text class="panel-foot__note">想换一种表达口吻时，可以重新生成一次 AI 解读。</text>
      <button
        v-if="aiStatus !== 'COMPLETED' || !pending"
        class="mini-button"
        :disabled="aiRefreshing"
        @tap="emit('retry')"
      >
        {{ aiRefreshing ? "处理中..." : "重新生成 AI 解读" }}
      </button>
    </view>
  </view>
</template>

<style scoped lang="scss">
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
  line-height: 1.64;
  color: $xc-muted;
}

.status-chip {
  flex-shrink: 0;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 700;
}

.status--pending {
  background: rgba(212, 168, 83, 0.15);
  color: #9f6b17;
}

.status--done {
  background: rgba(124, 197, 178, 0.18);
  color: #2d6a5c;
}

.status--idle {
  background: rgba(155, 126, 216, 0.12);
  color: $xc-purple-d;
}

.ai-skeleton {
  margin-top: 18rpx;
  border-radius: 24rpx;
  padding: 24rpx;
  display: flex;
  gap: 18rpx;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.86), rgba(252, 247, 255, 0.94));
  border: 2rpx solid rgba(155, 126, 216, 0.1);
}

.ai-skeleton__orb {
  width: 88rpx;
  height: 88rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 28rpx;
  background: linear-gradient(135deg, rgba(155, 126, 216, 0.22), rgba(232, 114, 154, 0.18));
}

.ai-skeleton__orb-icon {
  font-size: 42rpx;
  animation: pulseSoft 1.8s ease-in-out infinite;
}

.ai-skeleton__content {
  flex: 1;
}

.ai-skeleton__line {
  height: 18rpx;
  border-radius: 999rpx;
  margin-top: 10rpx;
  background: linear-gradient(
    90deg,
    rgba(155, 126, 216, 0.06),
    rgba(155, 126, 216, 0.26),
    rgba(155, 126, 216, 0.08)
  );
  background-size: 220% 100%;
  animation: shimmer 1.5s linear infinite;
}

.ai-skeleton__line--short {
  width: 72%;
}

.ai-skeleton__hint {
  display: block;
  margin-top: 18rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.deep-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.deep-card {
  border-radius: 24rpx;
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  background: rgba(255, 255, 255, 0.86);
  overflow: hidden;
  transition: transform 0.24s $xc-ease, border-color 0.24s $xc-ease;
}

.deep-card--open {
  transform: translateY(-2rpx);
}

.deep-card--purple.deep-card--open {
  border-color: rgba(155, 126, 216, 0.22);
}

.deep-card--pink.deep-card--open {
  border-color: rgba(232, 114, 154, 0.24);
}

.deep-card--gold.deep-card--open {
  border-color: rgba(212, 168, 83, 0.24);
}

.deep-card--mint.deep-card--open {
  border-color: rgba(124, 197, 178, 0.24);
}

.deep-card__head {
  padding: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.deep-card__lead {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.deep-card__icon-wrap {
  width: 74rpx;
  height: 74rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, rgba(155, 126, 216, 0.16), rgba(255, 255, 255, 0.86));
}

.deep-card--pink .deep-card__icon-wrap {
  background: linear-gradient(145deg, rgba(232, 114, 154, 0.16), rgba(255, 255, 255, 0.88));
}

.deep-card--gold .deep-card__icon-wrap {
  background: linear-gradient(145deg, rgba(212, 168, 83, 0.16), rgba(255, 255, 255, 0.9));
}

.deep-card--mint .deep-card__icon-wrap {
  background: linear-gradient(145deg, rgba(124, 197, 178, 0.16), rgba(255, 255, 255, 0.9));
}

.deep-card__icon {
  font-size: 34rpx;
}

.deep-card__title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.deep-card__eyebrow {
  display: block;
  font-size: 20rpx;
  color: $xc-muted;
}

.deep-card__title {
  display: block;
  font-size: 27rpx;
  font-weight: 800;
  color: $xc-ink;
}

.deep-card__toggle {
  font-size: 20rpx;
  font-weight: 700;
  color: $xc-purple-d;
}

.deep-card__body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.34s $xc-ease, padding 0.34s $xc-ease;
  padding: 0 20rpx;
}

.deep-card__body-text {
  display: block;
  color: $xc-muted;
  font-size: 24rpx;
  line-height: 1.8;
}

.deep-card--open .deep-card__body {
  max-height: 340rpx;
  padding: 0 20rpx 22rpx;
}

.panel-foot {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.panel-foot__note {
  flex: 1;
  font-size: 21rpx;
  line-height: 1.58;
  color: $xc-muted;
}

.mini-button {
  flex-shrink: 0;
  border: none;
  border-radius: 999rpx;
  padding: 14rpx 24rpx;
  font-size: 22rpx;
  color: #fff;
  @include btn-primary;
}

.mini-button::after {
  border: none;
}

@keyframes pulseSoft {
  0%,
  100% {
    transform: scale(1);
    opacity: 0.88;
  }

  50% {
    transform: scale(1.08);
    opacity: 1;
  }
}
</style>
