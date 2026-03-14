<script setup lang="ts">
import { getCurrentInstance, nextTick, onMounted, watch } from "vue";

import type { MatchDimensionComparisonItem } from "@/shared/models/match";

const props = defineProps<{
  dimensions: MatchDimensionComparisonItem[];
}>();

const instance = getCurrentInstance();
const canvasId = `match-radar-${Math.random().toString(36).slice(2, 8)}`;

function pointAt(
  cx: number,
  cy: number,
  radius: number,
  angle: number,
  value: number,
) {
  const scaled = (Math.max(0, Math.min(value, 100)) / 100) * radius;
  return {
    x: cx + Math.cos(angle) * scaled,
    y: cy + Math.sin(angle) * scaled,
  };
}

function drawPolygon(
  ctx: UniApp.CanvasContext,
  values: number[],
  radius: number,
  centerX: number,
  centerY: number,
  strokeColor: string,
  fillColor: string,
) {
  if (!values.length) {
    return;
  }

  ctx.beginPath();
  values.forEach((value, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / values.length;
    const point = pointAt(centerX, centerY, radius, angle, value);
    if (index === 0) {
      ctx.moveTo(point.x, point.y);
    } else {
      ctx.lineTo(point.x, point.y);
    }
  });
  ctx.closePath();
  ctx.setStrokeStyle(strokeColor);
  ctx.setFillStyle(fillColor);
  ctx.setLineWidth(2);
  ctx.stroke();
  ctx.fill();
}

function drawRadar() {
  if (!instance?.proxy) {
    return;
  }
  const ctx = uni.createCanvasContext(canvasId, instance.proxy);
  const width = 320;
  const height = 320;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 110;
  const dimensions = props.dimensions.slice(0, 6);

  ctx.clearRect(0, 0, width, height);
  ctx.setFillStyle("#fffaf4");
  ctx.fillRect(0, 0, width, height);

  for (let step = 1; step <= 4; step += 1) {
    const gridValues = dimensions.map(() => (step / 4) * 100);
    drawPolygon(
      ctx,
      gridValues,
      radius,
      centerX,
      centerY,
      "rgba(174, 135, 111, 0.18)",
      "rgba(0,0,0,0)",
    );
  }

  dimensions.forEach((item, index) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / dimensions.length;
    const edgePoint = pointAt(centerX, centerY, radius, angle, 100);
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(edgePoint.x, edgePoint.y);
    ctx.setStrokeStyle("rgba(174, 135, 111, 0.18)");
    ctx.setLineWidth(1);
    ctx.stroke();

    const labelPoint = pointAt(centerX, centerY, radius + 20, angle, 100);
    ctx.setFillStyle("#7c6351");
    ctx.setFontSize(12);
    ctx.setTextAlign("center");
    ctx.fillText(item.dim_code.toUpperCase(), labelPoint.x, labelPoint.y);
  });

  drawPolygon(
    ctx,
    dimensions.map((item) => item.initiator_score),
    radius,
    centerX,
    centerY,
    "#d96f3d",
    "rgba(217,111,61,0.24)",
  );
  drawPolygon(
    ctx,
    dimensions.map((item) => item.partner_score),
    radius,
    centerX,
    centerY,
    "#6b91d9",
    "rgba(107,145,217,0.22)",
  );
  ctx.draw();
}

onMounted(() => {
  void nextTick(() => {
    drawRadar();
  });
});

watch(
  () => props.dimensions,
  () => {
    void nextTick(() => {
      drawRadar();
    });
  },
  { deep: true },
);
</script>

<template>
  <view class="radar-card">
    <canvas :canvas-id="canvasId" :id="canvasId" class="radar-card__canvas" />
    <view class="radar-card__legend">
      <view class="radar-card__legend-item">
        <text class="radar-card__dot radar-card__dot--warm" />
        <text>我</text>
      </view>
      <view class="radar-card__legend-item">
        <text class="radar-card__dot radar-card__dot--cool" />
        <text>TA</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.radar-card {
  padding: 18rpx;
  border-radius: 28rpx;
  background: rgba(255, 251, 244, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
}

.radar-card__canvas {
  width: 640rpx;
  height: 640rpx;
}

.radar-card__legend {
  display: flex;
  justify-content: center;
  gap: 28rpx;
  margin-top: 12rpx;
}

.radar-card__legend-item {
  display: flex;
  align-items: center;
  gap: 10rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.radar-card__dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  display: inline-block;
}

.radar-card__dot--warm {
  background: #d96f3d;
}

.radar-card__dot--cool {
  background: #6b91d9;
}
</style>
