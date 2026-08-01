-- Identifies POS transactions that are actually the in-store pickup half of
-- an online order — same customer/sku/quantity/price within a 2-day window
-- of the online order. These get excluded from fct_sales so a pickup order
-- isn't counted twice (once online, once at pickup).
select distinct pos.txn_id
from {{ ref('stg_pos_transactions') }} pos
join {{ ref('stg_online_orders') }} online
    on pos.customer_email = online.customer_email
    and pos.sku = online.sku
    and pos.quantity = online.quantity
    and pos.unit_price = online.unit_price
    and online.fulfillment_type = 'pickup'
    and pos.txn_ts between online.order_ts and online.order_ts + interval '2 days'
