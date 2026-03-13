<script setup lang="ts">
import type { PublishedQuestionPayload } from "@/shared/models/tests";

defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const fallbackPositions = [
  { left: "14%", top: "28%" },
  { left: "62%", top: "12%" },
  { left: "36%", top: "58%" },
  { left: "78%", top: "48%" },
  { left: "18%", top: "78%" },
];
</script>

<template>
  <view class="constellation">
    <view class="constellation__board">
      <view
        v-for="(option, index) in question.options"
        :key="option.option_code || option.seq"
        class="constellation__star"
        :class="{ 'constellation__star--active': modelValue === (option.option_code || String(option.seq)) }"
        :style="{
          left: fallbackPositions[index % fallbackPositions.length].left,
          top: fallbackPositions[index % fallbackPositions.length].top,
        }"
        @tap="emit('update:modelValue', option.option_code || String(option.seq))"
      >
        <text class="constellation__glyph">{{ option.emoji || "✦" }}</text>
        <text class="constellation__label">{{ option.label }}</text>
      </view>
    </view>
    <text class="constellation__tip">点亮最像你此刻轨迹的那颗星。</text>
  </view>
</template>

<style lang="scss" scoped>
.constellation {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.constellation__board {
  position: relative;
  min-height: 420rpx;
  border-radius: 28rpx;
  background:
    radial-gradient(circle at top, rgba(131, 109, 199, 0.18), rgba(34, 27, 56, 0.92)),
    #241c3f;
  overflow: hidden;
}

.constellation__board::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.8) 0, transparent 8rpx),
    radial-gradient(circle at 70% 28%, rgba(255, 255, 255, 0.7) 0, transparent 6rpx),
    radial-gradient(circle at 46% 74%, rgba(255, 255, 255, 0.6) 0, transparent 7rpx);
  opacity: 0.35;
  pointer-events: none;
}

.constellation__star {
  position: absolute;
  width: 132rpx;
  min-height: 108rpx;
  padding: 18rpx 10rpx;
  margin-left: -66rpx;
  margin-top: -54rpx;
  border-radius: 22rpx;
  text-align: center;
  background: rgba(255, 255, 255, 0.12);
  border: 2rpx solid rgba(255, 255, 255, 0.2);
  color: #fffaf3;
  backdrop-filter: blur(8rpx);
}

.constellation__star--active {
  background: rgba(255, 223, 196, 0.26);
  border-color: rgba(255, 227, 200, 0.78);
  box-shadow: 0 0 22rpx rgba(255, 212, 179, 0.45);
}

.constellation__glyph {
  display: block;
  font-size: 30rpx;
}

.constellation__label {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.5;
}

.constellation__tip {
  font-size: 22rpx;
  color: $xc-muted;
}
</style>
