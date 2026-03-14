export interface TimeCapsuleItem {
  id: number;
  message: string;
  persona_title?: string | null;
  persona_icon?: string | null;
  test_id?: number | null;
  report_id?: number | null;
  created_at: string;
  unlock_date: string;
  duration_days: number;
  is_read: boolean;
  is_unlocked: boolean;
  days_remaining: number;
}

export interface TimeCapsuleCheckPayload {
  has_revealable: boolean;
  items: TimeCapsuleItem[];
}
