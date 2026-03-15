<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import ReportReveal from "@/components/feedback/ReportReveal.vue";
import XiaoCe from "@/components/mascot/XiaoCe.vue";
import XcBubble from "@/components/mascot/XcBubble.vue";
import XcMicroFeedback from "@/components/mascot/XcMicroFeedback.vue";
import QuestionRenderer from "@/components/question-renderers/QuestionRenderer.vue";
import type { AnswerValue } from "@/shared/models/answers";
import type { PublishedTestQuestionnaire } from "@/shared/models/tests";
import {
  clearAuthSession,
  ensureAppSession,
  getSessionUser,
} from "@/shared/services/auth";
import { submitTestAnswers } from "@/shared/services/tests";
import { resolveInteractionUiMeta, resolveTestTheme } from "@/shared/utils/test-ui";
import { SoundManager } from "@/shared/utils/sound-manager";
import { useTestCatalogStore } from "@/stores/test-catalog";

const store = useTestCatalogStore();

const questionnaire = ref<PublishedTestQuestionnaire | null>(null);
const loading = ref(true);
const error = ref("");
const currentIndex = ref(0);
const answers = ref<Record<number, AnswerValue>>({});
const submitting = ref(false);
const advancing = ref(false);
const startedAt = ref(Date.now());
const microFeedbackText = ref("");
const microFeedbackVisible = ref(false);
const revealVisible = ref(false);
const revealPersona = ref<{
  name?: string | null;
  persona_name?: string | null;
  persona_key?: string | null;
  emoji?: string | null;
  result_tier?: string | null;
  rarity_percent?: number | null;
  dimensions?: Array<{ name: string }>;
} | null>(null);
const revealScore = ref(0);
const revealRecordId = ref(0);
let microFeedbackTimer: ReturnType<typeof setTimeout> | null = null;

const theme = computed(() => resolveTestTheme(questionnaire.value?.category));
const currentQuestion = computed(
  () => questionnaire.value?.questions[currentIndex.value] || null,
);
const interactionUi = computed(() =>
  resolveInteractionUiMeta(currentQuestion.value?.interaction_type),
);
const progressPercent = computed(() => {
  if (!questionnaire.value) {
    return 0;
  }
  return ((currentIndex.value + 1) / questionnaire.value.question_count) * 100;
});
const answeredCount = computed(() => Object.keys(answers.value).length);
const progressText = computed(() => {
  if (!questionnaire.value) {
    return "";
  }
  return `${currentIndex.value + 1}/${questionnaire.value.question_count}`;
});
const stageBadgeText = computed(() => {
  if (!currentQuestion.value) {
    return "";
  }
  const dims = Object.keys(currentQuestion.value.dim_weights || {}).map((item) => item.toUpperCase());
  return dims.length ? dims.slice(0, 2).join(" / ") : "灵魂线索";
});
const assistantText = computed(() =>
  microFeedbackVisible.value && microFeedbackText.value
    ? microFeedbackText.value
    : interactionUi.value.prompt,
);
const isCurrentAnswered = computed(() => {
  if (!currentQuestion.value) {
    return false;
  }
  const answer = answers.value[currentQuestion.value.seq];
  return Boolean(
    answer &&
      (answer.option_code ||
        typeof answer.numeric_value === "number" ||
        (answer.ordered_option_codes && answer.ordered_option_codes.length) ||
        answer.point),
  );
});
const nextButtonText = computed(() => {
  if (!questionnaire.value) {
    return "下一题";
  }
  if (submitting.value) {
    return "结果显影中...";
  }
  return currentIndex.value + 1 === questionnaire.value.question_count ? "完成测试" : "下一题";
});
const rocketMarks = computed(() => {
  if (!questionnaire.value) {
    return [];
  }
  return Array.from({ length: questionnaire.value.question_count }, (_, index) => ({
    key: index + 1,
    active: index < currentIndex.value,
    current: index === currentIndex.value,
  }));
});

async function loadQuestionnaire(testCode: string) {
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    questionnaire.value = await store.loadQuestionnaire(testCode, true);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "题目加载失败";
  } finally {
    loading.value = false;
  }
}

function updateAnswer(value: AnswerValue) {
  const question = currentQuestion.value;
  if (!question) {
    return;
  }

  answers.value = {
    ...answers.value,
    [question.seq]: value,
  };

  if (SoundManager.isSoundEnabled()) {
    SoundManager.play("whoosh");
  }
  SoundManager.haptic(15);
}

function previousQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value -= 1;
  }
}

function goBack() {
  if (!answeredCount.value) {
    uni.navigateBack();
    return;
  }

  uni.showModal({
    title: "退出答题？",
    content: "当前进度不会保存，确定回到详情页吗？",
    confirmText: "退出",
    cancelText: "继续答题",
    success: (res) => {
      if (res.confirm) {
        uni.navigateBack();
      }
    },
  });
}

function pickMicroFeedback(interactionType?: string) {
  const type = (interactionType || "").toLowerCase();
  if (type.includes("swipe")) {
    return Math.random() > 0.5 ? "直觉够果断" : "这个倾向很真实";
  }
  if (type.includes("bubble")) {
    return "这个泡泡在发光";
  }
  if (type.includes("tarot")) {
    return "命运牌面翻开了";
  }
  if (type.includes("slider")) {
    return "这个刻度刚刚好";
  }
  if (type.includes("star")) {
    return "你很清楚自己的感受";
  }
  if (type.includes("fortune")) {
    return "答案已经转出来了";
  }
  return "小测收到啦";
}

function triggerMicroFeedback(interactionType?: string) {
  microFeedbackText.value = pickMicroFeedback(interactionType);
  microFeedbackVisible.value = false;
  if (microFeedbackTimer) {
    clearTimeout(microFeedbackTimer);
  }
  void nextTick(() => {
    microFeedbackVisible.value = true;
    microFeedbackTimer = setTimeout(() => {
      microFeedbackVisible.value = false;
    }, 1500);
  });
}

function completeReveal() {
  revealVisible.value = false;
  if (!revealRecordId.value) {
    return;
  }
  uni.redirectTo({
    url: `/pages/test/result?recordId=${revealRecordId.value}`,
  });
}

async function goNext() {
  if (
    !questionnaire.value ||
    !currentQuestion.value ||
    !isCurrentAnswered.value ||
    submitting.value ||
    advancing.value
  ) {
    return;
  }

  const interactionType = currentQuestion.value.interaction_type;

  if (currentIndex.value < questionnaire.value.question_count - 1) {
    advancing.value = true;
    triggerMicroFeedback(interactionType);
    currentIndex.value += 1;
    setTimeout(() => {
      advancing.value = false;
    }, 220);
    return;
  }

  submitting.value = true;
  advancing.value = true;
  try {
    const currentUser = await ensureAppSession();
    const payload = {
      user_id: currentUser.user_id,
      nickname: "心测访客",
      duration_seconds: Math.max(1, Math.round((Date.now() - startedAt.value) / 1000)),
      answers: questionnaire.value.questions.map((item) => ({
        question_seq: item.seq,
        option_code: answers.value[item.seq]?.option_code || null,
        numeric_value:
          typeof answers.value[item.seq]?.numeric_value === "number"
            ? answers.value[item.seq]?.numeric_value || null
            : null,
        ordered_option_codes: answers.value[item.seq]?.ordered_option_codes || null,
        point: answers.value[item.seq]?.point || null,
      })),
    };
    let response;
    try {
      response = await submitTestAnswers(questionnaire.value.test_code, payload);
    } catch (err) {
      if (
        err instanceof Error &&
        (err.message.includes("User not found") ||
          err.message.includes("Authorization required") ||
          err.message.includes("Token"))
      ) {
        clearAuthSession();
        const fallbackUser = await ensureAppSession();
        response = await submitTestAnswers(questionnaire.value.test_code, {
          ...payload,
          user_id: fallbackUser.user_id,
        });
      } else {
        throw err;
      }
    }
    const storedUser = getSessionUser();
    if (!storedUser || storedUser.user_id !== response.user_id) {
      await ensureAppSession();
    }

    revealRecordId.value = response.record_id;
    revealScore.value = response.total_score || 0;
    revealPersona.value = {
      name: response.persona_name,
      persona_name: response.persona_name,
      persona_key: response.persona_key,
      result_tier:
        (response.unlocked_badges && response.unlocked_badges[0]?.name) || "稀有人格",
      dimensions: Array.from(
        new Set(
          questionnaire.value.questions.flatMap((item) =>
            Object.keys(item.dim_weights || {}).map((dimCode) => dimCode.toUpperCase()),
          ),
        ),
      )
        .slice(0, 5)
        .map((name) => ({ name })),
    };
    revealVisible.value = true;
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "提交失败",
      icon: "none",
    });
  } finally {
    submitting.value = false;
    advancing.value = false;
  }
}

onLoad((query) => {
  const testCode = query && typeof query.testCode === "string" ? query.testCode : "";
  if (!testCode) {
    error.value = "缺少 testCode 参数";
    loading.value = false;
    return;
  }
  startedAt.value = Date.now();
  void loadQuestionnaire(testCode);
});

onBeforeUnmount(() => {
  if (microFeedbackTimer) {
    clearTimeout(microFeedbackTimer);
  }
});
</script>

<template>
  <view class="page">
    <view class="page__ambient page__ambient--one" :style="{ background: theme.chipGradient }" />
    <view class="page__ambient page__ambient--two" :style="{ background: theme.softGradient }" />

    <view v-if="loading" class="state-card">
      <text class="state-card__text">正在加载题目...</text>
    </view>

    <view v-else-if="error" class="state-card state-card--error">
      <text class="state-card__text">{{ error }}</text>
    </view>

    <view v-else-if="questionnaire && currentQuestion" class="answer">
      <view class="tt-top">
        <view class="tt-top-row">
          <button class="tt-back" @tap="goBack">←</button>
          <text class="tt-title">{{ questionnaire.name }}</text>
          <text class="tt-counter">{{ progressText }}</text>
        </view>
        <view class="rocket-track">
          <view class="rocket-bar" />
          <view class="rocket-fill" :style="{ width: `${progressPercent}%`, background: theme.gradient }">
            <text class="rocket-icon">{{ theme.emoji }}</text>
          </view>
          <view class="rocket-stars">
            <text
              v-for="item in rocketMarks"
              :key="item.key"
              class="rocket-star"
              :class="{
                'rocket-star--active': item.active,
                'rocket-star--current': item.current,
              }"
            >
              {{ item.active ? "⭐" : item.current ? "✦" : "·" }}
            </text>
          </view>
        </view>
      </view>

      <view class="q-stage" :style="{ background: theme.softGradient }">
        <view :key="currentQuestion.seq" class="q-shell">
          <view class="q-header">
            <text class="q-num">QUESTION {{ String(currentQuestion.seq).padStart(2, "0") }}</text>
            <view class="q-meta-row">
              <text class="q-pill" :style="{ background: theme.chipGradient }">
                {{ interactionUi.icon }} {{ interactionUi.label }}
              </text>
              <text class="q-pill q-pill--ghost">{{ stageBadgeText }}</text>
              <text class="q-pill q-pill--ghost">已答 {{ answeredCount }}/{{ questionnaire.question_count }}</text>
            </view>
            <text class="q-text">{{ currentQuestion.question_text }}</text>
          </view>

          <view class="q-guide">
            <view class="q-guide__mascot">
              <XiaoCe expression="thinking" size="md" :animated="true" />
            </view>
            <view class="q-guide__bubble">
              <XcBubble :text="assistantText" :persistent="true" />
            </view>
          </view>

          <view class="q-body" :class="{ 'q-body--advancing': advancing }">
            <QuestionRenderer
              :model-value="answers[currentQuestion.seq] || {}"
              :question="currentQuestion"
              @update:model-value="updateAnswer"
            />
          </view>
        </view>

        <view class="q-actions">
          <button class="q-button q-button--ghost" :disabled="currentIndex === 0" @tap="previousQuestion">
            上一题
          </button>
          <button
            class="q-button q-button--primary"
            :disabled="!isCurrentAnswered || submitting || advancing"
            @tap="goNext"
          >
            {{ nextButtonText }}
          </button>
        </view>
      </view>

      <XcMicroFeedback :text="microFeedbackText" :show="microFeedbackVisible" />
    </view>

    <ReportReveal
      :visible="revealVisible"
      :persona="revealPersona"
      :total-score="revealScore"
      :on-complete="completeReveal"
    />
  </view>
</template>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.page__ambient {
  position: fixed;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.6;
  pointer-events: none;
}

.page__ambient--one {
  top: 120rpx;
  left: -70rpx;
  width: 220rpx;
  height: 220rpx;
}

.page__ambient--two {
  right: -90rpx;
  bottom: 180rpx;
  width: 280rpx;
  height: 280rpx;
}

.state-card {
  margin: 28rpx;
  padding: 32rpx;
  border-radius: $xc-r-lg;
  @include glass;
  text-align: center;
}

.state-card--error {
  background: rgba(255, 240, 235, 0.92);
}

.state-card__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.answer {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.tt-top {
  position: sticky;
  top: 0;
  z-index: 30;
  padding: 16rpx 22rpx 14rpx;
  background: rgba(251, 247, 244, 0.9);
  border-bottom: 1px solid $xc-line-soft;
  // #ifdef H5
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  // #endif
}

.tt-top-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 10rpx;
}

.tt-back {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.88);
  color: $xc-muted;
  font-size: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $xc-sh-sm;
}

.tt-title {
  flex: 1;
  min-width: 0;
  text-align: center;
  font-size: 25rpx;
  color: $xc-muted;
  font-weight: 700;
}

.tt-counter {
  min-width: 72rpx;
  text-align: right;
  font-size: 24rpx;
  font-weight: 900;
  color: $xc-purple;
}

.rocket-track {
  position: relative;
  height: 46rpx;
}

.rocket-bar {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 8rpx;
  transform: translateY(-50%);
  border-radius: 999rpx;
  background: rgba(181, 169, 191, 0.22);
}

.rocket-fill {
  position: absolute;
  top: 50%;
  left: 0;
  height: 8rpx;
  transform: translateY(-50%);
  border-radius: 999rpx;
  transition: width 0.7s $xc-ease;
}

.rocket-icon {
  position: absolute;
  right: -16rpx;
  top: 50%;
  transform: translateY(-52%);
  font-size: 24rpx;
  filter: drop-shadow(0 4rpx 10rpx rgba(155, 126, 216, 0.25));
}

.rocket-stars {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
}

.rocket-star {
  font-size: 20rpx;
  color: rgba(181, 169, 191, 0.5);
}

.rocket-star--active {
  color: $xc-gold;
}

.rocket-star--current {
  color: $xc-purple;
}

.q-stage {
  flex: 1;
  min-height: calc(100vh - 128rpx);
  padding: 24rpx 24rpx calc(40rpx + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  gap: 22rpx;
  transition: background 0.5s $xc-ease;
}

.q-shell {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  flex: 1;
}

.q-header {
  text-align: center;
  animation: qEnter 0.45s $xc-ease both;
}

.q-num {
  display: block;
  font-size: 20rpx;
  font-weight: 800;
  letter-spacing: 3rpx;
  color: $xc-purple;
}

.q-meta-row {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10rpx;
}

.q-pill {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  color: $xc-purple-d;
  font-weight: 700;
}

.q-pill--ghost {
  background: rgba(255, 255, 255, 0.78);
  color: $xc-muted;
  border: 1px solid rgba(155, 126, 216, 0.08);
}

.q-text {
  display: block;
  margin-top: 18rpx;
  padding: 0 8rpx;
  font-family: $xc-font-serif;
  font-size: 38rpx;
  line-height: 1.62;
  font-weight: 800;
  color: $xc-ink;
}

.q-guide {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.q-guide__mascot {
  padding-top: 6rpx;
  flex-shrink: 0;
}

.q-guide__bubble {
  flex: 1;
  min-width: 0;
}

.q-body {
  flex: 1;
  padding: 28rpx 20rpx 24rpx;
  border-radius: $xc-r-lg;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: $xc-sh-md;
  // #ifdef H5
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  // #endif
  transition:
    transform 0.24s $xc-ease,
    opacity 0.24s $xc-ease;
}

.q-body--advancing {
  transform: translateY(8rpx);
  opacity: 0.9;
}

.q-actions {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 14rpx;
}

.q-button {
  height: 88rpx;
  border-radius: 999rpx;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.q-button--ghost {
  background: rgba(255, 255, 255, 0.88);
  color: $xc-muted;
  border: 1px solid rgba(155, 126, 216, 0.1);
}

.q-button--primary {
  position: relative;
  overflow: hidden;
  @include btn-primary;
}

.q-button--primary::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  background-size: 200% 100%;
  animation: shimmer 2.4s infinite;
}

.q-button[disabled] {
  opacity: 0.45;
  box-shadow: none;
}

@keyframes qEnter {
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
