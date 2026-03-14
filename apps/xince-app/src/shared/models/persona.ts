export interface PersonaCardDimensionItem {
  dim_code: string;
  label: string;
  score: number;
}

export interface PersonaCardWeather {
  emoji: string;
  title: string;
  description: string;
}

export interface PersonaCardPayload {
  user_id: number;
  nickname: string;
  avatar_value: string;
  persona_title: string;
  soul_signature: string;
  keywords: string[];
  dimensions: PersonaCardDimensionItem[];
  weather: PersonaCardWeather;
}
