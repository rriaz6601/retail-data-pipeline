-- Identifies POS transactions that are actually the in-store pickup half of
-- an online order — same customer/sku/quantity/price within a 2-day window
-- of the online order. Ranked per online order AND per POS transaction so
-- each side pairs with at most one match (rn = 1 on both), preventing an
-- unrelated coincidental sale (same customer/sku/qty/price, different
-- reason) from being excluded alongside a genuine pickup match.
with candidates as (
    select
        online.order_id,
        pos.txn_id,
        row_number() over (partition by online.order_id order by pos.txn_ts) as rn_per_order,
        row_number() over (partition by pos.txn_id order by online.order_ts) as rn_per_txn
    from {{ ref('stg_pos_transactions') }} pos
    join {{ ref('stg_online_orders') }} online
        on pos.customer_email = online.customer_email
        and pos.sku = online.sku
        and pos.quantity = online.quantity
        and pos.unit_price = online.unit_price
        and online.fulfillment_type = 'pickup'
        and pos.txn_ts between online.order_ts and online.order_ts + interval '2 days'
)

select txn_id
from candidates
where rn_per_order = 1
  and rn_per_txn = 1
