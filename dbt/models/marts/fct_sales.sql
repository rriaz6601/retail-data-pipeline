-- One row per real sale, regardless of which source system recorded it.
-- Online orders are always included. POS transactions are included unless
-- they were already counted as the pickup half of an online order (see
-- int_pos_matched) — this mirrors the real production fix for a
-- double-counted-order bug.
with matched_pos_txn_ids as (
    select txn_id from {{ ref('int_pos_matched') }}
),

online_sales as (
    select
        order_id as sale_id,
        customer_email,
        sku,
        quantity,
        unit_price,
        quantity * unit_price as sale_amount,
        order_ts as sale_ts,
        'online' as source_channel
    from {{ ref('stg_online_orders') }}
),

pos_sales as (
    select
        pos.txn_id as sale_id,
        pos.customer_email,
        pos.sku,
        pos.quantity,
        pos.unit_price,
        pos.quantity * pos.unit_price as sale_amount,
        pos.txn_ts as sale_ts,
        'pos' as source_channel
    from {{ ref('stg_pos_transactions') }} pos
    left join matched_pos_txn_ids matched on pos.txn_id = matched.txn_id
    where matched.txn_id is null
)

select * from online_sales
union all
select * from pos_sales
