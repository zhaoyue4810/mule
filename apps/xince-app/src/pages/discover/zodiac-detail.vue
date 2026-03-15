<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

type FortuneDetail = {
  dateRange: string;
  overall: number;
  metrics: Array<{ label: string; score: number }>;
  luckyNumber: string;
  luckyColor: string;
  luckyDirection: string;
  advice: string;
  bestMatches: Array<{ emoji: string; name: string }>;
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
const ringStyle = computed(() => ({
  background: `conic-gradient(#9B7ED8 0 ${fortune.value.overall}%, rgba(255,255,255,0.55) ${fortune.value.overall}% 100%)`,
}));

function stars(score: number) {
  return Math.max(1, Math.min(5, Math.round(score / 20)));
}

onLoad((options) => {
  zodiacKey.value = typeof options?.key === "string" && options.key ? options.key : "aries";
  zodiacName.value = typeof options?.name === "string" && options.name ? options.name : "白羊";
  zodiacEmoji.value = typeof options?.emoji === "string" && options.emoji ? options.emoji : "♈";
});
</script>

<template>
  <view class="page">
    <view class="shell">
      <view class="hero-card">
        <text class="hero-card__emoji">{{ zodiacEmoji }}</text>
        <text class="hero-card__name">{{ zodiacName }}</text>
        <text class="hero-card__date">{{ fortune.dateRange }}</text>
      </view>

      <view class="card">
        <text class="card__title">今日运势</text>
        <view class="fortune-overview">
          <view class="ring" :style="ringStyle">
            <view class="ring__inner">
              <text class="ring__score">{{ fortune.overall }}</text>
              <text class="ring__label">综合</text>
            </view>
          </view>
          <view class="metrics">
            <view v-for="item in fortune.metrics" :key="item.label" class="metric">
              <view class="metric__head">
                <text class="metric__label">{{ item.label }}</text>
                <text class="metric__value">{{ item.score }}</text>
              </view>
              <view class="metric__bar">
                <view class="metric__fill" :style="{ width: `${item.score}%` }" />
              </view>
              <text class="metric__stars">{{ "★".repeat(stars(item.score)) }}{{ "☆".repeat(5 - stars(item.score)) }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="card">
        <text class="card__title">幸运信息</text>
        <view class="lucky-grid">
          <view class="lucky-item">
            <text class="lucky-item__label">幸运数字</text>
            <text class="lucky-item__value">{{ fortune.luckyNumber }}</text>
          </view>
          <view class="lucky-item">
            <text class="lucky-item__label">幸运颜色</text>
            <text class="lucky-item__value">{{ fortune.luckyColor }}</text>
          </view>
          <view class="lucky-item">
            <text class="lucky-item__label">幸运方位</text>
            <text class="lucky-item__value">{{ fortune.luckyDirection }}</text>
          </view>
        </view>
      </view>

      <view class="card">
        <text class="card__title">今日建议</text>
        <text class="advice">{{ fortune.advice }}</text>
        <view class="match-row">
          <text class="match-row__label">最佳匹配</text>
          <view class="match-row__chips">
            <view v-for="item in fortune.bestMatches" :key="item.name" class="match-chip">
              <text>{{ item.emoji }}</text>
              <text>{{ item.name }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 28rpx 24rpx 56rpx;
  animation: fadeInUp 0.45s $xc-ease both;
  background:
    radial-gradient(circle at top right, rgba(232, 114, 154, 0.12), transparent 26%),
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.18), transparent 30%),
    $xc-bg;
}

.shell {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.hero-card,
.card {
  @include card-base;
}

.hero-card {
  padding: 38rpx 30rpx;
  text-align: center;
  background:
    radial-gradient(circle at top, rgba(255, 244, 214, 0.92), rgba(245, 236, 255, 0.9)),
    linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(248, 242, 255, 0.88));
}

.hero-card__emoji {
  display: block;
  font-size: 88rpx;
}

.hero-card__name {
  display: block;
  margin-top: 12rpx;
  font-size: 42rpx;
  font-weight: 800;
  color: $xc-ink;
}

.hero-card__date {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.card {
  padding: 28rpx;
}

.card__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.fortune-overview {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.ring {
  width: 220rpx;
  height: 220rpx;
  margin: 0 auto;
  border-radius: 50%;
  padding: 14rpx;
}

.ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.ring__score {
  font-size: 56rpx;
  font-weight: 800;
  color: $xc-purple-d;
}

.ring__label {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.metrics {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.metric {
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: rgba(248, 246, 255, 0.9);
}

.metric__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric__label,
.metric__value {
  font-size: 24rpx;
  color: $xc-ink;
}

.metric__value {
  font-weight: 700;
}

.metric__bar {
  margin-top: 12rpx;
  height: 12rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  overflow: hidden;
}

.metric__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, $xc-purple, $xc-pink);
}

.metric__stars {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: $xc-gold;
}

.lucky-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.lucky-item {
  padding: 18rpx 14rpx;
  border-radius: 22rpx;
  background: rgba(248, 246, 255, 0.92);
  text-align: center;
}

.lucky-item__label {
  display: block;
  font-size: 21rpx;
  color: $xc-muted;
}

.lucky-item__value {
  display: block;
  margin-top: 8rpx;
  font-size: 27rpx;
  font-weight: 700;
  color: $xc-ink;
}

.advice {
  display: block;
  margin-top: 18rpx;
  font-size: 25rpx;
  line-height: 1.8;
  color: $xc-muted;
}

.match-row {
  margin-top: 20rpx;
}

.match-row__label {
  display: block;
  font-size: 24rpx;
  font-weight: 700;
  color: $xc-ink;
}

.match-row__chips {
  margin-top: 12rpx;
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
}

.match-chip {
  display: inline-flex;
  align-items: center;
  gap: 10rpx;
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, rgba(237, 229, 249, 0.94), rgba(253, 230, 239, 0.92));
  color: $xc-purple-d;
  font-size: 23rpx;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
