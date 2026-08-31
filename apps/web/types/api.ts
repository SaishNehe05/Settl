export interface Customer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  success_rate: number;
  customer_value: string;
  opted_out: boolean;
}

export interface RecoveryAction {
  id: string;
  action_type: string;
  status: string;
  razorpay_entity_id?: string;
  reference_id?: string;
  policy_result?: string;
  policy_reason?: string;
  executed_at: string;
  response_payload?: Record<string, any>;
}

export interface AuditLog {
  id: string;
  actor: string;
  event_name: string;
  reason?: string;
  log_metadata?: Record<string, any>;
  created_at: string;
}

export interface RecoveryCaseItem {
  id: string;
  merchant_id: string;
  revenue_event_id: string;
  amount_at_risk_paise: number;
  recovery_probability: number;
  root_cause?: string;
  priority: string;
  recommended_action?: string;
  actual_action?: string;
  attempt_count: number;
  status: string;
  amount_recovered_paise: number;
  escalation_status?: string;
  customer_name?: string;
  customer_email?: string;
  created_at: string;
  updated_at: string;
}

export interface ModelPrediction {
  id: string;
  case_id: string;
  model_name: string;
  model_version: string;
  probability: number;
  root_cause_prediction?: string;
  recommended_action?: string;
  reason?: string;
  features_hash?: string;
  validation_status?: string;
  created_at: string;
}

export interface RecoveryCaseDetail extends RecoveryCaseItem {
  resolved_at?: string;
  customer?: Customer;
  event_type?: string;
  failure_reason?: string;
  actions: RecoveryAction[];
  audit_logs: AuditLog[];
  latest_prediction?: ModelPrediction;
}

export interface DashboardSummary {
  revenue_at_risk_paise: number;
  eligible_revenue_paise: number;
  revenue_recovered_paise: number;
  recovery_attempts_count: number;
  recovery_rate: number;
  guardrail_blocks_count: number;
  human_escalations_count: number;
  total_cases_count: number;
  active_cases_count: number;
  recovered_cases_count: number;
  recent_cases: RecoveryCaseItem[];
}

export interface Policy {
  id: string;
  merchant_id: string;
  max_attempts: number;
  max_automated_amount_paise: number;
  min_probability: number;
  cooldown_minutes: number;
  human_review_above_paise: number;
  created_at: string;
  updated_at: string;
}

export interface StrategyMetrics {
  attempts_count: number;
  successful_recoveries: number;
  wasted_attempts_fp: number;
  correct_stops_tn: number;
  missed_opportunities_fn: number;
  precision: number;
  recall: number;
  f1_score: number;
  accuracy: number;
  recovery_rate: number;
  gross_recovered_inr: number;
  outreach_cost_inr: number;
  net_recovered_inr: number;
  guardrail_blocks?: number;
  human_escalations?: number;
}

export interface EvaluationSummary {
  dataset_type: string;
  total_events: number;
  total_revenue_at_risk_inr: number;
  strategies: {
    settl_ai_agent: StrategyMetrics;
    naive_rule_based: StrategyMetrics;
    no_action: StrategyMetrics;
  };
  lift: {
    net_revenue_lift_inr: number;
    net_revenue_lift_pct: number;
    precision_improvement_pts: number;
    wasted_outreach_reduced_count: number;
    spam_reduction_rate: number;
  };
  confusion_matrix: {
    settl: { tp: number; fp: number; tn: number; fn: number };
    naive: { tp: number; fp: number; tn: number; fn: number };
  };
  category_breakdown: Record<string, {
    total: number;
    truly_recoverable: number;
    settl_recovered: number;
    naive_recovered: number;
  }>;
}
