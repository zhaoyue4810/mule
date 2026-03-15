<script setup lang="ts">
import { computed, ref } from "vue";

import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: number | null;
  min?: number;
  max?: number;
  step?: number;
  labels?: string[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const flash = ref(false);
const values = computed(() => {
  const min = props.min ?? 1;
  const max = props.max ?? 5;
  const out: number[] = [];
  for (let v = min; v <= max; v += props.step ?? 1) {
    out.push(v);
  }
  return out;
});
const caption = computed(() => {
  if (!props.modelValue) {
    return "1=完全不是, 5=非常像我";
  }
  return props.labels?.[props.modelValue - 1] || `评分 ${props.modelValue}`;
});

function select(value: number) {
  playSound("chime");
  haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  emit("update:modelValue", value);
}
</script>

<template>
  <view class="stars q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="stars__row">
      <text
        v-for="value in values"
        :key="value"
        class="stars__item"
        :class="{ 'stars__item--active': (modelValue || 0) >= value }"
        @tap="select(value)"
      >
        {{ (modelValue || 0) >= value ? "★" : "☆" }}
      </text>
    </view>
    <view class="stars__labels">
      <text>完全不是我</text>
      <text>就是我本人</text>
    </view>
    <text class="stars__caption">{{ caption }}</text>
  </view>
</template>

<style lang="scss" scoped>
.stars {
  position: relative;
  text-align: center;
  padding: 18rpx 0 10rpx;
}

.stars__row {
  display: flex;
  justify-content: center;
  gap: 12rpx;
}

.stars__item {
  font-size: 68rpx;
  color: rgba(123, 110, 133, 0.3);
  transition: all 0.25s $xc-spring;
  filter: grayscale(1) opacity(0.42);
}

.stars__item--active {
  color: $xc-gold;
  filter: none;
  animation: starPulse 0.4s $xc-spring both;
}

.stars__labels {
  display: flex;
  justify-content: space-between;
  margin-top: 10rpx;
  padding: 0 12rpx;
  font-size: 18rpx;
  color: $xc-hint;
}

.stars__caption {
  margin-top: 14rpx;
  display: block;
  color: $xc-purple;
  font-size: 26rpx;
  font-weight: 800;
}

.edge-flash {
  position: absolute;
  inset: 0;
  animation: edgeFlash 0.3s ease;
}

.q-enter {
  animation: qEnter 0.4s $xc-ease both;
}

@keyframes starPulse {
  0% {
    transform: scale(0.8);
  }
  60% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes qEnter {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes edgeFlash {
  from {
    box-shadow: inset 0 0 0 0 rgba(212, 168, 83, 0.55);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(212, 168, 83, 0);
  }
}
</style>
