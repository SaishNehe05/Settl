"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-30 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. merchants
    op.create_table(
        'merchants',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('api_key_hash', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_merchants_email'), 'merchants', ['email'], unique=True)

    # 2. customers
    op.create_table(
        'customers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('external_customer_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('success_rate', sa.Float(), nullable=True),
        sa.Column('customer_value', sa.String(), nullable=True),
        sa.Column('opted_out', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_merchant_id'), 'customers', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=False)
    op.create_index(op.f('ix_customers_external_customer_id'), 'customers', ['external_customer_id'], unique=False)

    # 3. orders
    op.create_table(
        'orders',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('external_order_id', sa.String(), nullable=True),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_merchant_id'), 'orders', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_orders_customer_id'), 'orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_orders_external_order_id'), 'orders', ['external_order_id'], unique=False)

    # 4. payments
    op.create_table(
        'payments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=False),
        sa.Column('external_payment_id', sa.String(), nullable=True),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('method', sa.String(), nullable=True),
        sa.Column('failure_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_order_id'), 'payments', ['order_id'], unique=False)
    op.create_index(op.f('ix_payments_external_payment_id'), 'payments', ['external_payment_id'], unique=False)

    # 5. revenue_events
    op.create_table(
        'revenue_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('order_id', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('failure_reason', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revenue_events_merchant_id'), 'revenue_events', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_revenue_events_customer_id'), 'revenue_events', ['customer_id'], unique=False)
    op.create_index(op.f('ix_revenue_events_order_id'), 'revenue_events', ['order_id'], unique=False)
    op.create_index(op.f('ix_revenue_events_event_type'), 'revenue_events', ['event_type'], unique=False)

    # 6. recovery_cases
    op.create_table(
        'recovery_cases',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('revenue_event_id', sa.String(), nullable=False),
        sa.Column('amount_at_risk_paise', sa.BigInteger(), nullable=False),
        sa.Column('recovery_probability', sa.Float(), nullable=True),
        sa.Column('root_cause', sa.String(), nullable=True),
        sa.Column('priority', sa.String(), nullable=False),
        sa.Column('recommended_action', sa.String(), nullable=True),
        sa.Column('actual_action', sa.String(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('amount_recovered_paise', sa.BigInteger(), nullable=False),
        sa.Column('escalation_status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['revenue_event_id'], ['revenue_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('revenue_event_id')
    )
    op.create_index(op.f('ix_recovery_cases_merchant_id'), 'recovery_cases', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_recovery_cases_status'), 'recovery_cases', ['status'], unique=False)

    # 7. recovery_actions
    op.create_table(
        'recovery_actions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('razorpay_entity_id', sa.String(), nullable=True),
        sa.Column('reference_id', sa.String(), nullable=True),
        sa.Column('policy_result', sa.String(), nullable=True),
        sa.Column('policy_reason', sa.String(), nullable=True),
        sa.Column('request_payload', sa.JSON(), nullable=True),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference_id')
    )
    op.create_index(op.f('ix_recovery_actions_case_id'), 'recovery_actions', ['case_id'], unique=False)
    op.create_index(op.f('ix_recovery_actions_razorpay_entity_id'), 'recovery_actions', ['razorpay_entity_id'], unique=False)

    # 8. policies
    op.create_table(
        'policies',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('max_automated_amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('min_probability', sa.Float(), nullable=False),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False),
        sa.Column('human_review_above_paise', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('merchant_id')
    )
    op.create_index(op.f('ix_policies_merchant_id'), 'policies', ['merchant_id'], unique=True)

    # 9. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('actor', sa.String(), nullable=False),
        sa.Column('event_name', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_merchant_id'), 'audit_logs', ['merchant_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_case_id'), 'audit_logs', ['case_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)

    # 10. model_predictions
    op.create_table(
        'model_predictions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('root_cause_prediction', sa.String(), nullable=True),
        sa.Column('recommended_action', sa.String(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('features_hash', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_predictions_case_id'), 'model_predictions', ['case_id'], unique=False)

    # 11. notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('merchant_id', sa.String(), nullable=False),
        sa.Column('case_id', sa.String(), nullable=True),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('recipient', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_merchant_id'), 'notifications', ['merchant_id'], unique=False)

    # 12. webhook_events
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('external_event_id', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('signature_valid', sa.Boolean(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'external_event_id', name='uq_provider_external_event_id')
    )
    op.create_index(op.f('ix_webhook_events_provider'), 'webhook_events', ['provider'], unique=False)
    op.create_index(op.f('ix_webhook_events_external_event_id'), 'webhook_events', ['external_event_id'], unique=False)


def downgrade() -> None:
    op.drop_table('webhook_events')
    op.drop_table('notifications')
    op.drop_table('model_predictions')
    op.drop_table('audit_logs')
    op.drop_table('policies')
    op.drop_table('recovery_actions')
    op.drop_table('recovery_cases')
    op.drop_table('revenue_events')
    op.drop_table('payments')
    op.drop_table('orders')
    op.drop_table('customers')
    op.drop_table('merchants')
