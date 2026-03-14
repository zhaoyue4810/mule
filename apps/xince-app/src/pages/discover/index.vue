<script setup lang="ts">
import { computed, ref } from "vue";

import TabBuddy from "@/components/mascot/TabBuddy.vue";

const activeTab = ref<"hot" | "story" | "zodiac">("hot");

// TODO: 接入后端 API
const hotPosts = ref([
  {
    id: 1,
    avatar: "🦊",
    nickname: "阿狐",
    time: "5分钟前",
    content: "做完关系匹配发现我们在「冲突处理」维度差异超大，太准了😂",
    tags: ["关系匹配", "情侣"],
    likes: 126,
    comments: 32,
    shares: 19,
  },
  {
    id: 2,
    avatar: "🐱",
    nickname: "小猫",
    time: "12分钟前",
    content: "今天的每日灵魂提问很戳我，居然一句话说中了最近的状态。",
    tags: ["每日提问", "成长"],
    likes: 89,
    comments: 14,
    shares: 6,
  },
  {
    id: 3,
    avatar: "🦄",
    nickname: "栗子",
    time: "1小时前",
    content: "MBTI 快速版只要几分钟，结果出来后又去测了完整版，差别挺有意思。",
    tags: ["MBTI", "性格测试"],
    likes: 241,
    comments: 55,
    shares: 23,
  },
  {
    id: 4,
    avatar: "🐰",
    nickname: "桃桃",
    time: "2小时前",
    content: "发现页的故事专栏内容好温柔，晚上看完会安心很多。",
    tags: ["发现页", "故事"],
    likes: 67,
    comments: 9,
    shares: 4,
  },
  {
    id: 5,
    avatar: "🐼",
    nickname: "慢慢",
    time: "3小时前",
    content: "最近在用心情日历补签，连续天数终于又拉回来了。",
    tags: ["心情日历", "打卡"],
    likes: 113,
    comments: 22,
    shares: 8,
  },
]);

// TODO: 接入后端 API
const stories = ref([
  {
    id: 1,
    emoji: "🌌",
    title: "高敏感不是脆弱，而是一种更细致的感知力",
    summary: "当我们把“敏感”从缺点转为天赋，它会成为理解自己和他人的桥梁。",
    author: "小测编辑部",
    authorAvatar: "🪄",
    reads: 1208,
    likes: 346,
    gradient: "linear-gradient(135deg,#9B7ED8,#E8729A)",
  },
  {
    id: 2,
    emoji: "🧭",
    title: "为什么你总在关系里退后一步",
    summary: "回避并不代表不在乎，很多时候只是大脑在保护你。",
    author: "心理研究组",
    authorAvatar: "🧠",
    reads: 982,
    likes: 271,
    gradient: "linear-gradient(135deg,#7CC5B2,#9B7ED8)",
  },
  {
    id: 3,
    emoji: "🌙",
    title: "睡前五分钟，和自己的情绪和解",
    summary: "一个轻量夜间复盘练习，帮助你把焦虑感停留在今天。",
    author: "夜读社",
    authorAvatar: "🫧",
    reads: 743,
    likes: 220,
    gradient: "linear-gradient(135deg,#5F4C8A,#9B7ED8)",
  },
  {
    id: 4,
    emoji: "✨",
    title: "人格报告怎么读，才不被标签困住",
    summary: "把类型当作起点而不是终点，你会看到更立体的自己。",
    author: "XinCe Team",
    authorAvatar: "💫",
    reads: 1584,
    likes: 498,
    gradient: "linear-gradient(135deg,#D4A853,#E8729A)",
  },
]);

const zodiacList = [
  { key: "aries", emoji: "♈", name: "白羊", brief: "行动力满格，适合启动计划" },
  { key: "taurus", emoji: "♉", name: "金牛", brief: "稳中有进，节奏感很好" },
  { key: "gemini", emoji: "♊", name: "双子", brief: "表达欲上升，社交顺滑" },
  { key: "cancer", emoji: "♋", name: "巨蟹", brief: "情绪细腻，适合疗愈自己" },
  { key: "leo", emoji: "♌", name: "狮子", brief: "魅力在线，适合主导发声" },
  { key: "virgo", emoji: "♍", name: "处女", brief: "细节加分，推进效率高" },
  { key: "libra", emoji: "♎", name: "天秤", brief: "关系平衡感增强" },
  { key: "scorpio", emoji: "♏", name: "天蝎", brief: "洞察力很强，适合深聊" },
  { key: "sagittarius", emoji: "♐", name: "射手", brief: "灵感充足，适合探索新鲜感" },
  { key: "capricorn", emoji: "♑", name: "摩羯", brief: "执行稳定，目标清晰" },
  { key: "aquarius", emoji: "♒", name: "水瓶", brief: "创意跃迁，脑洞在线" },
  { key: "pisces", emoji: "♓", name: "双鱼", brief: "共情力提升，适合创作" },
];

const zodiacScroller = computed(() => zodiacList.slice(0, 12));

function openSearch() {
  uni.showToast({ title: "搜索页即将上线", icon: "none" });
}

function openPostAction() {
  uni.showToast({ title: "社区互动即将上线", icon: "none" });
}

function openStory() {
  uni.showToast({ title: "故事详情即将上线", icon: "none" });
}

function openZodiac(name: string) {
  uni.showToast({ title: `${name}详情即将上线`, icon: "none" });
}
</script>

<template>
  <view class="page">
    <view class="search glass d1" @tap="openSearch">
      <text>🔍</text>
      <text class="search__placeholder">搜索测试、话题...</text>
    </view>

    <view class="tabs d1">
      <text
        v-for="item in [
          { key: 'hot', label: '热门' },
          { key: 'story', label: '故事' },
          { key: 'zodiac', label: '星座' },
        ]"
        :key="item.key"
        class="tabs__item"
        :class="{ 'tabs__item--active': activeTab === item.key }"
        @tap="activeTab = item.key as 'hot' | 'story' | 'zodiac'"
      >
        {{ item.label }}
      </text>
      <view
        class="tabs__line"
        :style="{
          left: activeTab === 'hot' ? '8%' : activeTab === 'story' ? '41%' : '74%',
        }"
      />
    </view>

    <template v-if="activeTab === 'hot'">
      <scroll-view scroll-x class="zodiac-row d2">
        <view class="zodiac-row__list">
          <view
            v-for="item in zodiacScroller"
            :key="item.key"
            class="zodiac-chip"
            @tap="openZodiac(item.name)"
          >
            <text class="zodiac-chip__emoji">{{ item.emoji }}</text>
            <text class="zodiac-chip__name">{{ item.name }}</text>
          </view>
        </view>
      </scroll-view>

      <view class="post-list d3">
        <view v-for="post in hotPosts" :key="post.id" class="post">
          <view class="post__head">
            <view class="post__avatar">{{ post.avatar }}</view>
            <view class="post__meta">
              <text class="post__name">{{ post.nickname }}</text>
              <text class="post__time">{{ post.time }}</text>
            </view>
          </view>
          <text class="post__content">{{ post.content }}</text>
          <view class="post__tags">
            <text v-for="tag in post.tags" :key="tag" class="post__tag">#{{ tag }}</text>
          </view>
          <view class="post__ops">
            <text @tap="openPostAction">❤️ {{ post.likes }}</text>
            <text @tap="openPostAction">💬 {{ post.comments }}</text>
            <text @tap="openPostAction">🔁 {{ post.shares }}</text>
          </view>
        </view>
      </view>
    </template>

    <template v-else-if="activeTab === 'story'">
      <view class="story-list d2">
        <view v-for="item in stories" :key="item.id" class="story-card" @tap="openStory">
          <view class="story-card__cover" :style="{ background: item.gradient }">
            <text>{{ item.emoji }}</text>
          </view>
          <view class="story-card__body">
            <text class="story-card__title">{{ item.title }}</text>
            <text class="story-card__summary">{{ item.summary }}</text>
            <view class="story-card__foot">
              <view class="story-card__author">
                <text>{{ item.authorAvatar }}</text>
                <text>{{ item.author }}</text>
              </view>
              <text>{{ item.reads }} 阅读 · {{ item.likes }} 点赞</text>
            </view>
          </view>
        </view>
      </view>
    </template>

    <template v-else>
      <view class="zodiac-grid d2">
        <view
          v-for="item in zodiacList"
          :key="item.key"
          class="zodiac-card"
          @tap="openZodiac(item.name)"
        >
          <text class="zodiac-card__emoji">{{ item.emoji }}</text>
          <text class="zodiac-card__name">{{ item.name }}</text>
          <text class="zodiac-card__brief">{{ item.brief }}</text>
        </view>
      </view>
    </template>

    <TabBuddy />
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 22rpx 24rpx 40rpx;
}

.glass {
  @include glass;
}

.search {
  border-radius: 999rpx;
  padding: 18rpx 22rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.search__placeholder {
  color: $xc-muted;
  font-size: 24rpx;
}

.tabs {
  margin-top: 18rpx;
  position: relative;
  display: flex;
  justify-content: space-around;
  padding-bottom: 14rpx;
  border-bottom: 1px solid rgba(155, 126, 216, 0.1);
}

.tabs__item {
  font-size: 26rpx;
  color: $xc-muted;
  padding: 8rpx 14rpx;
}

.tabs__item--active {
  color: $xc-purple-d;
  font-weight: 700;
}

.tabs__line {
  position: absolute;
  bottom: -2rpx;
  width: 16%;
  height: 6rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, $xc-purple, $xc-pink);
  transition: left 0.3s $xc-ease;
}

.zodiac-row {
  margin-top: 16rpx;
}

.zodiac-row__list {
  display: flex;
  gap: 12rpx;
}

.zodiac-chip {
  width: 98rpx;
  flex-shrink: 0;
  border-radius: 999rpx;
  padding: 14rpx 10rpx;
  text-align: center;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(155, 126, 216, 0.12);
}

.zodiac-chip__emoji {
  display: block;
  font-size: 26rpx;
}

.zodiac-chip__name {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.post-list {
  margin-top: 14rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.88);
  overflow: hidden;
}

.post {
  padding: 20rpx;
  border-bottom: 1px solid rgba(155, 126, 216, 0.08);
}

.post:last-child {
  border-bottom: 0;
}

.post__head {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.post__avatar {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: rgba(237, 229, 249, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
}

.post__meta {
  display: flex;
  flex-direction: column;
}

.post__name {
  font-size: 24rpx;
  font-weight: 700;
}

.post__time {
  font-size: 20rpx;
  color: $xc-muted;
}

.post__content {
  margin-top: 12rpx;
  display: block;
  font-size: 25rpx;
  line-height: 1.65;
}

.post__tags {
  margin-top: 8rpx;
  display: flex;
  gap: 10rpx;
  flex-wrap: wrap;
}

.post__tag {
  font-size: 20rpx;
  color: $xc-purple-d;
  background: $xc-purple-p;
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
}

.post__ops {
  margin-top: 12rpx;
  display: flex;
  gap: 24rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.story-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.story-card {
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.88);
  overflow: hidden;
  border: 1px solid rgba(155, 126, 216, 0.1);
}

.story-card__cover {
  height: 220rpx;
  color: $xc-white;
  font-size: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.story-card__body {
  padding: 18rpx;
}

.story-card__title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}

.story-card__summary {
  margin-top: 8rpx;
  display: block;
  color: $xc-muted;
  font-size: 23rpx;
  line-height: 1.6;
}

.story-card__foot {
  margin-top: 14rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: $xc-muted;
  font-size: 20rpx;
}

.story-card__author {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.zodiac-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.zodiac-card {
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(155, 126, 216, 0.12);
  padding: 14rpx 10rpx;
  text-align: center;
}

.zodiac-card__emoji {
  display: block;
  font-size: 32rpx;
}

.zodiac-card__name {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  font-weight: 700;
}

.zodiac-card__brief {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
  line-height: 1.5;
}

.d1,
.d2,
.d3 {
  animation: fadeInUp 0.5s $xc-ease both;
}

.d1 {
  animation-delay: 0.06s;
}

.d2 {
  animation-delay: 0.12s;
}

.d3 {
  animation-delay: 0.18s;
}

::v-deep(::-webkit-scrollbar) {
  display: none;
  width: 0;
  height: 0;
}
</style>
