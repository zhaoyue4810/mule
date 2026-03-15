# 可配置卡片式报告系统设计方案

## 1. 当前系统分析

### 1.1 当前报告生成流程

```
用户提交测试 → TestSubmissionService.submit() → ScoreEngine 计分 → 匹配 Persona
                            ↓
                    ReportSnapshot 创建 (report_json 存储固定结构)
                            ↓
                    AppReportService.get_report_detail() → 组装固定报告结构
                            ↓
                    AI 分析 (可选) → ReportAiService._generate_ai_analysis()
```

### 1.2 当前数据结构

**后端 (ReportSnapshot)**:
```python
class ReportSnapshot:
    dimension_scores: JSON       # 维度分数
    overall_score: int          # 总分
    persona_code: str           # 人格代码
    report_json: JSON           # 固定结构: {test_code, test_name, persona_key, persona_name, summary, top_dimensions}
    ai_text: str               # AI 生成的文本
```

**前端 (AppReportDetail)**:
- 固定返回结构包含: radar_dimensions, persona_tags, soul_weather, metaphor_cards, dna_segments, action_guides, share_card 等
- 所有字段在 `app_report_service.py` 中通过 `_build_*` 方法硬编码生成

### 1.3 当前配置能力

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `report_template_code` | TestVersion | 仅用于选择 AI Prompt 模板 |
| Prompt 模板 | `ai_prompt_templates.yaml` | 纯文本模板，无结构化卡片概念 |
| 报告结构 | `app_report_service.py` 硬编码 | 无法灵活配置 |

### 1.4 当前系统限制

1. **报告结构固定**: 所有测试返回相同的报告字段，无法针对测试定制
2. **卡片类型固定**: 只能展示预定义的卡片（雷达图、DNA、隐喻卡等）
3. **计算逻辑硬编码**: 如 `_build_soul_weather()`、`_build_metaphor_cards()` 等方法写死在代码中
4. **AI 生成无卡片概念**: AI 只生成一段纯文本，无法与特定卡片绑定
5. **前端渲染固定**: `result.vue` 中写死了各卡片的渲染顺序和样式

---

## 2. 目标设计架构

### 2.1 核心概念: 报告配置模板 (ReportLayoutConfig)

每个测试版本关联一个报告布局配置，定义报告由哪些卡片组成，以及每张卡片如何渲染和计算。

```
TestVersion → ReportLayoutConfig → ReportCards[]
                    ↓
            CardConfig + DataSource + RenderConfig
```

### 2.2 卡片类型设计

| 卡片类型 | 用途 | 配置内容 |
|----------|------|----------|
| `hero` | 顶部人格展示 | 标题、emoji、分数展示方式 |
| `radar` | 雷达图 | 维度选择、颜色主题 |
| `bar_chart` | 柱状图 | 维度分组、标签、颜色 |
| `persona_desc` | 人格描述 | 字段映射、样式 |
| `calendar` | 日历热力图 | 数据映射规则 |
| `hex_dim` | 六维图 | 六个维度的配置 |
| `future_letter` | 未来的信 | AI 生成配置 |
| `metaphor` | 隐喻卡片 | 隐喻类型、图标配置 |
| `tags` | 标签云 | 标签来源、样式 |
| `score_ring` | 分数环 | 计算规则、阈值 |
| `action_guide` | 行动建议 | 建议模板、规则 |
| `ai_analysis` | AI 深度分析 | Prompt 片段、输出格式 |
| `share_card` | 分享卡片 | 布局、字段选择 |

### 2.3 AI 生成策略

**整体架构**:
```
ReportLayoutConfig 包含一个 base_prompt（整套测试共用）
    ↓
每张卡片可以定义:
  - prompt_addon: 附加到 base_prompt 的片段
  - output_format: 期望输出格式 (json/markdown/text)
  - placeholder_key: 在最终报告中替换的占位符
    ↓
AI 生成完整报告 → 解析各卡片内容 → 存储到 ReportSnapshot.card_contents
```

**Prompt 组装示例**:
```yaml
# ReportLayoutConfig.ai_config
base_prompt: |
  你是一位心理测评报告撰写专家。请基于用户的测试结果生成一份完整的报告。
  测试名称: {test_name}
  人格类型: {persona_name}
  维度分数: {dimension_scores}

cards:
  - card_type: "future_letter"
    prompt_addon: |
      ## 未来的信
      请以"来自未来的你"的口吻写一段 150 字左右的信，包含:
      1. 对当前状态的肯定
      2. 一个具体的未来场景描绘
      3. 一句鼓励的话
    output_format: "markdown"
    placeholder_key: "future_letter_content"

  - card_type: "metaphor"
    prompt_addon: |
      ## 隐喻卡片
      请生成 3 个隐喻卡片，每个包含: category, title, subtitle, emoji
      与 {persona_name} 的人格特质相关
    output_format: "json"
    placeholder_key: "metaphor_cards"
```

---

## 3. 详细技术方案

### 3.1 数据模型设计

#### 3.1.1 新模型: ReportLayoutConfig

```python
# server/app/models/report_layout.py

class ReportLayoutConfig(TimestampMixin, Base):
    __tablename__ = "xc_report_layout_config"

    id: Mapped[int] = mapped_column(BIGINT_ID, primary_key=True)
    config_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # 如: mbti_default_v1
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # AI 配置
    ai_base_prompt: Mapped[Optional[str]] = mapped_column(Text)  # 基础 prompt
    ai_model_tier: Mapped[str] = mapped_column(String(20), default="PRO")
    ai_temperature: Mapped[float] = mapped_column(default=0.75)
    ai_max_tokens: Mapped[int] = mapped_column(default=2000)

    # 卡片配置 (JSON 存储卡片列表配置)
    cards_config: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ReportLayoutCardConfig(BaseModel):
    """单张卡片的配置 (存储在 cards_config 中)"""
    card_type: str                    # 卡片类型标识
    card_id: str                      # 唯一标识，用于前端定位
    title: Optional[str]              # 卡片标题
    icon: Optional[str]               # 图标/emoji
    sort_order: int                   # 排序

    # 数据源配置
    data_source: CardDataSource       # 数据从哪来

    # 渲染配置
    render_config: CardRenderConfig   # 如何渲染

    # AI 生成配置 (可选)
    ai_config: Optional[CardAiConfig]

    # 显示条件
    display_condition: Optional[DisplayCondition]


class CardDataSource(BaseModel):
    """数据源配置"""
    type: Literal["dimension_scores", "persona", "computed", "ai_generated", "static"]
    # 不同 type 的具体配置
    config: dict

    # type=dimension_scores: config={"dims": ["EI", "SN"], "sort_by": "abs_score", "limit": 5}
    # type=persona: config={"fields": ["name", "description", "keywords"]}
    # type=computed: config={"formula": "score_EI > 0 ? 'E' : 'I'", "variables": [...]}
    # type=ai_generated: config={"placeholder_key": "future_letter"}
    # type=static: config={"value": {...}}


class CardRenderConfig(BaseModel):
    """渲染配置"""
    # 通用样式
    theme: Optional[str]              # 主题色
    background: Optional[str]         # 背景样式
    card_style: Optional[str]         # 卡片样式: elevated/flat/outlined

    # 组件特定配置
    component_config: dict            # 组件特定参数

    # radar 组件: {"show_labels": true, "fill_opacity": 0.3, "grid_lines": 5}
    # bar_chart 组件: {"orientation": "vertical", "show_values": true, "bar_colors": [...]}
    # calendar 组件: {"heatmap_field": "mood_score", "date_field": "date"}


class CardAiConfig(BaseModel):
    """AI 生成配置"""
    prompt_addon: str                 # 附加到 base_prompt 的片段
    output_format: Literal["text", "markdown", "json"]
    placeholder_key: str              # 在 ReportSnapshot 中存储的 key
    fallback_content: Optional[str]   # AI 失败时的默认内容


class DisplayCondition(BaseModel):
    """显示条件"""
    type: Literal["always", "score_threshold", "dimension_match", "has_persona"]
    config: dict

    # type=score_threshold: config={"min_score": 50, "max_score": 100}
    # type=dimension_match: config={"dim_code": "EI", "operator": ">", "value": 0}
```

#### 3.1.2 修改现有模型

```python
# server/app/models/test.py

class TestVersion:
    # ... 现有字段 ...
    # 修改: 从 report_template_code 改为 report_layout_config_id
    report_layout_config_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("xc_report_layout_config.id"),
        nullable=True,
    )


# server/app/models/report.py

class ReportSnapshot:
    # ... 现有字段保留 (向后兼容) ...

    # 新增: 存储各卡片的 AI 生成内容
    card_contents: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # 存储结构: {"future_letter": "...", "metaphor_cards": [...], ...}

    # 新增: 使用的布局配置
    layout_config_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("xc_report_layout_config.id"),
        nullable=True,
    )
```

### 3.2 API 设计

#### 3.2.1 管理后台 API

```typescript
// 报告布局配置 CRUD
GET   /admin/report-layouts                    // 列表
POST  /admin/report-layouts                    // 创建
GET   /admin/report-layouts/:id                // 详情
PUT   /admin/report-layouts/:id                // 更新
DELETE /admin/report-layouts/:id               // 删除 (软删除)

// 卡片类型元数据
GET   /admin/report-layouts/card-types         // 获取所有可用卡片类型及配置 schema

// 预览报告 (用于测试配置)
POST  /admin/report-layouts/:id/preview        // 传入模拟数据，返回渲染后的报告

// 复制配置
POST  /admin/report-layouts/:id/clone
```

#### 3.2.2 前端报告 API (修改现有)

```typescript
// 现有 API 保持兼容，内部实现改为基于配置
GET   /reports/:record_id

// 新增: 获取报告布局配置 (前端动态渲染用)
GET   /reports/:record_id/layout               // 返回该报告使用的布局配置

// 新增: 获取特定卡片数据
GET   /reports/:record_id/cards/:card_id       // 返回特定卡片的详细数据
```

### 3.3 前端架构

#### 3.3.1 动态组件渲染架构

```typescript
// apps/xince-app/src/components/report/cards/
// 卡片组件注册表

interface CardComponentMap {
  hero: typeof HeroCard;
  radar: typeof RadarCard;
  bar_chart: typeof BarChartCard;
  persona_desc: typeof PersonaDescCard;
  calendar: typeof CalendarCard;
  hex_dim: typeof HexDimCard;
  future_letter: typeof FutureLetterCard;
  metaphor: typeof MetaphorCard;
  tags: typeof TagsCard;
  score_ring: typeof ScoreRingCard;
  action_guide: typeof ActionGuideCard;
  ai_analysis: typeof AiAnalysisCard;
  share_card: typeof ShareCard;
}

// 动态渲染组件
// ReportCardRenderer.vue
const props = defineProps<{
  cardType: string;
  cardConfig: CardConfig;
  cardData: any;
}>();

const component = computed(() => cardComponentRegistry[props.cardType]);
```

#### 3.3.2 报告页面重构

```vue
<!-- result.vue 新结构 -->
<template>
  <view class="report-page">
    <!-- 动态渲染配置的卡片 -->
    <ReportCardRenderer
      v-for="card in layoutConfig.cards"
      :key="card.card_id"
      :card-type="card.card_type"
      :card-config="card"
      :card-data="reportData.cardContents[card.card_id]"
      :base-data="reportData.base"
    />
  </view>
</template>
```

### 3.4 服务层重构

#### 3.4.1 新服务: ReportLayoutService

```python
# server/app/services/report_layout_service.py

class ReportLayoutService:
    """报告布局服务 - 处理布局配置的 CRUD 和验证"""

    async def get_layout_config(self, config_id: int) -> ReportLayoutConfig:
        ...

    async def validate_cards_config(self, cards_config: list[dict]) -> ValidationResult:
        """验证卡片配置是否合法"""
        ...

    async def preview_layout(
        self,
        layout_config: ReportLayoutConfig,
        mock_data: dict
    ) -> dict:
        """预览布局效果"""
        ...

    async def get_card_types_schema(self) -> list[CardTypeSchema]:
        """获取所有支持的卡片类型及配置 schema"""
        ...
```

#### 3.4.2 重构: AppReportService

```python
# server/app/services/app_report_service.py

class AppReportService:
    async def get_report_detail(self, record_id: int) -> dict:
        # 1. 获取 ReportSnapshot
        snapshot = await self._get_snapshot(record_id)

        # 2. 获取布局配置
        layout_config = await self._get_layout_config(snapshot)

        # 3. 基础数据准备
        base_data = await self._prepare_base_data(snapshot)

        # 4. 按卡片配置计算/获取数据
        cards_data = {}
        for card_config in layout_config.cards_config:
            cards_data[card_config.card_id] = await self._build_card_data(
                card_config, base_data, snapshot
            )

        # 5. 组装响应
        return {
            "report_id": snapshot.id,
            "record_id": record_id,
            "layout_config": self._serialize_layout_config(layout_config),
            "base_data": base_data,
            "card_contents": snapshot.card_contents,
            "cards_data": cards_data,
        }

    async def _build_card_data(
        self,
        card_config: CardConfig,
        base_data: dict,
        snapshot: ReportSnapshot
    ) -> dict:
        """根据卡片配置构建数据"""
        ds = card_config.data_source

        if ds.type == "dimension_scores":
            return self._build_dimension_scores_card(ds.config, base_data)

        elif ds.type == "computed":
            return self._build_computed_card(ds.config, base_data)

        elif ds.type == "ai_generated":
            # 从 snapshot.card_contents 中获取 AI 生成内容
            key = card_config.ai_config.placeholder_key
            return snapshot.card_contents.get(key, {})

        elif ds.type == "persona":
            return self._build_persona_card(ds.config, base_data)

        # ... 其他类型
```

#### 3.4.3 重构: ReportAiService

```python
# server/app/services/report_ai_service.py

class ReportAiService:
    async def _generate_ai_analysis(
        self,
        record_id: int,
        snapshot: ReportSnapshot
    ) -> dict:
        # 1. 获取布局配置
        layout_config = await self._get_layout_config(snapshot)

        # 2. 构建完整 prompt
        base_prompt = layout_config.ai_base_prompt
        base_context = await self._build_base_context(record_id, snapshot)

        # 3. 组装带卡片指令的 prompt
        card_sections = []
        for card in layout_config.cards_config:
            if card.ai_config:
                section = self._build_card_prompt_section(card)
                card_sections.append(section)

        full_prompt = f"""
{base_prompt}

测试数据:
{json.dumps(base_context, ensure_ascii=False, indent=2)}

请按以下格式生成报告各部分内容:
{chr(10).join(card_sections)}
"""

        # 4. 调用 AI
        result = await self.ai_gateway.generate(
            prompt=full_prompt,
            model_tier=layout_config.ai_model_tier,
            temperature=layout_config.ai_temperature,
            max_tokens=layout_config.ai_max_tokens,
        )

        # 5. 解析各卡片内容
        card_contents = self._parse_ai_response(result["content"], layout_config)

        return {
            "provider": result["provider"],
            "model_used": result["model_used"],
            "content": result["content"],
            "card_contents": card_contents,
        }

    def _parse_ai_response(
        self,
        content: str,
        layout_config: ReportLayoutConfig
    ) -> dict:
        """解析 AI 响应，提取各卡片内容"""
        card_contents = {}

        # 尝试按配置的 placeholder_key 提取
        for card in layout_config.cards_config:
            if not card.ai_config:
                continue

            key = card.ai_config.placeholder_key
            format_type = card.ai_config.output_format

            # 使用正则或结构化解析提取内容
            extracted = self._extract_section(content, key, format_type)
            card_contents[key] = extracted

        return card_contents
```

---

## 4. 迁移方案

### 4.1 数据库迁移

```python
# alembic migration

# 1. 创建 xc_report_layout_config 表
# 2. 修改 xc_test_version 表: 添加 report_layout_config_id，保留 report_template_code 用于回退
# 3. 修改 xc_report_snapshot 表: 添加 layout_config_id 和 card_contents
# 4. 创建默认布局配置，将现有 report_template_code 映射到对应的布局配置
```

### 4.2 代码迁移步骤

**阶段 1: 基础设施 (2-3 天)**
1. 创建 `ReportLayoutConfig` 模型
2. 创建 `ReportLayoutService`
3. 创建卡片组件基础架构
4. 添加管理后台布局配置 CRUD API

**阶段 2: 卡片实现 (3-4 天)**
1. 实现各卡片类型的数据计算逻辑
2. 实现前端卡片组件
3. 实现 AI Prompt 组装和解析

**阶段 3: 服务层重构 (2-3 天)**
1. 重构 `AppReportService` 支持基于配置的渲染
2. 重构 `ReportAiService` 支持多卡片 AI 生成
3. 保持向后兼容：当无布局配置时，使用原有硬编码逻辑

**阶段 4: 前端重构 (2-3 天)**
1. 重构 `result.vue` 使用动态卡片渲染
2. 实现管理后台布局配置界面
3. 添加实时预览功能

**阶段 5: 数据迁移 (1 天)**
1. 为现有测试创建默认布局配置
2. 迁移生产数据

### 4.3 向后兼容策略

```python
# AppReportService.get_report_detail()

async def get_report_detail(self, record_id: int) -> dict:
    snapshot = await self._get_snapshot(record_id)
    layout_config = await self._get_layout_config(snapshot)

    if layout_config:
        # 新逻辑：基于配置的渲染
        return await self._get_report_with_layout(snapshot, layout_config)
    else:
        # 兼容逻辑：使用原有硬编码方法
        return await self._get_report_legacy(snapshot)
```

---

## 5. 与当前系统的差距分析

| 能力 | 当前系统 | 目标系统 | 差距 |
|------|----------|----------|------|
| 报告结构 | 固定 11 个字段 | 可配置卡片列表 | 需新增布局配置模型和动态渲染 |
| 卡片类型 | 7 种固定类型 | 12+ 种可扩展类型 | 需抽象卡片接口，实现组件注册机制 |
| 计算逻辑 | 硬编码在 service | 配置化计算规则 | 需实现表达式引擎或规则引擎 |
| AI 生成 | 单段文本 | 多卡片结构化生成 | 需重构 Prompt 组装和响应解析 |
| 数据存储 | report_json 固定结构 | card_contents 动态结构 | 需修改模型，保持向后兼容 |
| 前端渲染 | 硬编码组件 | 动态组件渲染 | 需实现组件注册和动态加载 |
| 管理配置 | 仅支持 AI 模板选择 | 可视化卡片配置 | 需开发复杂配置界面 |

---

## 6. 估算与优先级

### 6.1 工作量估算

| 阶段 | 工作量 | 说明 |
|------|--------|------|
| 基础设施 | 2-3 天 | 模型、服务、基础 API |
| 卡片实现 | 4-5 天 | 12 种卡片类型 |
| 服务层重构 | 2-3 天 | 兼容现有逻辑 |
| 前端重构 | 3-4 天 | 动态渲染、配置界面 |
| 测试 & 修复 | 2-3 天 | 全面测试 |
| **总计** | **13-18 天** | 约 2.5-3.5 人周 |

### 6.2 优先级建议

**P1 - 核心功能 (必做)**
- 布局配置模型和 API
- Hero、Radar、PersonaDesc、AIAnalysis 卡片
- 基础管理后台配置界面
- 向后兼容机制

**P2 - 增强功能 (建议做)**
- BarChart、Calendar、HexDim 卡片
- 计算规则引擎
- 实时预览功能

**P3 - 高级功能 (可选)**
- FutureLetter、Metaphor 等创意卡片
- 卡片间联动配置
- A/B 测试支持

---

## 7. 示例配置

### 7.1 MBTI 测试报告配置示例

```yaml
config_code: mbti_default_v1
name: MBTI 默认报告布局
description: 经典的 MBTI 人格报告布局

ai_base_prompt: |
  你是 MBTI 人格测试报告生成专家。请基于用户的测试结果生成一份专业、温暖的报告。
  注意：
  1. 使用温和、非评判性的语言
  2. 避免使用医疗诊断术语
  3. 提供具体、可执行的建议

ai_model_tier: PRO
ai_temperature: 0.75
ai_max_tokens: 2500

cards_config:
  # 1. Hero 卡片 - 顶部展示
  - card_type: hero
    card_id: main_hero
    title: null  # 使用测试名称
    icon: "🎭"
    sort_order: 1
    data_source:
      type: persona
      config:
        fields: [name, emoji, description]
    render_config:
      theme: purple
      card_style: elevated

  # 2. 雷达图 - 四维度展示
  - card_type: radar
    card_id: dim_radar
    title: 维度分布
    icon: "🎯"
    sort_order: 2
    data_source:
      type: dimension_scores
      config:
        dims: [EI, SN, TF, JP]
        normalize: true
    render_config:
      component_config:
        show_labels: true
        fill_opacity: 0.3
        grid_lines: 4

  # 3. 人格描述卡片
  - card_type: persona_desc
    card_id: persona_detail
    title: 你的画像
    sort_order: 3
    data_source:
      type: person
      config:
        fields: [name, description, keywords, soul_signature]

  # 4. AI 深度分析
  - card_type: ai_analysis
    card_id: deep_analysis
    title: 深度解读
    sort_order: 4
    ai_config:
      prompt_addon: |
        ## 深度解读
        请从以下四个方面分析这个人格类型:
        1. 核心优势 (strength)
        2. 成长空间 (growth)
        3. 人际关系建议 (social)
        4. 日常行动指南 (action)

        每个方面 80-100 字，用温和、鼓励的语气。
      output_format: json
      placeholder_key: deep_analysis_sections
      fallback_content: |
        {"strength": "...", "growth": "...", "social": "...", "action": "..."}

  # 5. 六维图 (可选，如果分数足够)
  - card_type: hex_dim
    card_id: hex_chart
    title: 六维雷达
    sort_order: 5
    data_source:
      type: computed
      config:
        formula: |
          // 从维度分数计算六个子维度
          {
            "外向": max(0, EI),
            "内向": max(0, -EI),
            "实感": max(0, SN),
            "直觉": max(0, -SN),
            "思考": max(0, TF),
            "情感": max(0, -TF)
          }
    display_condition:
      type: score_threshold
      config:
        min_score: 30  # 总分超过 30 才显示

  # 6. 分享卡片
  - card_type: share_card
    card_id: share_preview
    title: 分享卡片
    sort_order: 100
    data_source:
      type: computed
      config:
        template: default
        include_fields: [persona_name, top_dimensions, summary]

  # 7. 行动指南
  - card_type: action_guide
    card_id: action_tips
    title: 行动指南
    sort_order: 6
    data_source:
      type: computed
      config:
        rules:
          - condition: "EI > 0.5"
            title: "发挥外向优势"
            description: "..."
          - condition: "EI < -0.5"
            title: "善用内向力量"
            description: "..."
```

---

## 8. 总结

### 关键价值

1. **灵活性**: 不同测试可配置完全不同的报告结构
2. **可扩展性**: 新增卡片类型无需修改现有代码
3. **运营能力**: 非技术人员可通过配置调整报告样式
4. **AI 精细化**: 每张卡片可独立配置 AI 生成策略
5. **数据驱动**: 支持 A/B 测试不同报告布局效果

### 实施建议

建议采用**渐进式迁移**策略：
1. 先实现基础设施和核心卡片类型
2. 在现有测试上试用新系统，保持向后兼容
3. 逐步将旧测试迁移到新配置系统
4. 最终实现完全配置化

这样可以降低风险，同时让新功能尽快投入使用。
