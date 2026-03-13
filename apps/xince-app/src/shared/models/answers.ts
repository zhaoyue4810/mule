export interface AnswerValue {
  option_code?: string | null;
  numeric_value?: number | null;
  ordered_option_codes?: string[] | null;
  point?: { x: number; y: number } | null;
}
