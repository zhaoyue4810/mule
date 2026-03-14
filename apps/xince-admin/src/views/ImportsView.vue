<template>
  <el-card>
    <template #header>内容导入</template>
    <el-alert title="当前独立后台已预留导入位，下一步可接 /api/admin/import 接口形成完整导入工作流。" type="info" :closable="false" />
  </el-card>
</template>
