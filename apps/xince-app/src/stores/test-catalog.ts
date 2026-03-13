import { defineStore } from "pinia";
import { ref } from "vue";

import type {
  PublishedTestDetail,
  PublishedTestQuestionnaire,
  PublishedTestSummary,
} from "@/shared/models/tests";
import {
  fetchPublishedTestDetail,
  fetchPublishedTestQuestionnaire,
  fetchPublishedTests,
} from "@/shared/services/tests";

export const useTestCatalogStore = defineStore("testCatalog", () => {
  const tests = ref<PublishedTestSummary[]>([]);
  const loading = ref(false);
  const error = ref("");
  const detailMap = ref<Record<string, PublishedTestDetail>>({});
  const questionnaireMap = ref<Record<string, PublishedTestQuestionnaire>>({});

  async function loadTests(force = false) {
    if (tests.value.length > 0 && !force) {
      return tests.value;
    }

    loading.value = true;
    error.value = "";
    try {
      tests.value = await fetchPublishedTests();
      return tests.value;
    } catch (err) {
      error.value = err instanceof Error ? err.message : "测试列表加载失败";
      throw err;
    } finally {
      loading.value = false;
    }
  }

  async function loadDetail(testCode: string, force = false) {
    if (detailMap.value[testCode] && !force) {
      return detailMap.value[testCode];
    }

    const detail = await fetchPublishedTestDetail(testCode);
    detailMap.value = {
      ...detailMap.value,
      [testCode]: detail,
    };
    return detail;
  }

  async function loadQuestionnaire(testCode: string, force = false) {
    if (questionnaireMap.value[testCode] && !force) {
      return questionnaireMap.value[testCode];
    }

    const questionnaire = await fetchPublishedTestQuestionnaire(testCode);
    questionnaireMap.value = {
      ...questionnaireMap.value,
      [testCode]: questionnaire,
    };
    return questionnaire;
  }

  return {
    detailMap,
    error,
    loading,
    questionnaireMap,
    tests,
    loadDetail,
    loadQuestionnaire,
    loadTests,
  };
});
