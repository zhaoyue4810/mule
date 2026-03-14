<script setup lang="ts">
import { computed, ref } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";

const props = defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const spinning = ref(false);
const rotation = ref(0);

const options = computed(() => props.question.options || []);
const sectorAngle = computed(() =>
  options.value.length ? 360 / options.value.length : 360,
);

const defaultColors = ["#f5c597", "#f1a8b4", "#cbb8f1", "#9cd0c3", "#f6dd9d", "#f3b9a1"];
const sectorColors = computed(() => {
  const config = (props.question.config || {}) as Record<string, unknown>;
  const configured = Array.isArray(config.sector_colors)
    ? config.sector_colors.filter((item): item is string => typeof item === "string")
    : [];
  return configured.length ? configured : defaultColors;
});

const wheelBackground = computed(() => {
  if (!options.value.length) {
    return "#fff8f1";
  }
  const stops: string[] = [];
  for (let index = 0; index < options.value.length; index += 1) {
    const start = index * sectorAngle.value;
    const end = start + sectorAngle.value;
    const color = sectorColors.value[index % sectorColors.value.length];
    stops.push(`${color} ${start}deg ${end}deg`);
  }
  return `conic-gradient(from -90deg, ${stops.join(", ")})`;
});

const labelPoints = computed(() =>
  options.value.map((option, index) => {
    const theta = (((index + 0.5) * sectorAngle.value - 90) * Math.PI) / 180;
    const radius = 36;
    const x = 50 + Math.cos(theta) * radius;
    const y = 50 + Math.sin(theta) * radius;
    return {
      optionCode: option.option_code || String(option.seq),
      label: option.label,
      style: {
        left: `${x}%`,
        top: `${y}%`,
      },
    };
  }),
);

const selectedLabel = computed(() => {
  if (!props.modelValue) {
    return "";
  }
  const selected = options.value.find(
    (item) => (item.option_code || String(item.seq)) === props.modelValue,
  );
  return selected?.label || "";
});

const wheelStyle = computed(() => ({
  transform: `rotate(${rotation.value}deg)`,
  transition: spinning.value ? "transform 4.2s cubic-bezier(0.15, 0.85, 0.2, 1)" : "none",
}));

function spinWheel() {
  if (spinning.value || !options.value.length) {
    return;
  }
  const pickedIndex = Math.floor(Math.random() * options.value.length);
  const picked = options.value[pickedIndex];
  const pickedCode = picked.option_code || String(picked.seq);
  const centerAngle = pickedIndex * sectorAngle.value + sectorAngle.value / 2;
  const targetRemainder = (360 - centerAngle) % 360;
  const currentRemainder = ((rotation.value % 360) + 360) % 360;
  const delta = (targetRemainder - currentRemainder + 360) % 360;
  const extraSpins = 5 * 360;
  spinning.value = true;
  rotation.value += extraSpins + delta;
  setTimeout(() => {
    spinning.value = false;
    emit("update:modelValue", pickedCode);
  }, 4300);
}
</script>

<template>
  <view class="fortune">
    <view class="fortune__wheel-wrap">
      <view class="fortune__pointer" />
      <view class="fortune__wheel" :style="wheelStyle">
        <view class="fortune__surface" :style="{ background: wheelBackground }" />
        <view
          v-for="point in labelPoints"
          :key="point.optionCode"
          class="fortune__label"
          :class="{ 'fortune__label--active': modelValue === point.optionCode }"
          :style="point.style"
        >
          {{ point.label }}
        </view>
      </view>
    </view>
    <button class="fortune__btn" :disabled="spinning" @tap="spinWheel">
      {{ spinning ? "命运轮盘转动中..." : "转动命运轮盘" }}
    </button>
    <text v-if="selectedLabel" class="fortune__result">当前抽中：{{ selectedLabel }}</text>
  </view>
</template>

<style lang="scss" scoped>
.fortune {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  align-items: center;
}

.fortune__wheel-wrap {
  position: relative;
  width: 460rpx;
  height: 460rpx;
}

.fortune__pointer {
  position: absolute;
  left: 50%;
  top: -8rpx;
  z-index: 4;
  width: 0;
  height: 0;
  margin-left: -16rpx;
  border-left: 16rpx solid transparent;
  border-right: 16rpx solid transparent;
  border-top: 36rpx solid #bf5321;
}

.fortune__label {
  position: absolute;
  width: 140rpx;
  margin-left: -70rpx;
  margin-top: -20rpx;
  text-align: center;
  font-size: 22rpx;
  line-height: 1.4;
  color: #2b2118;
  font-weight: 600;
  text-shadow: 0 1rpx 0 rgba(255, 255, 255, 0.35);
  z-index: 3;
}

.fortune__label--active {
  color: #8d2e00;
  font-weight: 700;
}

.fortune__wheel {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.fortune__surface {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 8rpx solid rgba(255, 255, 255, 0.72);
  box-shadow: $xc-shadow;
}

.fortune__btn {
  width: 420rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #d96f3d, #bf5321);
  color: #fff8f1;
  font-size: 26rpx;
}

.fortune__result {
  font-size: 24rpx;
  color: $xc-muted;
}
</style>
