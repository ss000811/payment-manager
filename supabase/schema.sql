-- 支払い管理システム: Supabase テーブル定義
-- Supabase ダッシュボード > SQL Editor で実行してください

-- payments テーブル
CREATE TABLE IF NOT EXISTS public.payments (
    id             uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id        uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    year           integer NOT NULL,
    month          integer NOT NULL,
    payee          text NOT NULL,
    description    text NOT NULL DEFAULT '',
    payment_type   text NOT NULL DEFAULT 'fixed',
    payment_day    integer,
    adjusted_date  date,
    amount         numeric DEFAULT 0,
    payment_method text DEFAULT '',
    status         text DEFAULT 'unpaid',
    category       text DEFAULT '',
    notes          text DEFAULT '',
    created_at     timestamptz DEFAULT now(),
    updated_at     timestamptz DEFAULT now()
);

-- Row Level Security の有効化
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

-- ポリシー: 自分のデータのみ操作可能
CREATE POLICY "Users can manage their own payments"
    ON public.payments
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_payments_user_year_month
    ON public.payments(user_id, year, month);

CREATE INDEX IF NOT EXISTS idx_payments_status
    ON public.payments(status);

CREATE INDEX IF NOT EXISTS idx_payments_adjusted_date
    ON public.payments(adjusted_date);
