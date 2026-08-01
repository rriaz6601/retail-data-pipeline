select
    txn_id,
    lower(cust_email) as customer_email,
    txn_datetime::timestamp as txn_ts,
    product_code as sku,
    qty::int as quantity,
    price_each::numeric as unit_price,
    store_id
from {{ source('raw', 'pos_transactions') }}
