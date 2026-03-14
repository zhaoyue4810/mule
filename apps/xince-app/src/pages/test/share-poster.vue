<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { onLoad, onShareAppMessage, onShareTimeline } from "@dcloudio/uni-app";

import type { MatchCreateResponse } from "@/shared/models/match";
import type { AppReportDetail } from "@/shared/models/reports";
import {
  resolveSharePosterTemplate,
  sharePosterTemplates,
} from "@/shared/config/share-posters";
import { createQrMatrix } from "@/shared/utils/qrcode";
import { createMatchInvite } from "@/shared/services/match";
import { fetchReportDetail } from "@/shared/services/reports";

const report = ref<AppReportDetail | null>(null);
const loading = ref(true);
const error = ref("");
const generating = ref(false);
const posterImageUrl = ref("");
const selectedTemplateId = ref("");
const posterMode = ref<"report" | "challenge">("report");
const challengeInvite = ref<MatchCreateResponse | null>(null);
const challengeLoading = ref(false);
const POSTER_W = 640;
const POSTER_H = 900;

const activeTemplate = computed(() =>
  resolveSharePosterTemplate(selectedTemplateId.value || report.value?.share_card.theme),
);
const shareThemeClass = computed(
  () => `poster poster--${activeTemplate.value.id || "sunset"}`,
);
const posterTitle = computed(() => {
  if (!report.value) {
    return "";
  }
  if (posterMode.value === "challenge") {
    return `来挑战我的「${report.value.test_name}」结果`;
  }
  return report.value.share_card.title;
});
const posterSubtitle = computed(() => {
  if (!report.value) {
    return "";
  }
  if (posterMode.value === "challenge") {
    return `${report.value.test_name} · 好友挑战`;
  }
  return report.value.share_card.subtitle;
});
const posterShareText = computed(() => {
  if (!report.value) {
    return "";
  }
  if (posterMode.value === "challenge" && challengeInvite.value) {
    return challengeInvite.value.share_message;
  }
  return report.value.share_card.share_text;
});

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

async function ensureChallengeInvite() {
  if (!report.value || challengeInvite.value || challengeLoading.value) {
    return challengeInvite.value;
  }
  challengeLoading.value = true;
  try {
    challengeInvite.value = await createMatchInvite(report.value.test_code);
    posterImageUrl.value = "";
    return challengeInvite.value;
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "挑战邀请创建失败",
      icon: "none",
    });
    return null;
  } finally {
    challengeLoading.value = false;
  }
}

async function setPosterMode(mode: "report" | "challenge") {
  posterMode.value = mode;
  posterImageUrl.value = "";
  if (mode === "challenge") {
    await ensureChallengeInvite();
  }
}

function setTemplate(templateId: string) {
  if (selectedTemplateId.value === templateId) {
    return;
  }
  selectedTemplateId.value = templateId;
  posterImageUrl.value = "";
}

async function copyShareText() {
  if (!posterShareText.value) {
    return;
  }
  try {
    await uni.setClipboardData({
      data: posterShareText.value,
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

function wrapText(
  ctx: UniApp.CanvasContext,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number,
  maxLines: number,
) {
  if (!text) {
    return;
  }
  let line = "";
  let lineIndex = 0;
  for (const char of text) {
    const testLine = `${line}${char}`;
    const { width } = ctx.measureText(testLine);
    if (width > maxWidth && line) {
      ctx.fillText(line, x, y + lineIndex * lineHeight);
      line = char;
      lineIndex += 1;
      if (lineIndex >= maxLines - 1) {
        break;
      }
    } else {
      line = testLine;
    }
  }
  if (lineIndex < maxLines) {
    const suffix = lineIndex === maxLines - 1 && line.length < text.length ? "..." : "";
    ctx.fillText(`${line}${suffix}`, x, y + lineIndex * lineHeight);
  }
}

function drawQrBlock(
  ctx: UniApp.CanvasContext,
  x: number,
  y: number,
  size: number,
  content: string,
) {
  const qr = createQrMatrix(content);
  const padding = 12;
  const cell = (size - padding * 2) / qr.size;
  ctx.setFillStyle("#ffffff");
  drawRoundedRect(ctx, x, y, size, size, 20);
  for (let row = 0; row < qr.size; row += 1) {
    for (let col = 0; col < qr.size; col += 1) {
      if (!qr.modules[row][col]) {
        continue;
      }
      ctx.setFillStyle("#1f1711");
      ctx.fillRect(
        x + padding + col * cell,
        y + padding + row * cell,
        Math.ceil(cell),
        Math.ceil(cell),
      );
    }
  }
}

async function generatePosterImage() {
  if (!report.value || generating.value) {
    return;
  }
  if (posterMode.value === "challenge") {
    await ensureChallengeInvite();
    if (!challengeInvite.value) {
      return;
    }
  }

  generating.value = true;
  try {
    await nextTick();
    const ctx = uni.createCanvasContext("posterCanvas");
    const theme = activeTemplate.value;

    const personaEmoji = report.value.persona?.persona_name?.includes("星")
      ? "🌟"
      : report.value.persona?.persona_name?.includes("月")
        ? "🌙"
        : "✨";

    const grd = ctx.createLinearGradient(0, 0, POSTER_W, POSTER_H);
    grd.addColorStop(0, "#9B7ED8");
    grd.addColorStop(0.55, "#E8729A");
    grd.addColorStop(1, "#F2A68B");
    ctx.setFillStyle(grd);
    ctx.fillRect(0, 0, POSTER_W, POSTER_H);

    ctx.setFillStyle("rgba(255,255,255,0.94)");
    drawRoundedRect(ctx, 26, 24, POSTER_W - 52, POSTER_H - 48, 26);

    ctx.setFillStyle(theme.accent);
    ctx.setFontSize(18);
    ctx.fillText(posterMode.value === "challenge" ? "好友挑战" : "报告分享", 48, 58);
    ctx.setFillStyle("#3A2E42");
    ctx.setFontSize(26);
    wrapText(ctx, report.value.test_name, 48, 92, 380, 34, 1);
    ctx.setFillStyle(theme.secondary);
    ctx.setFontSize(22);
    ctx.fillText(personaEmoji, 48, 132);
    wrapText(ctx, report.value.persona.persona_name || "灵魂旅人", 78, 132, 260, 30, 1);

    ctx.setFillStyle("rgba(155,126,216,0.08)");
    drawRoundedRect(ctx, 46, 152, 548, 206, 18);
    ctx.setFillStyle("#3A2E42");
    ctx.setFontSize(20);
    wrapText(ctx, posterTitle.value, 64, 184, 512, 30, 2);

    const radarDims = report.value.radar_dimensions.slice(0, 5);
    const cx = 150;
    const cy = 278;
    const radius = 64;
    const pointAt = (angle: number, value: number) => ({
      x: cx + Math.cos(angle) * radius * Math.max(0, Math.min(1, value)),
      y: cy + Math.sin(angle) * radius * Math.max(0, Math.min(1, value)),
    });
    for (let ring = 1; ring <= 3; ring += 1) {
      ctx.beginPath();
      radarDims.forEach((_, index) => {
        const angle = -Math.PI / 2 + (Math.PI * 2 * index) / radarDims.length;
        const p = pointAt(angle, ring / 3);
        if (index === 0) {
          ctx.moveTo(p.x, p.y);
        } else {
          ctx.lineTo(p.x, p.y);
        }
      });
      ctx.closePath();
      ctx.setStrokeStyle("rgba(155,126,216,0.22)");
      ctx.stroke();
    }
    ctx.beginPath();
    radarDims.forEach((item, index) => {
      const angle = -Math.PI / 2 + (Math.PI * 2 * index) / radarDims.length;
      const p = pointAt(angle, item.normalized_score || 0);
      if (index === 0) {
        ctx.moveTo(p.x, p.y);
      } else {
        ctx.lineTo(p.x, p.y);
      }
    });
    ctx.closePath();
    ctx.setStrokeStyle("#9B7ED8");
    ctx.setFillStyle("rgba(155,126,216,0.24)");
    ctx.stroke();
    ctx.fill();

    const bars = report.value.share_card.stat_chips.slice(0, 3);
    let barY = 216;
    bars.forEach((item) => {
      ctx.setFillStyle("rgba(155,126,216,0.12)");
      drawRoundedRect(ctx, 268, barY, 300, 22, 11);
      ctx.setFillStyle(theme.accent);
      drawRoundedRect(ctx, 268, barY, Math.max(90, Math.min(300, item.length * 18)), 22, 11);
      ctx.setFillStyle("#3A2E42");
      ctx.setFontSize(18);
      ctx.fillText(item, 272, barY + 44);
      barY += 58;
    });

    ctx.setFillStyle(theme.panel);
    drawRoundedRect(ctx, 46, 380, 548, 210, 18);
    ctx.setFillStyle("#3A2E42");
    ctx.setFontSize(20);
    if (posterMode.value === "challenge" && challengeInvite.value) {
      wrapText(ctx, "我已经完成这套测试，来看看我们有多默契。", 64, 414, 340, 32, 3);
      ctx.setFillStyle(theme.accent);
      ctx.setFontSize(26);
      ctx.fillText(`邀请码 ${challengeInvite.value.invite_code}`, 64, 542);
    } else {
      wrapText(ctx, report.value.share_card.highlight_lines.join(" · "), 64, 414, 340, 32, 4);
    }

    ctx.setFillStyle("rgba(255,255,255,0.95)");
    drawRoundedRect(ctx, 428, 404, 148, 148, 14);
    if (posterMode.value === "challenge" && challengeInvite.value) {
      drawQrBlock(ctx, 440, 416, 124, challengeInvite.value.invite_link || challengeInvite.value.invite_code);
    } else {
      ctx.setFillStyle("rgba(58,46,66,0.28)");
      ctx.setFontSize(16);
      ctx.fillText("二维码", 474, 488);
    }

    ctx.setFillStyle("rgba(58,46,66,0.74)");
    ctx.setFontSize(18);
    wrapText(ctx, report.value.share_card.footer, 46, 636, 548, 28, 2);
    ctx.setFillStyle("rgba(58,46,66,0.45)");
    ctx.setFontSize(16);
    ctx.fillText("心测 XinCe", 46, 680);
    ctx.fillText("灵魂说明书", 122, 680);
    if (posterMode.value === "challenge") {
      ctx.setFillStyle("rgba(232,114,154,0.22)");
      drawRoundedRect(ctx, 430, 646, 164, 36, 18);
      ctx.setFillStyle("#E8729A");
      ctx.setFontSize(18);
      ctx.fillText("挑战模式", 476, 670);
    }

    await new Promise<void>((resolve) => {
      ctx.draw(false, () => resolve());
    });

    const tempPath = await new Promise<string>((resolve, reject) => {
      uni.canvasToTempFilePath(
        {
          canvasId: "posterCanvas",
          width: POSTER_W,
          height: POSTER_H,
          destWidth: POSTER_W * 2,
          destHeight: POSTER_H * 2,
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

async function loadReport(recordId: number, mode: "report" | "challenge") {
  loading.value = true;
  error.value = "";
  try {
    report.value = await fetchReportDetail(recordId);
    selectedTemplateId.value = report.value.share_card.theme;
    if (mode === "challenge") {
      await setPosterMode("challenge");
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "报告加载失败";
  } finally {
    loading.value = false;
  }
}

onLoad((query) => {
  const recordId =
    query && typeof query.recordId === "string" ? Number(query.recordId) : 0;
  const mode =
    query && query.mode === "challenge" ? "challenge" : "report";
  if (!recordId) {
    error.value = "缺少 recordId 参数";
    loading.value = false;
    return;
  }
  loadReport(recordId, mode);
});

onShareAppMessage(() => ({
  title:
    posterMode.value === "challenge"
      ? `${report.value?.test_name || "心测"} 挑战邀请`
      : `${report.value?.test_name || "心测"} 报告分享`,
  path:
    posterMode.value === "challenge" && challengeInvite.value
      ? `/pages/match/invite?code=${challengeInvite.value.invite_code}`
      : `/pages/test/share-poster?recordId=${report.value?.record_id || 0}`,
}));

onShareTimeline(() => ({
  title:
    posterMode.value === "challenge"
      ? `${report.value?.test_name || "心测"} 挑战邀请`
      : `${report.value?.test_name || "心测"} 报告分享`,
  query:
    posterMode.value === "challenge" && challengeInvite.value
      ? `code=${challengeInvite.value.invite_code}`
      : `recordId=${report.value?.record_id || 0}`,
}));
</script>

<template>
  <view class="page">
    <view v-if="loading" class="panel">
      <text class="panel__text">正在准备海报素材...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__title">海报加载失败</text>
      <text class="panel__text">{{ error }}</text>
    </view>

    <view v-else-if="report" class="stack">
      <view class="toolbar">
        <button class="toolbar__back" @tap="backResult">返回报告</button>
        <text class="toolbar__title">分享海报</text>
      </view>

      <view class="selector">
        <button
          class="selector__button"
          :class="{ 'selector__button--active': posterMode === 'report' }"
          @tap="setPosterMode('report')"
        >
          报告分享
        </button>
        <button
          class="selector__button"
          :class="{ 'selector__button--active': posterMode === 'challenge' }"
          @tap="setPosterMode('challenge')"
        >
          好友挑战
        </button>
      </view>

      <scroll-view scroll-x class="template-tabs">
        <view class="template-tabs__list">
          <button
            v-for="template in sharePosterTemplates"
            :key="template.id"
            class="template-tabs__item"
            :class="{ 'template-tabs__item--active': activeTemplate.id === template.id }"
            @tap="setTemplate(template.id)"
          >
            {{ template.name }}
          </button>
        </view>
      </scroll-view>

      <view class="poster-wrap">
        <view class="poster-preview" :class="shareThemeClass">
          <text class="poster-preview__eyebrow">{{ posterSubtitle }}</text>
          <text class="poster-preview__title">{{ posterTitle }}</text>
          <text class="poster-preview__accent">
            {{ posterMode === "challenge" ? "挑战邀请已开启" : `主导标签：${report.share_card.accent}` }}
          </text>
          <view class="poster-preview__chips">
            <text
              v-for="chip in report.share_card.stat_chips"
              :key="chip"
              class="poster-preview__chip"
            >
              {{ chip }}
            </text>
          </view>
          <view class="poster-preview__panel">
            <template v-if="posterMode === 'challenge'">
              <text class="poster-preview__line">
                {{ challengeInvite?.share_message || "生成挑战邀请后，这里会显示邀请码与扫码入口。" }}
              </text>
              <view class="poster-preview__qr">
                <text class="poster-preview__qr-text">
                  {{ challengeInvite?.invite_code || (challengeLoading ? "生成中..." : "待生成") }}
                </text>
              </view>
            </template>
            <template v-else>
              <text
                v-for="line in report.share_card.highlight_lines"
                :key="line"
                class="poster-preview__line"
              >
                {{ line }}
              </text>
            </template>
          </view>
          <text class="poster-preview__footer">
            {{ posterMode === "challenge" ? "扫描海报二维码即可直达匹配邀请页" : report.share_card.footer }}
          </text>
        </view>
      </view>

      <view class="actions">
        <button class="actions__primary" :loading="generating" @tap="generatePosterImage">
          {{ generating ? "生成中..." : "生成海报图片" }}
        </button>
        <button class="actions__secondary" @tap="copyShareText">复制文案</button>
        <button class="actions__secondary" @tap="previewPosterImage">预览图片</button>
        <button class="actions__secondary" @tap="savePosterImage">保存图片</button>
        <!-- #ifdef MP-WEIXIN -->
        <button class="actions__secondary" open-type="share">分享到微信</button>
        <!-- #endif -->
      </view>
      <canvas
        canvas-id="posterCanvas"
        id="posterCanvas"
        class="poster-canvas"
        style="width: 640px; height: 900px"
      />
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  padding: 24rpx 24rpx 40rpx;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.panel,
.toolbar,
.selector,
.poster-wrap,
.actions {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 252, 247, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  box-shadow: $xc-shadow;
}

.panel--error {
  background: rgba(255, 240, 235, 0.96);
}

.panel__title,
.toolbar__title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
}

.panel__text {
  display: block;
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar__back {
  min-width: 160rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.1);
  color: $xc-accent;
  font-size: 24rpx;
}

.selector {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.selector__button,
.template-tabs__item {
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.1);
  color: $xc-accent;
  font-size: 24rpx;
}

.selector__button--active,
.template-tabs__item--active {
  background: linear-gradient(135deg, #9B7ED8, #7C5DBF);
  color: #FBF7F4;
}

.template-tabs__list {
  display: flex;
  gap: 12rpx;
}

.template-tabs__item {
  min-width: 140rpx;
}

.poster-preview {
  min-height: 860rpx;
  padding: 36rpx 32rpx;
  border-radius: 30rpx;
  color: #3A2E42;
}

.poster--sunset {
  background: linear-gradient(160deg, #ffd8c0, #ffb684);
}

.poster--aurora {
  background: linear-gradient(160deg, #d6f6e5, #9ed9c0);
}

.poster--nightfall {
  background: linear-gradient(160deg, #dfe6ff, #b9c5ff);
}

.poster-preview__eyebrow,
.poster-preview__footer {
  display: block;
  font-size: 24rpx;
  color: rgba(58, 46, 66, 0.68);
}

.poster-preview__title {
  display: block;
  margin-top: 18rpx;
  font-size: 44rpx;
  font-weight: 700;
  line-height: 1.35;
}

.poster-preview__accent {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
}

.poster-preview__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 22rpx;
}

.poster-preview__chip {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  font-size: 22rpx;
}

.poster-preview__panel {
  margin-top: 24rpx;
  padding: 26rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.78);
  min-height: 360rpx;
}

.poster-preview__line {
  display: block;
  font-size: 26rpx;
  line-height: 1.8;
  color: rgba(58, 46, 66, 0.82);
}

.poster-preview__line + .poster-preview__line {
  margin-top: 16rpx;
}

.poster-preview__qr {
  width: 220rpx;
  height: 220rpx;
  margin: 26rpx auto 0;
  border-radius: 24rpx;
  background:
    linear-gradient(45deg, rgba(58, 46, 66, 0.9) 25%, transparent 25%) -12rpx 0/24rpx 24rpx,
    linear-gradient(-45deg, rgba(58, 46, 66, 0.9) 25%, transparent 25%) -12rpx 0/24rpx 24rpx,
    linear-gradient(45deg, transparent 75%, rgba(58, 46, 66, 0.9) 75%) -12rpx 0/24rpx 24rpx,
    linear-gradient(-45deg, transparent 75%, rgba(58, 46, 66, 0.9) 75%) -12rpx 0/24rpx 24rpx,
    #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.poster-preview__qr-text {
  width: 160rpx;
  font-size: 26rpx;
  font-weight: 700;
}

.poster-preview__footer {
  margin-top: 24rpx;
}

.actions {
  display: grid;
  gap: 12rpx;
}

.actions__primary,
.actions__secondary {
  border-radius: 18rpx;
}

.actions__primary {
  background: linear-gradient(135deg, #9B7ED8, #7C5DBF);
  color: #FBF7F4;
}

.actions__secondary {
  background: rgba(255, 245, 235, 0.96);
  color: $xc-ink;
}

.poster-canvas {
  position: fixed;
  left: -9999px;
  top: -9999px;
  pointer-events: none;
}
</style>
