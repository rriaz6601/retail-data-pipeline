select
    order_id,
    lower(customer_email) as customer_email,
    order_timestamp::timestamp as order_ts,
    item_sku as sku,
    quantity::int as quantity,
    unit_price::numeric as unit_price,
    fulfillment_type
from {{ source('raw', 'online_orders') }}
