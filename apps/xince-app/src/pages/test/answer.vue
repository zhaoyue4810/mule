<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import QuestionRenderer from "@/components/question-renderers/QuestionRenderer.vue";
import type { AnswerValue } from "@/shared/models/answers";
import type { PublishedTestQuestionnaire } from "@/shared/models/tests";
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
const startedAt = ref(Date.now());

const currentQuestion = computed(
  () => questionnaire.value?.questions[currentIndex.value] || null,
);
const selectedOptionCode = computed(() => {
  const question = currentQuestion.value;
  if (!question) {
    return "";
  }
  return answers.value[question.seq]?.option_code || "";
});
const selectedNumericValue = computed(() => {
  const question = currentQuestion.value;
  if (!question) {
    return null;
  }
  const value = answers.value[question.seq]?.numeric_value;
  return typeof value === "number" ? value : null;
});
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
}

function previousQuestion() {
  if (currentIndex.value > 0) {
    currentIndex.value -= 1;
  }
}

async function goNext() {
  if (!questionnaire.value || !currentQuestion.value || !selectedOptionCode.value) {
    if (
      !questionnaire.value ||
      !currentQuestion.value ||
      !isCurrentAnswered.value
    ) {
      return;
    }

    if (currentIndex.value < questionnaire.value.question_count - 1) {
      currentIndex.value += 1;
      return;
    }

    submitting.value = true;
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

      uni.redirectTo({
        url: `/pages/test/result?recordId=${response.record_id}`,
      });
    } catch (err) {
      uni.showToast({
        title: err instanceof Error ? err.message : "提交失败",
        icon: "none",
      });
    } finally {
      submitting.value = false;
    }
    return;
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
        <button class="actions__primary" :disabled="!isCurrentAnswered || submitting" @tap="goNext">
          {{
            submitting
              ? "提交中..."
              : currentIndex + 1 === questionnaire.question_count
                ? "完成"
                : "下一题"
          }}
        </button>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx;
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
  color: rgba(43, 33, 24, 0.68);
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
  color: rgba(43, 33, 24, 0.74);
}

.question-card {
  padding: 30rpx 26rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid rgba(43, 33, 24, 0.06);
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
  background: linear-gradient(135deg, #d96f3d, #bf5321);
  color: #fff8f1;
}
</style>
