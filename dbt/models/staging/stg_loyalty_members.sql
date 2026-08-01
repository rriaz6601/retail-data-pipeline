select
    member_id,
    lower(email) as email,
    full_name,
    signup_date::date as signup_date,
    loyalty_tier
from {{ source('raw', 'loyalty_members') }}
