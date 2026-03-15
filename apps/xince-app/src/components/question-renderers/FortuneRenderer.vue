<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { haptic, playSound } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const spinning = ref(false);
const rotation = ref(0);
const flash = ref(false);
let spinTimer: ReturnType<typeof setTimeout> | null = null;

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
  playSound("whoosh");
  haptic(15);
  flash.value = true;
  setTimeout(() => {
    flash.value = false;
  }, 300);
  const pickedIndex = Math.floor(Math.random() * options.value.length);
  const picked = options.value[pickedIndex];
  const pickedCode = picked.option_code || String(picked.seq);
  const centerAngle = pickedIndex * sectorAngle.value + sectorAngle.value / 2;
  const targetRemainder = (360 - centerAngle) % 360;
  const currentRemainder = ((rotation.value % 360) + 360) % 360;
  const delta = (targetRemainder - currentRemainder + 360) % 360;
  const extraSpins = (3 + Math.floor(Math.random() * 3)) * 360;
  spinning.value = true;
  rotation.value += extraSpins + delta;
  if (spinTimer) {
    clearTimeout(spinTimer);
  }
  spinTimer = setTimeout(() => {
    spinning.value = false;
    rotation.value = ((rotation.value % 360) + 360) % 360;
    emit("update:modelValue", pickedCode);
    spinTimer = null;
  }, 4300);
}

onBeforeUnmount(() => {
  if (spinTimer) {
    clearTimeout(spinTimer);
    spinTimer = null;
  }
});
</script>

<template>
  <view class="fortune q-enter">
    <view v-if="flash" class="edge-flash" />
    <view class="fortune__wheel-wrap">
      <view class="fortune__pointer">📍</view>
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
      <view class="fortune__center" @tap="spinWheel">转动</view>
    </view>
    <button class="fortune__btn" :disabled="spinning" @tap="spinWheel">
      {{ spinning ? "命运轮盘转动中..." : "点击中间或按钮开始" }}
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
  width: 520rpx;
  height: 520rpx;
}

.fortune__pointer {
  position: absolute;
  left: 50%;
  top: -16rpx;
  z-index: 4;
  transform: translateX(-50%);
  font-size: 34rpx;
  filter: drop-shadow(0 4rpx 10rpx rgba(0, 0, 0, 0.14));
}

.fortune__label {
  position: absolute;
  width: 132rpx;
  margin-left: -66rpx;
  margin-top: -24rpx;
  text-align: center;
  font-size: 20rpx;
  line-height: 1.4;
  color: #fff;
  font-weight: 700;
  text-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.16);
  z-index: 3;
}

.fortune__label--active {
  color: #fff9e8;
}

.fortune__wheel {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  transform-origin: center;
  will-change: transform;
}

.fortune__surface {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 8rpx solid rgba(255, 255, 255, 0.32);
  box-shadow:
    0 4rpx 24rpx rgba(155, 126, 216, 0.2),
    inset 0 0 0 4rpx rgba(255, 255, 255, 0.3);
}

.fortune__center {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 5;
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  color: $xc-white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  font-weight: 800;
  box-shadow: 0 8rpx 22rpx rgba(155, 126, 216, 0.32);
}

.fortune__btn {
  width: 420rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, $xc-purple, #7c5dbf);
  color: #fff8f1;
  font-size: 24rpx;
}

.fortune__result {
  font-size: 24rpx;
  color: $xc-muted;
  animation: popIn 0.24s $xc-spring both;
}

.edge-flash {
  position: absolute;
  inset: 0;
  pointer-events: none;
  animation: edgeFlash 0.3s ease;
}

.q-enter {
  animation: qEnter 0.4s $xc-ease both;
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

@keyframes popIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes edgeFlash {
  from {
    box-shadow: inset 0 0 0 0 rgba(155, 126, 216, 0.58);
  }
  to {
    box-shadow: inset 0 0 0 14rpx rgba(155, 126, 216, 0);
  }
}
</style>
