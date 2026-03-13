<script setup lang="ts">
import { computed } from "vue";

import BubbleRenderer from "@/components/question-renderers/BubbleRenderer.vue";
import ColorPickRenderer from "@/components/question-renderers/ColorPickRenderer.vue";
import ConstellationRenderer from "@/components/question-renderers/ConstellationRenderer.vue";
import FortuneRenderer from "@/components/question-renderers/FortuneRenderer.vue";
import HotColdRenderer from "@/components/question-renderers/HotColdRenderer.vue";
import OptionListFallback from "@/components/question-renderers/OptionListFallback.vue";
import Plot2dRenderer from "@/components/question-renderers/Plot2dRenderer.vue";
import PressureRenderer from "@/components/question-renderers/PressureRenderer.vue";
import RankRenderer from "@/components/question-renderers/RankRenderer.vue";
import ScratchRenderer from "@/components/question-renderers/ScratchRenderer.vue";
import ScenarioRenderer from "@/components/question-renderers/ScenarioRenderer.vue";
import SliderRenderer from "@/components/question-renderers/SliderRenderer.vue";
import StarRenderer from "@/components/question-renderers/StarRenderer.vue";
import SwipeRenderer from "@/components/question-renderers/SwipeRenderer.vue";
import TarotRenderer from "@/components/question-renderers/TarotRenderer.vue";
import VersusRenderer from "@/components/question-renderers/VersusRenderer.vue";
import type { AnswerValue } from "@/shared/models/answers";
import type { PublishedQuestionPayload } from "@/shared/models/tests";

const props = defineProps<{
  modelValue: AnswerValue;
  question: PublishedQuestionPayload;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: AnswerValue];
}>();

const config = computed<Record<string, unknown>>(
  () => (props.question.config as Record<string, unknown> | null) || {},
);
const optionValue = computed(() => props.modelValue.option_code || "");
const numericValue = computed(() =>
  typeof props.modelValue.numeric_value === "number"
    ? props.modelValue.numeric_value
    : null,
);
const orderedOptionCodes = computed(() => props.modelValue.ordered_option_codes || []);
const pointValue = computed(() => props.modelValue.point || null);

function updateOption(optionCode: string) {
  emit("update:modelValue", { option_code: optionCode });
}

function updateNumeric(value: number) {
  emit("update:modelValue", { numeric_value: value });
}

function updateRank(value: string[]) {
  emit("update:modelValue", { ordered_option_codes: value });
}

function updatePoint(value: { x: number; y: number }) {
  emit("update:modelValue", { point: value });
}
</script>

<template>
  <BubbleRenderer
    v-if="question.interaction_type === 'bubble'"
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
  <VersusRenderer
    v-else-if="question.interaction_type === 'versus'"
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
  <SwipeRenderer
    v-else-if="question.interaction_type === 'swipe'"
    :model-value="numericValue"
    :left-label="String(config.left_label || '不认同')"
    :right-label="String(config.right_label || '认同')"
    @update:model-value="updateNumeric"
  />
  <SliderRenderer
    v-else-if="question.interaction_type === 'slider'"
    :model-value="numericValue"
    :min="Number(config.min || 1)"
    :max="Number(config.max || 5)"
    :labels="(config.labels as string[] | undefined)"
    @update:model-value="updateNumeric"
  />
  <StarRenderer
    v-else-if="question.interaction_type === 'star'"
    :model-value="numericValue"
    :max="Number(config.max_stars || 5)"
    :labels="(config.labels as string[] | undefined)"
    @update:model-value="updateNumeric"
  />
  <HotColdRenderer
    v-else-if="question.interaction_type === 'hotcold'"
    :model-value="numericValue"
    :emojis="(config.emojis as string[] | undefined)"
    :labels="(config.labels as string[] | undefined)"
    :min-label="String(config.min_label || '冰冷')"
    :max-label="String(config.max_label || '火热')"
    @update:model-value="updateNumeric"
  />
  <ScenarioRenderer
    v-else-if="question.interaction_type === 'scenario'"
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
  <TarotRenderer
    v-else-if="question.interaction_type === 'tarot'"
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
  <FortuneRenderer
    v-else-if="question.interaction_type === 'fortune'"
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
  <ConstellationRenderer
    v-else-if="question.interaction_type === 'constellation'"
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
  <PressureRenderer
    v-else-if="question.interaction_type === 'pressure'"
    :model-value="numericValue"
    :max-duration="Number(config.max_duration || 3000)"
    @update:model-value="updateNumeric"
  />
  <RankRenderer
    v-else-if="question.interaction_type === 'rank'"
    :model-value="orderedOptionCodes"
    :question="question"
    @update:model-value="updateRank"
  />
  <Plot2dRenderer
    v-else-if="question.interaction_type === 'plot2d'"
    :model-value="pointValue"
    :x-min="String(config.x_min || '左')"
    :x-max="String(config.x_max || '右')"
    :y-min="String(config.y_min || '下')"
    :y-max="String(config.y_max || '上')"
    @update:model-value="updatePoint"
  />
  <ColorPickRenderer
    v-else-if="question.interaction_type === 'colorpick'"
    :model-value="numericValue"
    :hue-map="(config.hue_map as Record<string, unknown> | undefined)"
    @update:model-value="updateNumeric"
  />
  <ScratchRenderer
    v-else-if="question.interaction_type === 'scratch'"
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
  <OptionListFallback
    v-else
    :model-value="optionValue"
    :question="question"
    @update:model-value="updateOption"
  />
</template>
