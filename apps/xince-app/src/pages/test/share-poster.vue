<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import type { AppReportDetail } from "@/shared/models/reports";
import { fetchReportDetail } from "@/shared/services/reports";

const report = ref<AppReportDetail | null>(null);
const loading = ref(true);
const error = ref("");
const generating = ref(false);
const posterImageUrl = ref("");

const shareThemeClass = computed(
  () => `poster poster--${report.value?.share_card.theme || "sunset"}`,
);

function backResult() {
  uni.navigateBack();
}

async function ensurePosterImage() {
  if (posterImageUrl.value) {
    return posterImageUrl.value;
  }
  await generatePosterImage();
  return posterImageUrl.value;
}

async function copyShareText() {
  if (!report.value?.share_card.share_text) {
    return;
  }
  try {
    await uni.setClipboardData({
      data: report.value.share_card.share_text,
    });
    uni.showToast({
      title: "海报文案已复制",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "复制失败",
      icon: "none",
    });
  }
}

async function previewPosterImage() {
  const imageUrl = await ensurePosterImage();
  if (!imageUrl) {
    return;
  }
  uni.previewImage({
    urls: [imageUrl],
    current: imageUrl,
  });
}

async function savePosterImage() {
  const imageUrl = await ensurePosterImage();
  if (!imageUrl) {
    uni.showToast({
      title: "请先生成海报",
      icon: "none",
    });
    return;
  }

  // #ifdef H5
  if (typeof document !== "undefined") {
    const link = document.createElement("a");
    link.href = imageUrl;
    link.download = `xince-poster-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    uni.showToast({
      title: "图片下载已触发",
      icon: "success",
    });
    return;
  }
  // #endif

  // #ifndef H5
  try {
    await uni.saveImageToPhotosAlbum({
      filePath: imageUrl,
    });
    uni.showToast({
      title: "已保存到相册",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "保存失败",
      icon: "none",
    });
  }
  // #endif
}

function resolvePosterTheme(theme: string) {
  const mapping: Record<string, { background: string; panel: string; accent: string }> = {
    dawn: { background: "#ffd6b4", panel: "#fff4e7", accent: "#d96f3d" },
    aurora: { background: "#ccefd9", panel: "#effcf3", accent: "#2f8b61" },
    ember: { background: "#ffc3a2", panel: "#fff0e8", accent: "#cb6131" },
    nightfall: { background: "#d6ddff", panel: "#f1f4ff", accent: "#5a69c7" },
    sunset: { background: "#ffd7bf", panel: "#fff5ed", accent: "#d96f3d" },
  };
  return mapping[theme] || mapping.sunset;
}

async function generatePosterImage() {
  if (!report.value || generating.value) {
    return;
  }

  generating.value = true;
  try {
    await nextTick();
    const ctx = uni.createCanvasContext("posterCanvas");
    const theme = resolvePosterTheme(report.value.share_card.theme);

    ctx.setFillStyle(theme.background);
    ctx.fillRect(0, 0, 720, 1280);

    ctx.setFillStyle("rgba(255,255,255,0.72)");
    drawRoundedRect(ctx, 36, 36, 648, 1208, 28);

    ctx.setFillStyle(theme.accent);
    ctx.setFontSize(24);
    ctx.fillText(report.value.share_card.badge, 68, 100);

    ctx.setFillStyle("#6f5645");
    ctx.setFontSize(20);
    ctx.fillText("心测 Share Poster", 500, 100);

    ctx.setFillStyle(theme.accent);
    ctx.setFontSize(26);
    ctx.fillText(report.value.share_card.subtitle, 68, 178);

    ctx.setFillStyle("#2b2118");
    ctx.setFontSize(48);
    thisWrapText(ctx, report.value.share_card.title, 68, 250, 584, 64, 2);

    ctx.setFillStyle("#5d483b");
    ctx.setFontSize(24);
    ctx.fillText(`主导标签：${report.value.share_card.accent}`, 68, 386);

    let chipX = 68;
    let chipY = 446;
    ctx.setFontSize(22);
    for (const chip of report.value.share_card.stat_chips) {
      const width = Math.min(220, Math.max(120, chip.length * 24 + 36));
      if (chipX + width > 620) {
        chipX = 68;
        chipY += 58;
      }
      ctx.setFillStyle("rgba(255,255,255,0.78)");
      drawRoundedRect(ctx, chipX, chipY - 28, width, 42, 21);
      ctx.setFillStyle("#4b3a2f");
      ctx.fillText(chip, chipX + 18, chipY);
      chipX += width + 12;
    }

    ctx.setFillStyle(theme.panel);
    drawRoundedRect(ctx, 68, 540, 584, 268, 24);

    ctx.setFillStyle("#2b2118");
    ctx.setFontSize(30);
    let lineY = 602;
    for (const line of report.value.share_card.highlight_lines) {
      thisWrapText(ctx, line, 96, lineY, 528, 48, 2);
      lineY += 78;
    }

    ctx.setFillStyle("#7a6659");
    ctx.setFontSize(22);
    thisWrapText(ctx, report.value.share_card.footer, 68, 1046, 584, 34, 2);
    ctx.setFillStyle("rgba(43,33,24,0.52)");
    ctx.setFontSize(20);
    ctx.fillText("当前为前端生成预览图，后续会补图片导出优化。", 68, 1116);

    await new Promise<void>((resolve) => {
      ctx.draw(false, () => resolve());
    });

    const tempPath = await new Promise<string>((resolve, reject) => {
      uni.canvasToTempFilePath(
        {
          canvasId: "posterCanvas",
          width: 720,
          height: 1280,
          destWidth: 1080,
          destHeight: 1920,
          success: (res) => resolve(res.tempFilePath),
          fail: reject,
        },
      );
    });

    posterImageUrl.value = tempPath;
    uni.showToast({
      title: "海报图片已生成",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "生成失败",
      icon: "none",
    });
  } finally {
    generating.value = false;
  }
}

function drawRoundedRect(
  ctx: UniApp.CanvasContext,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number,
) {
  const safeRadius = Math.max(0, Math.min(radius, width / 2, height / 2));
  ctx.beginPath();
  ctx.moveTo(x + safeRadius, y);
  ctx.lineTo(x + width - safeRadius, y);
  ctx.arc(x + width - safeRadius, y + safeRadius, safeRadius, -Math.PI / 2, 0);
  ctx.lineTo(x + width, y + height - safeRadius);
  ctx.arc(x + width - safeRadius, y + height - safeRadius, safeRadius, 0, Math.PI / 2);
  ctx.lineTo(x + safeRadius, y + height);
  ctx.arc(x + safeRadius, y + height - safeRadius, safeRadius, Math.PI / 2, Math.PI);
  ctx.lineTo(x, y + safeRadius);
  ctx.arc(x + safeRadius, y + safeRadius, safeRadius, Math.PI, Math.PI * 1.5);
  ctx.closePath();
  ctx.fill();
}

function thisWrapText(
  ctx: UniApp.CanvasContext,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines: number,
) {
  const chars = text.split("");
  let current = "";
  let currentY = y;
  let lineCount = 0;

  for (let index = 0; index < chars.length; index += 1) {
    const next = current + chars[index];
    if (ctx.measureText(next).width > maxWidth && current) {
      lineCount += 1;
      ctx.fillText(current, x, currentY);
      current = chars[index];
      currentY += lineHeight;
      if (lineCount >= maxLines - 1) {
        break;
      }
      continue;
    }
    current = next;
  }

  if (current) {
    if (lineCount >= maxLines - 1 && chars.join("") !== current) {
      const safeText = current.length > 1 ? `${current.slice(0, -1)}...` : `${current}...`;
      ctx.fillText(safeText, x, currentY);
      return;
    }
    ctx.fillText(current, x, currentY);
  }
}

async function loadPoster(recordId: number) {
  loading.value = true;
  error.value = "";
  try {
    report.value = await fetchReportDetail(recordId);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "海报加载失败";
  } finally {
    loading.value = false;
  }
}

onLoad((query) => {
  const recordId =
    query && typeof query.recordId === "string" ? Number(query.recordId) : 0;
  if (!recordId) {
    error.value = "缺少 recordId 参数";
    loading.value = false;
    return;
  }
  loadPoster(recordId);
});
</script>

<template>
  <view class="page">
    <view v-if="loading" class="state-card">
      <text class="state-card__text">正在生成海报预览...</text>
    </view>

    <view v-else-if="error" class="state-card state-card--error">
      <text class="state-card__text">{{ error }}</text>
    </view>

    <view v-else-if="report" class="poster-page">
      <view :class="shareThemeClass">
        <view class="poster__top">
          <text class="poster__badge">{{ report.share_card.badge }}</text>
          <text class="poster__brand">心测 Share Poster</text>
        </view>

        <view class="poster__hero">
          <text class="poster__subtitle">{{ report.share_card.subtitle }}</text>
          <text class="poster__title">{{ report.share_card.title }}</text>
          <text class="poster__accent">主导标签：{{ report.share_card.accent }}</text>
        </view>

        <view class="poster__chips">
          <text
            v-for="chip in report.share_card.stat_chips"
            :key="chip"
            class="poster__chip"
          >
            {{ chip }}
          </text>
        </view>

        <view class="poster__summary">
          <text
            v-for="line in report.share_card.highlight_lines"
            :key="line"
            class="poster__line"
          >
            {{ line }}
          </text>
        </view>

        <view class="poster__footer">
          <text class="poster__footer-text">{{ report.share_card.footer }}</text>
          <text class="poster__footer-note">建议长按截图保存，后续会接正式图片导出。</text>
        </view>
      </view>

      <view class="actions">
        <button class="actions__ghost" @tap="backResult">返回报告</button>
        <button class="actions__primary" @tap="copyShareText">复制海报文案</button>
      </view>

      <view class="actions">
        <button class="actions__primary" :disabled="generating" @tap="generatePosterImage">
          {{ generating ? "生成中..." : "生成图片预览" }}
        </button>
        <button class="actions__ghost" @tap="previewPosterImage">预览大图</button>
      </view>

      <view v-if="posterImageUrl" class="export-panel">
        <text class="export-panel__title">导出预览</text>
        <text class="export-panel__body">当前已经支持预览与保存图片，后续再补更完整的渠道分享和模板配置。</text>
        <image class="export-panel__image" :src="posterImageUrl" mode="widthFix" />
        <view class="actions actions--single">
          <button class="actions__primary" @tap="savePosterImage">保存图片</button>
        </view>
      </view>

      <canvas class="poster-canvas" canvas-id="posterCanvas" />
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  padding: 28rpx;
}

.poster-page {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.state-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid rgba(43, 33, 24, 0.06);
}

.state-card--error {
  background: rgba(255, 240, 235, 0.92);
}

.state-card__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.poster {
  min-height: 980rpx;
  padding: 34rpx 30rpx;
  border-radius: 34rpx;
  border: 2rpx solid rgba(43, 33, 24, 0.08);
  box-shadow: $xc-shadow;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 28rpx;
}

.poster--dawn {
  background:
    radial-gradient(circle at top right, rgba(255, 247, 230, 0.98), rgba(255, 206, 171, 0.9)),
    linear-gradient(145deg, #fff1df, #ffc8a4);
}

.poster--aurora {
  background:
    radial-gradient(circle at top right, rgba(242, 255, 246, 0.98), rgba(189, 247, 214, 0.92)),
    linear-gradient(145deg, #ebfff2, #b9efcf);
}

.poster--ember {
  background:
    radial-gradient(circle at top right, rgba(255, 245, 240, 0.98), rgba(255, 188, 152, 0.92)),
    linear-gradient(145deg, #fff0e8, #ffb48f);
}

.poster--nightfall {
  background:
    radial-gradient(circle at top right, rgba(243, 246, 255, 0.98), rgba(207, 218, 255, 0.92)),
    linear-gradient(145deg, #eef2ff, #c7d2ff);
}

.poster--sunset {
  background:
    radial-gradient(circle at top right, rgba(255, 238, 214, 0.98), rgba(255, 219, 189, 0.92)),
    linear-gradient(145deg, #fff7ef, #ffd7bf);
}

.poster__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.poster__badge {
  display: inline-flex;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.68);
  color: $xc-accent;
  font-size: 22rpx;
}

.poster__brand {
  font-size: 20rpx;
  color: rgba(43, 33, 24, 0.62);
}

.poster__hero {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.poster__subtitle {
  font-size: 24rpx;
  color: $xc-accent;
}

.poster__title {
  font-size: 52rpx;
  line-height: 1.2;
  font-weight: 700;
  color: $xc-ink;
}

.poster__accent {
  font-size: 24rpx;
  color: rgba(43, 33, 24, 0.72);
}

.poster__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.poster__chip {
  display: inline-flex;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.62);
  font-size: 22rpx;
  color: rgba(43, 33, 24, 0.82);
}

.poster__summary {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.52);
  backdrop-filter: blur(10rpx);
}

.poster__line {
  font-size: 30rpx;
  line-height: 1.6;
  color: $xc-ink;
}

.poster__footer {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.poster__footer-text {
  font-size: 22rpx;
  color: rgba(43, 33, 24, 0.7);
}

.poster__footer-note {
  font-size: 20rpx;
  color: rgba(43, 33, 24, 0.56);
}

.actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.actions--single {
  grid-template-columns: 1fr;
  margin-top: 18rpx;
}

.actions__ghost,
.actions__primary {
  border-radius: 999rpx;
}

.actions__ghost {
  background: rgba(255, 255, 255, 0.88);
  color: $xc-ink;
  border: 2rpx solid rgba(217, 111, 61, 0.12);
}

.actions__primary {
  background: linear-gradient(135deg, #d96f3d, #bf5321);
  color: #fff8f0;
}

.export-panel {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid rgba(43, 33, 24, 0.06);
}

.export-panel__title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
}

.export-panel__body {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.export-panel__image {
  width: 100%;
  margin-top: 18rpx;
  border-radius: 24rpx;
}

.poster-canvas {
  position: fixed;
  left: -9999px;
  top: -9999px;
  width: 720px;
  height: 1280px;
  opacity: 0;
  pointer-events: none;
}
</style>
