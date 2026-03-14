export interface SharePosterTemplate {
  id: string;
  name: string;
  backgroundStart: string;
  backgroundEnd: string;
  panel: string;
  accent: string;
  secondary: string;
  qrFrame: string;
}

export const sharePosterTemplates: SharePosterTemplate[] = [
  {
    id: "sunset",
    name: "晚霞",
    backgroundStart: "#ffd8c0",
    backgroundEnd: "#ffb684",
    panel: "#fff4ea",
    accent: "#c85c2d",
    secondary: "#6e5142",
    qrFrame: "#fff8f2",
  },
  {
    id: "aurora",
    name: "极光",
    backgroundStart: "#d6f6e5",
    backgroundEnd: "#9ed9c0",
    panel: "#f4fff9",
    accent: "#2f8b61",
    secondary: "#486256",
    qrFrame: "#f8fffb",
  },
  {
    id: "nightfall",
    name: "夜航",
    backgroundStart: "#dfe6ff",
    backgroundEnd: "#b9c5ff",
    panel: "#f5f7ff",
    accent: "#5867c7",
    secondary: "#4f567a",
    qrFrame: "#f8f9ff",
  },
];

export function resolveSharePosterTemplate(templateId?: string) {
  return (
    sharePosterTemplates.find((item) => item.id === templateId) ||
    sharePosterTemplates[0]
  );
}
