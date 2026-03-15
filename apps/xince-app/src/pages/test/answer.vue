<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import XiaoCe from "@/components/mascot/XiaoCe.vue";
import XcMicroFeedback from "@/components/mascot/XcMicroFeedback.vue";
import ReportReveal from "@/components/feedback/ReportReveal.vue";
import QuestionRenderer from "@/components/question-renderers/QuestionRenderer.vue";
import type { AnswerValue } from "@/shared/models/answers";
import type { PublishedTestQuestionnaire } from "@/shared/models/tests";
import { SoundManager } from "@/shared/utils/sound-manager";
import {
  clearAuthSession,
  ensureAppSession,
  getSessionUser,
} from "@/shared/services/auth";
import { useTestCatalogStore } from "@/stores/test-catalog";
import { submitTestAnswers } from "@/shared/services/tests";

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

const currentQuestion = computed(
  () => questionnaire.value?.questions[currentIndex.value] || null,
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
const progressText = computed(() => {
  if (!questionnaire.value) {
    return "";
  }
  return `${currentIndex.value + 1} / ${questionnaire.value.question_count}`;
});

async function loadQuestionnaire(testCode: string) {
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    questionnaire.value = await store.loadQuestionnaire(testCode);
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

function pickMicroFeedback(interactionType?: string) {
  const type = (interactionType || "").toLowerCase();
  if (type.includes("swipe")) {
    return Math.random() > 0.5 ? "果断!" : "让我想想…";
  }
  if (type.includes("bubble")) {
    return "这个泡泡很适合你~";
  }
  if (type.includes("tarot")) {
    return "命运的指引…";
  }
  if (type.includes("slider")) {
    return "这个刻度很有感觉";
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
      duration_seconds: Math.max(
        1,
        Math.round((Date.now() - startedAt.value) / 1000),
      ),
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
        (response.unlocked_badges && response.unlocked_badges[0]?.name) ||
        "稀有人格",
      dimensions:
        Array.from(
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
  const testCode =
    query && typeof query.testCode === "string" ? query.testCode : "";
  if (!testCode) {
    error.value = "缺少 testCode 参数";
    loading.value = false;
    return;
  }
  startedAt.value = Date.now();
  loadQuestionnaire(testCode);
});

onBeforeUnmount(() => {
  if (microFeedbackTimer) {
    clearTimeout(microFeedbackTimer);
  }
});
</script>

<template>
  <view class="page">
    <view v-if="loading" class="state-card">
      <text class="state-card__text">正在加载题目...</text>
    </view>

    <view v-else-if="error" class="state-card state-card--error">
      <text class="state-card__text">{{ error }}</text>
    </view>

    <view v-else-if="questionnaire && currentQuestion" class="answer">
      <view class="answer__hero">
        <text class="answer__category">{{ questionnaire.category }}</text>
        <text class="answer__title">{{ questionnaire.name }}</text>
        <text class="answer__meta">
          第 {{ progressText }} 题 · {{ questionnaire.duration_hint || "预计几分钟完成" }}
        </text>
      </view>

      <view class="question-card">
        <view class="question-card__mascot">
          <XiaoCe expression="thinking" size="md" :animated="true" />
        </view>
        <text class="question-card__index">Q{{ currentQuestion.seq }}</text>
        <text class="question-card__title">{{ currentQuestion.question_text }}</text>
        <text class="question-card__hint">
          当前题型：{{ currentQuestion.interaction_type }}
        </text>
      </view>

      <QuestionRenderer
        :model-value="answers[currentQuestion.seq] || {}"
        :question="currentQuestion"
        @update:model-value="updateAnswer"
      />

      <view class="actions">
        <button class="actions__ghost" :disabled="currentIndex === 0" @tap="previousQuestion">
          上一题
        </button>
        <button class="actions__primary" :disabled="!isCurrentAnswered || submitting || advancing" @tap="goNext">
          {{
            submitting
              ? "提交中..."
              : currentIndex + 1 === questionnaire.question_count
                ? "完成"
                : "下一题"
          }}
        </button>
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
  padding: 28rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.state-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 2rpx solid $xc-line;
}

.state-card--error {
  background: rgba(255, 240, 235, 0.92);
}

.state-card__text {
  font-size: 26rpx;
  color: $xc-muted;
}

.answer {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.answer__hero {
  padding: 32rpx 28rpx;
  border-radius: 26rpx;
  background: linear-gradient(145deg, #fff1dc, #ffd6b6);
  box-shadow: $xc-shadow;
}

.answer__category {
  display: block;
  font-size: 22rpx;
  color: rgba(58, 46, 66, 0.68);
}

.answer__title {
  display: block;
  margin-top: 16rpx;
  font-size: 38rpx;
  line-height: 1.35;
  font-weight: 700;
}

.answer__meta {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  color: rgba(58, 46, 66, 0.74);
}

.question-card {
  position: relative;
  padding: 30rpx 26rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid rgba(58, 46, 66, 0.06);
}

.question-card__mascot {
  position: absolute;
  right: 22rpx;
  top: 20rpx;
}

.question-card__index {
  display: block;
  font-size: 22rpx;
  color: $xc-accent;
}

.question-card__title {
  display: block;
  margin-top: 16rpx;
  font-size: 34rpx;
  line-height: 1.5;
  font-weight: 600;
}

.question-card__hint {
  display: block;
  margin-top: 14rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.actions__ghost,
.actions__primary {
  border-radius: 999rpx;
}

.actions__primary {
  background: linear-gradient(135deg, #9B7ED8, #7C5DBF);
  color: #fff8f1;
}
</style>
