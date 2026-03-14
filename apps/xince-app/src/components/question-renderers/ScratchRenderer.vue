<script setup lang="ts">
import { computed, getCurrentInstance, nextTick, onMounted, ref, watch } from "vue";

import type { PublishedQuestionPayload } from "@/shared/models/tests";
import { SoundManager } from "@/shared/utils/sound-manager";

const props = defineProps<{
  modelValue: string;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const gridCols = 14;
const gridRows = 8;
const totalCells = gridCols * gridRows;
const clearedCells = ref<boolean[]>([]);
const maskRect = ref<{ left: number; top: number; width: number; height: number } | null>(
  null,
);
const instance = getCurrentInstance();

const config = computed<Record<string, unknown>>(
  () => (props.question.config as Record<string, unknown> | null) || {},
);
const revealThreshold = computed(() => {
  const value = Number(config.value.reveal_threshold ?? 0.35);
  if (!Number.isFinite(value)) {
    return 0.35;
  }
  return Math.min(0.95, Math.max(0.1, value));
});
const stageHeight = computed(() => {
  const value = Number(config.value.canvas_height ?? 220);
  if (!Number.isFinite(value) || value <= 0) {
    return 220;
  }
  return value;
});
const stageStyle = computed(() => ({
  minHeight: `${stageHeight.value}rpx`,
}));
const clearedRatio = computed(() => {
  const clearedCount = clearedCells.value.filter(Boolean).length;
  return clearedCount / totalCells;
});
const revealed = computed(() => clearedRatio.value >= revealThreshold.value);
const progressText = computed(() => `${Math.round(clearedRatio.value * 100)}%`);

function resetScratchMask() {
  clearedCells.value = Array.from({ length: totalCells }, () => false);
  maskRect.value = null;
}

watch(
  revealed,
  (value, previous) => {
    if (value && !previous) {
      SoundManager.haptic(50);
      SoundManager.play("ding");
    }
  },
);

watch(
  () => props.question.seq,
  () => {
    resetScratchMask();
    void nextTick(() => {
      void ensureMaskRect();
    });
  },
  { immediate: true },
);

onMounted(() => {
  void nextTick(() => {
    void ensureMaskRect();
  });
});

function markCell(row: number, col: number) {
  if (row < 0 || row >= gridRows || col < 0 || col >= gridCols) {
    return;
  }
  const index = row * gridCols + col;
  if (!clearedCells.value[index]) {
    clearedCells.value[index] = true;
  }
}

async function ensureMaskRect() {
  if (maskRect.value) {
    return maskRect.value;
  }
  const proxy = instance?.proxy;
  return new Promise<{ left: number; top: number; width: number; height: number } | null>(
    (resolve) => {
      if (!proxy) {
        resolve(null);
        return;
      }
      uni.createSelectorQuery()
        .in(proxy)
        .select(".scratch__mask")
        .boundingClientRect((rect) => {
          const targetRect = Array.isArray(rect) ? rect[0] : rect;
          if (
            targetRect &&
            typeof targetRect.left === "number" &&
            typeof targetRect.top === "number" &&
            typeof targetRect.width === "number" &&
            typeof targetRect.height === "number"
          ) {
            const parsedRect = {
              left: targetRect.left,
              top: targetRect.top,
              width: targetRect.width,
              height: targetRect.height,
            };
            maskRect.value = parsedRect;
            resolve(parsedRect);
            return;
          }
          resolve(null);
        })
        .exec();
    },
  );
}

function getTouchPoint(event: {
  touches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
  changedTouches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
}) {
  const touch = event.touches?.[0] || event.changedTouches?.[0];
  if (!touch) {
    return null;
  }
  const x = touch.clientX ?? touch.pageX ?? touch.x;
  const y = touch.clientY ?? touch.pageY ?? touch.y;
  if (typeof x !== "number" || typeof y !== "number") {
    return null;
  }
  return { x, y };
}

async function onScratch(event: {
  touches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
  changedTouches?: Array<{ clientX?: number; pageX?: number; x?: number; clientY?: number; pageY?: number; y?: number }>;
}) {
  if (revealed.value) {
    return;
  }
  const point = getTouchPoint(event);
  if (!point) {
    return;
  }
  const rect = await ensureMaskRect();
  if (!rect || rect.width <= 0 || rect.height <= 0) {
    return;
  }
  const localX = point.x - rect.left;
  const localY = point.y - rect.top;
  if (localX < 0 || localX > rect.width || localY < 0 || localY > rect.height) {
    return;
  }
  const col = Math.floor((localX / rect.width) * gridCols);
  const row = Math.floor((localY / rect.height) * gridRows);
  for (let dr = -1; dr <= 1; dr += 1) {
    for (let dc = -1; dc <= 1; dc += 1) {
      markCell(row + dr, col + dc);
    }
  }
}
</script>

<template>
  <view class="scratch">
    <view class="scratch__card" :class="{ 'scratch__card--revealed': revealed }" :style="stageStyle">
      <text class="scratch__title">{{ revealed ? "已揭晓" : "滑动手指刮开遮罩" }}</text>
      <text class="scratch__hint">
        {{ revealed ? "现在选择最打动你的结果。" : `刮开进度：${progressText}` }}
      </text>
      <view
        v-if="!revealed"
        class="scratch__mask"
        @touchstart.prevent="onScratch"
        @touchmove.prevent="onScratch"
        @touchend.prevent="onScratch"
        @touchcancel.prevent="onScratch"
      >
        <view
          v-for="(_, index) in clearedCells"
          :key="index"
          class="scratch__cell"
          :class="{ 'scratch__cell--cleared': clearedCells[index] }"
        />
      </view>
    </view>
    <view class="scratch__options" v-if="revealed">
      <view
        v-for="option in question.options"
        :key="option.option_code || option.seq"
        class="scratch__option"
        :class="{ 'scratch__option--active': modelValue === (option.option_code || String(option.seq)) }"
        @tap="emit('update:modelValue', option.option_code || String(option.seq))"
      >
        <text>{{ option.label }}</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.scratch {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.scratch__card {
  position: relative;
  padding: 48rpx 24rpx;
  border-radius: 28rpx;
  text-align: center;
  background:
    linear-gradient(145deg, rgba(188, 188, 188, 0.95), rgba(224, 224, 224, 0.9)),
    #ddd;
}

.scratch__card--revealed {
  background:
    radial-gradient(circle at top, rgba(255, 240, 219, 0.98), rgba(255, 213, 179, 0.92)),
    #fff5ec;
}

.scratch__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.scratch__hint {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.scratch__mask {
  position: absolute;
  left: 16rpx;
  right: 16rpx;
  top: 16rpx;
  bottom: 16rpx;
  display: grid;
  grid-template-columns: repeat(14, minmax(0, 1fr));
  grid-template-rows: repeat(8, minmax(0, 1fr));
  gap: 2rpx;
  border-radius: 22rpx;
  overflow: hidden;
}

.scratch__cell {
  background: linear-gradient(145deg, rgba(191, 191, 191, 0.94), rgba(223, 223, 223, 0.9));
}

.scratch__cell--cleared {
  background: transparent;
}

.scratch__options {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.scratch__option {
  padding: 24rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(43, 33, 24, 0.07);
}

.scratch__option--active {
  border-color: rgba(217, 111, 61, 0.45);
  background: rgba(255, 235, 221, 0.94);
}
</style>
