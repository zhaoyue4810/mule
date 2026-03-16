<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

type FortuneMetric = { label: string; score: number };
type BestMatch = { emoji: string; name: string };
type FortuneDetail = {
  dateRange: string;
  overall: number;
  metrics: FortuneMetric[];
  luckyNumber: string;
  luckyColor: string;
  luckyDirection: string;
  advice: string;
  bestMatches: BestMatch[];
};

const fortuneMap: Record<string, FortuneDetail> = {
  aries: {
    dateRange: "3.21 - 4.19",
    overall: 86,
    metrics: [
      { label: "爱情", score: 82 },
      { label: "事业", score: 90 },
      { label: "财富", score: 76 },
      { label: "健康", score: 83 },
      { label: "学业", score: 78 },
    ],
    luckyNumber: "7",
    luckyColor: "晨雾紫",
    luckyDirection: "东南",
    advice: "今天适合主动一点，把已经想清楚的事往前推一步，节奏会比你想象中更顺。",
    bestMatches: [
      { emoji: "♌", name: "狮子" },
      { emoji: "♐", name: "射手" },
    ],
  },
  taurus: {
    dateRange: "4.20 - 5.20",
    overall: 79,
    metrics: [
      { label: "爱情", score: 80 },
      { label: "事业", score: 75 },
      { label: "财富", score: 88 },
      { label: "健康", score: 81 },
      { label: "学业", score: 72 },
    ],
    luckyNumber: "3",
    luckyColor: "奶油金",
    luckyDirection: "正西",
    advice: "给自己一点慢下来的空间，今天的好运更偏向稳定积累，而不是用力冲刺。",
    bestMatches: [
      { emoji: "♍", name: "处女" },
      { emoji: "♑", name: "摩羯" },
    ],
  },
  gemini: {
    dateRange: "5.21 - 6.21",
    overall: 84,
    metrics: [
      { label: "爱情", score: 78 },
      { label: "事业", score: 85 },
      { label: "财富", score: 80 },
      { label: "健康", score: 74 },
      { label: "学业", score: 92 },
    ],
    luckyNumber: "11",
    luckyColor: "流光蓝",
    luckyDirection: "东北",
    advice: "灵感会来得很快，把想到的点子记下来，晚些时候它们会成为很好的突破口。",
    bestMatches: [
      { emoji: "♎", name: "天秤" },
      { emoji: "♒", name: "水瓶" },
    ],
  },
  cancer: {
    dateRange: "6.22 - 7.22",
    overall: 88,
    metrics: [
      { label: "爱情", score: 90 },
      { label: "事业", score: 80 },
      { label: "财富", score: 79 },
      { label: "健康", score: 84 },
      { label: "学业", score: 83 },
    ],
    luckyNumber: "2",
    luckyColor: "月白",
    luckyDirection: "正北",
    advice: "今天你的感受力很准，先相信直觉，再慢慢确认细节，很多关系会因此更靠近。",
    bestMatches: [
      { emoji: "♏", name: "天蝎" },
      { emoji: "♓", name: "双鱼" },
    ],
  },
  leo: {
    dateRange: "7.23 - 8.22",
    overall: 85,
    metrics: [
      { label: "爱情", score: 84 },
      { label: "事业", score: 91 },
      { label: "财富", score: 81 },
      { label: "健康", score: 79 },
      { label: "学业", score: 77 },
    ],
    luckyNumber: "9",
    luckyColor: "琥珀橙",
    luckyDirection: "正南",
    advice: "你今天的感染力很强，适合公开表达想法，也适合带动身边人的节奏。",
    bestMatches: [
      { emoji: "♈", name: "白羊" },
      { emoji: "♐", name: "射手" },
    ],
  },
  virgo: {
    dateRange: "8.23 - 9.22",
    overall: 81,
    metrics: [
      { label: "爱情", score: 74 },
      { label: "事业", score: 88 },
      { label: "财富", score: 82 },
      { label: "健康", score: 86 },
      { label: "学业", score: 85 },
    ],
    luckyNumber: "6",
    luckyColor: "雾灰绿",
    luckyDirection: "西北",
    advice: "把注意力放回可控的小步骤，你会发现今天最强的运气来自细节被照顾好。",
    bestMatches: [
      { emoji: "♉", name: "金牛" },
      { emoji: "♑", name: "摩羯" },
    ],
  },
  libra: {
    dateRange: "9.23 - 10.23",
    overall: 83,
    metrics: [
      { label: "爱情", score: 88 },
      { label: "事业", score: 79 },
      { label: "财富", score: 76 },
      { label: "健康", score: 80 },
      { label: "学业", score: 84 },
    ],
    luckyNumber: "5",
    luckyColor: "玫瑰粉",
    luckyDirection: "西南",
    advice: "今天的人际能量很好，真诚地说出自己的想法，反而能换来更舒服的合作感。",
    bestMatches: [
      { emoji: "♊", name: "双子" },
      { emoji: "♒", name: "水瓶" },
    ],
  },
  scorpio: {
    dateRange: "10.24 - 11.22",
    overall: 87,
    metrics: [
      { label: "爱情", score: 91 },
      { label: "事业", score: 84 },
      { label: "财富", score: 80 },
      { label: "健康", score: 78 },
      { label: "学业", score: 86 },
    ],
    luckyNumber: "13",
    luckyColor: "深莓紫",
    luckyDirection: "正东",
    advice: "你的洞察会在今天特别清晰，适合做判断，也适合把暧昧不清的事说透一点。",
    bestMatches: [
      { emoji: "♋", name: "巨蟹" },
      { emoji: "♓", name: "双鱼" },
    ],
  },
  sagittarius: {
    dateRange: "11.23 - 12.21",
    overall: 84,
    metrics: [
      { label: "爱情", score: 79 },
      { label: "事业", score: 83 },
      { label: "财富", score: 78 },
      { label: "健康", score: 85 },
      { label: "学业", score: 90 },
    ],
    luckyNumber: "14",
    luckyColor: "晴空蓝",
    luckyDirection: "东南",
    advice: "今天适合把视野放远一点，多和新鲜的人事物接触，灵感会在途中自己出现。",
    bestMatches: [
      { emoji: "♈", name: "白羊" },
      { emoji: "♌", name: "狮子" },
    ],
  },
  capricorn: {
    dateRange: "12.22 - 1.19",
    overall: 82,
    metrics: [
      { label: "爱情", score: 72 },
      { label: "事业", score: 92 },
      { label: "财富", score: 87 },
      { label: "健康", score: 80 },
      { label: "学业", score: 81 },
    ],
    luckyNumber: "4",
    luckyColor: "岩灰",
    luckyDirection: "正北",
    advice: "保持原本的稳，会让今天很多事自然对齐。你不需要额外证明，持续推进就够了。",
    bestMatches: [
      { emoji: "♉", name: "金牛" },
      { emoji: "♍", name: "处女" },
    ],
  },
  aquarius: {
    dateRange: "1.20 - 2.18",
    overall: 86,
    metrics: [
      { label: "爱情", score: 77 },
      { label: "事业", score: 88 },
      { label: "财富", score: 79 },
      { label: "健康", score: 82 },
      { label: "学业", score: 91 },
    ],
    luckyNumber: "17",
    luckyColor: "冰川蓝",
    luckyDirection: "东北",
    advice: "你的想法很新，别急着先否定自己。先把脑海里的轮廓说出来，它会慢慢变清楚。",
    bestMatches: [
      { emoji: "♊", name: "双子" },
      { emoji: "♎", name: "天秤" },
    ],
  },
  pisces: {
    dateRange: "2.19 - 3.20",
    overall: 89,
    metrics: [
      { label: "爱情", score: 92 },
      { label: "事业", score: 78 },
      { label: "财富", score: 75 },
      { label: "健康", score: 83 },
      { label: "学业", score: 84 },
    ],
    luckyNumber: "12",
    luckyColor: "海盐白",
    luckyDirection: "西南",
    advice: "今天的温柔会成为你的好运来源，先照顾好自己的感受，再去回应世界也不迟。",
    bestMatches: [
      { emoji: "♋", name: "巨蟹" },
      { emoji: "♏", name: "天蝎" },
    ],
  },
};

const zodiacKey = ref("aries");
const zodiacName = ref("白羊");
const zodiacEmoji = ref("♈");

const fortune = computed(() => fortuneMap[zodiacKey.value] || fortuneMap.aries);
const strongestMetric = computed(
  () => fortune.value.metrics.slice().sort((a, b) => b.score - a.score)[0] || fortune.value.metrics[0],
);
const growthMetric = computed(
  () => fortune.value.metrics.slice().sort((a, b) => a.score - b.score)[0] || fortune.value.metrics[0],
);
const toneLabel = computed(() => {
  const score = fortune.value.overall;
  if (score >= 88) {
    return "高能顺风日";
  }
  if (score >= 82) {
    return "稳定发光日";
  }
  return "适合慢推进";
});
const energyMessage = computed(() => {
  if (strongestMetric.value.label === "事业" || strongestMetric.value.label === "学业") {
    return "今天适合把注意力放在推进目标和清晰表达上。";
  }
  if (strongestMetric.value.label === "爱情") {
    return "今天的人际和亲密关系更容易出现正反馈。";
  }
  return "今天更适合稳住自己的节奏，先把状态养好。";
});
const ringStyle = computed(() => ({
  background: `conic-gradient(#fff3bf 0 ${fortune.value.overall * 3.6}deg, rgba(255,255,255,0.12) 0)`,
}));
const insightCards = computed(() => [
  {
    eyebrow: "Today's Peak",
    title: `${strongestMetric.value.label}能量最强`,
    body: `当前分数 ${strongestMetric.value.score}，是今天最值得主动放大的优势区。`,
  },
  {
    eyebrow: "Growth Note",
    title: `${growthMetric.value.label}适合放慢一点`,
    body: `分数 ${growthMetric.value.score}，先降低预期、减少内耗，状态反而会更稳。`,
  },
  {
    eyebrow: "Mood Forecast",
    title: toneLabel.value,
    body: energyMessage.value,
  },
]);
const luckyCards = computed(() => [
  { label: "幸运数字", value: fortune.value.luckyNumber, icon: "#" },
  { label: "幸运颜色", value: fortune.value.luckyColor, icon: "◐" },
  { label: "幸运方位", value: fortune.value.luckyDirection, icon: "↗" },
]);

function stars(score: number) {
  return Math.max(1, Math.min(5, Math.round(score / 20)));
}

function goBack() {
  uni.navigateBack();
}

onLoad((options) => {
  zodiacKey.value = typeof options?.key === "string" && options.key ? options.key : "aries";
  zodiacName.value = typeof options?.name === "string" && options.name ? options.name : "白羊";
  zodiacEmoji.value = typeof options?.emoji === "string" && options.emoji ? options.emoji : "♈";
});
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--gold" />
    <view class="page__mesh" />

    <view class="page__content">
      <view class="hero">
        <button class="hero__back" @tap="goBack">返回</button>

        <view class="hero__topline">
          <text class="hero__eyebrow">DAILY ZODIAC</text>
          <text class="hero__badge">{{ toneLabel }}</text>
        </view>

        <view class="hero__body">
          <view class="hero__identity">
            <text class="hero__emoji">{{ zodiacEmoji }}</text>
            <view class="hero__copy">
              <text class="hero__name">{{ zodiacName }}</text>
              <text class="hero__date">{{ fortune.dateRange }}</text>
              <text class="hero__desc">{{ energyMessage }}</text>
            </view>
          </view>

          <view class="score-dial" :style="ringStyle">
            <view class="score-dial__inner">
              <text class="score-dial__value">{{ fortune.overall }}</text>
              <text class="score-dial__label">综合运势</text>
            </view>
          </view>
        </view>

        <view class="hero__tags">
          <text class="hero-tag">主升维度 {{ strongestMetric.label }}</text>
          <text class="hero-tag">建议慢放 {{ growthMetric.label }}</text>
          <text class="hero-tag">最佳匹配 {{ fortune.bestMatches.map((item) => item.name).join(" / ") }}</text>
        </view>
      </view>

      <view class="surface-card insight-panel">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Energy Snapshot</text>
            <text class="section-head__title">今天适合怎么过</text>
          </view>
        </view>

        <view class="insight-grid">
          <view v-for="item in insightCards" :key="item.title" class="insight-card">
            <text class="insight-card__eyebrow">{{ item.eyebrow }}</text>
            <text class="insight-card__title">{{ item.title }}</text>
            <text class="insight-card__body">{{ item.body }}</text>
          </view>
        </view>
      </view>

      <view class="surface-card metrics-panel">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Metric Board</text>
            <text class="section-head__title">分项运势</text>
          </view>
          <text class="section-head__meta">五星与分值同步显示</text>
        </view>

        <view class="metric-list">
          <view v-for="item in fortune.metrics" :key="item.label" class="metric-card">
            <view class="metric-card__row">
              <text class="metric-card__label">{{ item.label }}</text>
              <text class="metric-card__value">{{ item.score }}</text>
            </view>
            <view class="metric-card__bar">
              <view class="metric-card__fill" :style="{ width: `${item.score}%` }" />
            </view>
            <text class="metric-card__stars">
              {{ "★".repeat(stars(item.score)) }}{{ "☆".repeat(5 - stars(item.score)) }}
            </text>
          </view>
        </view>
      </view>

      <view class="surface-card luck-panel">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Lucky Signals</text>
            <text class="section-head__title">幸运信息</text>
          </view>
        </view>

        <view class="lucky-grid">
          <view v-for="item in luckyCards" :key="item.label" class="lucky-card">
            <text class="lucky-card__icon">{{ item.icon }}</text>
            <text class="lucky-card__label">{{ item.label }}</text>
            <text class="lucky-card__value">{{ item.value }}</text>
          </view>
        </view>
      </view>

      <view class="surface-card advice-panel">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Advice</text>
            <text class="section-head__title">今日建议</text>
          </view>
        </view>

        <text class="advice-panel__text">{{ fortune.advice }}</text>

        <view class="match-strip">
          <text class="match-strip__label">最佳共振星座</text>
          <view class="match-strip__chips">
            <view v-for="item in fortune.bestMatches" :key="item.name" class="match-chip">
              <text class="match-chip__emoji">{{ item.emoji }}</text>
              <text class="match-chip__name">{{ item.name }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.26), transparent 28%),
    radial-gradient(circle at top right, rgba(255, 228, 179, 0.34), transparent 24%),
    linear-gradient(180deg, #fff8ef 0%, #fffaf6 52%, #fff6f3 100%);
}

.page__glow,
.page__mesh {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.page__glow {
  filter: blur(14px);
  opacity: 0.9;
}

.page__glow--violet {
  background: radial-gradient(circle at 18% 16%, rgba(155, 126, 216, 0.28), transparent 25%);
}

.page__glow--gold {
  background: radial-gradient(circle at 82% 12%, rgba(255, 214, 102, 0.28), transparent 22%);
}

.page__mesh {
  opacity: 0.22;
  background-image:
    linear-gradient(rgba(155, 126, 216, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(155, 126, 216, 0.05) 1px, transparent 1px);
  background-size: 28rpx 28rpx;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.48), transparent 80%);
}

.page__content {
  position: relative;
  z-index: 1;
  padding: 28rpx 24rpx 56rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  animation: fade-in-up 0.45s $xc-ease both;
}

.hero,
.surface-card {
  position: relative;
  overflow: hidden;
  border-radius: 34rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.58);
  box-shadow: 0 24rpx 54rpx rgba(98, 78, 137, 0.12);
}

.hero {
  padding: 28rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.52), transparent 26%),
    linear-gradient(145deg, rgba(121, 89, 192, 0.94), rgba(232, 114, 154, 0.88), rgba(255, 202, 116, 0.86));
  color: #fff9f1;
}

.hero__back {
  width: 132rpx;
  height: 64rpx;
  margin: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  color: #fff9f1;
  font-size: 24rpx;
  line-height: 64rpx;
}

.hero__topline,
.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.hero__topline {
  margin-top: 18rpx;
}

.hero__eyebrow,
.section-head__eyebrow {
  display: block;
  font-size: 20rpx;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.hero__badge {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.18);
  font-size: 22rpx;
}

.hero__body {
  margin-top: 24rpx;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220rpx;
  gap: 22rpx;
  align-items: center;
}

.hero__identity {
  display: flex;
  gap: 20rpx;
  align-items: flex-start;
}

.hero__emoji {
  flex-shrink: 0;
  width: 108rpx;
  height: 108rpx;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.14);
  font-size: 64rpx;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.hero__name {
  display: block;
  font-size: 52rpx;
  font-weight: 800;
}

.hero__date,
.hero__desc {
  display: block;
}

.hero__date {
  margin-top: 8rpx;
  font-size: 22rpx;
  opacity: 0.88;
}

.hero__desc {
  margin-top: 16rpx;
  font-size: 25rpx;
  line-height: 1.7;
  color: rgba(255, 249, 241, 0.92);
}

.score-dial {
  width: 220rpx;
  height: 220rpx;
  border-radius: 50%;
  padding: 14rpx;
  justify-self: end;
}

.score-dial__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(85, 58, 132, 0.54);
  backdrop-filter: blur(20px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-dial__value {
  font-size: 62rpx;
  font-weight: 800;
}

.score-dial__label {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(255, 249, 241, 0.84);
}

.hero__tags {
  margin-top: 24rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.hero-tag {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  font-size: 22rpx;
}

.surface-card {
  padding: 26rpx;
  background: rgba(255, 251, 247, 0.92);
  backdrop-filter: blur(20px);
}

.section-head__eyebrow {
  color: rgba(121, 89, 192, 0.8);
}

.section-head__title {
  display: block;
  margin-top: 8rpx;
  font-size: 34rpx;
  font-weight: 800;
  color: $xc-ink;
}

.section-head__meta {
  flex-shrink: 0;
  font-size: 22rpx;
  color: $xc-muted;
}

.insight-grid,
.metric-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.insight-grid {
  margin-top: 22rpx;
}

.insight-card,
.metric-card,
.lucky-card,
.match-chip {
  border-radius: 24rpx;
}

.insight-card {
  padding: 22rpx;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.84), rgba(252, 244, 255, 0.92)),
    rgba(255, 255, 255, 0.72);
  border: 2rpx solid rgba(155, 126, 216, 0.1);
}

.insight-card__eyebrow {
  display: block;
  font-size: 19rpx;
  letter-spacing: 3rpx;
  text-transform: uppercase;
  color: rgba(155, 126, 216, 0.82);
}

.insight-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 29rpx;
  font-weight: 700;
  color: $xc-ink;
}

.insight-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.metrics-panel {
  gap: 18rpx;
}

.metric-list {
  margin-top: 22rpx;
}

.metric-card {
  padding: 20rpx;
  background: rgba(247, 243, 255, 0.88);
}

.metric-card__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric-card__label,
.metric-card__value {
  font-size: 25rpx;
  color: $xc-ink;
}

.metric-card__value {
  font-weight: 800;
}

.metric-card__bar {
  margin-top: 14rpx;
  height: 14rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(155, 126, 216, 0.14);
}

.metric-card__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #9b7ed8, #f3b96f);
}

.metric-card__stars {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #d7a632;
}

.lucky-grid {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.lucky-card {
  padding: 22rpx 16rpx;
  text-align: center;
  background: linear-gradient(180deg, rgba(255, 245, 216, 0.88), rgba(255, 255, 255, 0.9));
}

.lucky-card__icon {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: rgba(121, 89, 192, 0.72);
}

.lucky-card__label {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

.lucky-card__value {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 800;
  color: $xc-ink;
}

.advice-panel__text {
  display: block;
  margin-top: 22rpx;
  font-size: 26rpx;
  line-height: 1.9;
  color: rgba(58, 46, 66, 0.78);
}

.match-strip {
  margin-top: 24rpx;
}

.match-strip__label {
  display: block;
  font-size: 24rpx;
  font-weight: 700;
  color: $xc-ink;
}

.match-strip__chips {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.match-chip {
  display: inline-flex;
  align-items: center;
  gap: 10rpx;
  padding: 12rpx 18rpx;
  background: linear-gradient(145deg, rgba(236, 228, 252, 0.96), rgba(255, 238, 228, 0.92));
  color: $xc-purple-d;
}

.match-chip__emoji {
  font-size: 24rpx;
}

.match-chip__name {
  font-size: 23rpx;
  font-weight: 700;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(18rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
